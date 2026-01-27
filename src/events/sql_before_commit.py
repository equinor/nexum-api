from sqlalchemy import event
from sqlalchemy.orm import Session
from src.constants import SessionInfoParameters
from src.events.discrete_table_event_handler import DiscreteTableEventHandler


@event.listens_for(Session, "before_commit")
def before_commit_event_handler(session: Session) -> None:
    if SessionInfoParameters.IS_EVENT_DISABLED.value in session.info:
        if session.info[SessionInfoParameters.IS_EVENT_DISABLED.value]:
            return
    DiscreteTableEventHandler.recalculate_affected_probabilities(session)
    DiscreteTableEventHandler.recalculate_affected_utilities(session)
    DiscreteTableEventHandler.remove_options_from_strategy_table(session)
