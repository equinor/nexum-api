import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from src.models.base import Base

if TYPE_CHECKING:
    from src.models.strategy import Strategy
    from src.models.option import Option


class StrategyOption(Base):
    __tablename__ = "strategy_option"

    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy.id"), primary_key=True, index=True)
    option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("option.id"), primary_key=True, index=True)

    strategy: Mapped["Strategy"] = relationship(
        "Strategy",
        back_populates="strategy_options"
    )

    option: Mapped["Option"] = relationship(
        "Option",
        back_populates="strategy_options"
    )

    def __init__(
        self,
        strategy_id: uuid.UUID,
        option_id: uuid.UUID,
    ):
        self.strategy_id = strategy_id
        self.option_id = option_id

    def __repr__(self):
        return f"strategy_id={self.strategy_id}, option_id={self.option_id}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StrategyOption):
            return False
        return (
            self.strategy_id == other.strategy_id and
            self.option_id == other.option_id
        )
    
    def __hash__(self) -> int:
        return hash(uuid.uuid4())
