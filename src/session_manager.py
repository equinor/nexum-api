import asyncio
from typing import AsyncGenerator, Optional, Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from src.models.base import Base
from src.config import config
from src.seed_database import (
    seed_database,
    create_decision_tree_symmetry_DT_from_ID,
    create_decision_tree_symmetry_DT,
)
from src.database import (
    DatabaseConnectionStrings,
    get_connection_string_and_token,
    build_connection_url,
    ensure_default_value_metric_exists,
)
from src.logger import get_dot_api_logger

# import events to activate them
from src.events import (  # noqa: F401
    before_flush_event_handler,
    after_flush_event_handler,
    before_commit_event_handler,
    after_commit_event_handler,
)


class SessionManager:
    """Manages asynchronous DB sessions with connection pooling."""

    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._token_refresh_task: Optional[asyncio.Task[Any]] = None
        self._shutdown_event = asyncio.Event()
        self._logger = get_dot_api_logger()

    async def _initialize_in_memory_db(self, db_connection_string: str) -> None:
        """Initialize an in-memory database, and populate with test data."""
        self.engine = create_async_engine(
            db_connection_string,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=config.POOL_SIZE,
            max_overflow=config.MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=config.POOL_RECYCLE,
            echo=config.DEBUG,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await seed_database(conn, num_projects=10, num_nodes=50)
            await create_decision_tree_symmetry_DT_from_ID(conn)
            await create_decision_tree_symmetry_DT(conn)

    async def _initialize_persistent_db(self) -> None:
        """Initialize a persistent database."""
        (
            db_connection_string,
            token_dict,
        ) = await get_connection_string_and_token(config.APP_ENV)
        database_url = build_connection_url(db_connection_string, driver="aioodbc")

        if config.APP_ENV == "local":
            self.engine = create_async_engine(
                database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=config.POOL_SIZE,
                pool_timeout=None,
                max_overflow=config.MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=config.POOL_RECYCLE,
                echo=config.DEBUG,
            )
        else:
            self.engine = create_async_engine(
                database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=config.POOL_SIZE,
                pool_timeout=None,
                max_overflow=config.MAX_OVERFLOW,
                connect_args={"attrs_before": token_dict},
                pool_pre_ping=True,
                pool_recycle=config.POOL_RECYCLE,
                echo=config.DEBUG,
            )

    def _initialize_session_factory(self) -> None:
        """Initialize the session factory."""
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )

    async def init_db(self) -> None:
        """Initialize the database engine and session factory."""
        db_connection_string = DatabaseConnectionStrings.get_connection_string(config.APP_ENV)

        if ":memory:" in db_connection_string:
            await self._initialize_in_memory_db(db_connection_string)
        else:
            await self._initialize_persistent_db()

        self._initialize_session_factory()

        try:
            await self.run_start_task()
        except Exception:
            # implyes that a different thread is performing the start task
            pass

        if config.APP_ENV != "local" and ":memory:" not in db_connection_string:
            self._token_refresh_task = asyncio.create_task(self._token_refresh_loop())

    async def dispose_engine(self) -> None:
        if self.engine:
            await self.engine.dispose()

    async def close(self) -> None:
        """Dispose of the database engine."""
        self._shutdown_event.set()
        if self._token_refresh_task:
            self._token_refresh_task.cancel()
            try:
                await self._token_refresh_task
            except asyncio.CancelledError:
                # Task cancellation is expected during shutdown; no action needed.
                pass
            except Exception as e:
                self._logger.warning(f"Error while cancelling token refresh task: {e}")

        await self.dispose_engine()

    async def _refresh_database_engine(self) -> None:
        """Refresh database engine with new token."""
        await self.dispose_engine()

        # Recreate engine with fresh token
        await self._initialize_persistent_db()
        self._initialize_session_factory()

    async def _token_refresh_loop(self) -> None:
        """Background task to refresh database tokens periodically."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=config.DB_TOKEN_DURATION
                )
            except asyncio.TimeoutError:
                try:
                    print("Refreshing database engine")
                    await self._refresh_database_engine()
                except Exception as e:
                    # Log error but continue the loop
                    self._logger.warning(f"Refreshing database engine failed: {e}")

    async def run_start_task(self) -> None:
        """Run the database start task."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized.")

        async for session in self.get_session():
            try:
                await ensure_default_value_metric_exists(session)
            except Exception as e:
                print(e)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session with the correct schema set."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized.")

        async with self.session_factory() as session:
            try:
                yield session
                if session.deleted or session.new or session.dirty:
                    await session.commit()
            except Exception as e:
                await session.rollback()
                raise e


# Global instances
sessionmanager = SessionManager()
