from sqlalchemy.sql import select
from enum import Enum
from src.models import ValueMetric
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import config

from src.auth.db_auth import DatabaseAuthenticator
import urllib.parse
from typing import Optional, Any
from src.constants import default_value_metric_id


class DatabaseConnectionStrings(Enum):
    @classmethod
    def get_connection_string(cls, app_env: str) -> str:
        """Retrieve the appropriate connection string based on the application environment."""
        if app_env == "local":
            return config.DATABASE_CONN_LOCAL
        elif app_env == "dev":
            return config.DATABASE_CONN_DEV
        elif app_env == "test":
            return config.DATABASE_CONN_TEST
        elif app_env == "prod":
            return config.DATABASE_CONN_PROD
        else:
            raise ValueError(f"Unknown environment: {app_env}")


async def ensure_default_value_metric_exists(session: AsyncSession):
    value_metrics = list((await session.scalars(select(ValueMetric))).all())

    for value_metric in value_metrics:
        if value_metric.name == "":
            await session.delete(value_metric)

    if default_value_metric_id in [x.id for x in value_metrics]:
        await session.commit()
        return

    # create default value metric
    default_metric = ValueMetric(id=default_value_metric_id, name="value")
    session.add(default_metric)
    await session.commit()


async def get_connection_string_and_token(
    env: str,
) -> tuple[str, Optional[dict[Any, Any]]]:
    db_connection_string = DatabaseConnectionStrings.get_connection_string(env)
    database_authenticator = DatabaseAuthenticator()
    if env != "local":
        token_dict = await database_authenticator.authenticate_db_connection_string()
    else:
        token_dict = None
    await database_authenticator.close()
    return db_connection_string, token_dict


def build_connection_url(db_connection_string: str, driver: str) -> str:
    params = urllib.parse.quote_plus(db_connection_string.replace('"', ""))
    return f"mssql+{driver}:///?odbc_connect={params}"
