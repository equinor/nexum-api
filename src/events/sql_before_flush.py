from typing import Any
from sqlalchemy import event
from sqlalchemy.orm import Session
from src.constants import SessionInfoParameters
from src.events.discrete_table_event_handler import DiscreteTableEventHandler


@event.listens_for(Session, "before_flush")
def before_flush_event_handler(session: Session, flush_context: Any, instances: Any) -> None:
    if SessionInfoParameters.IS_EVENT_DISABLED.value in session.info:
        if session.info[SessionInfoParameters.IS_EVENT_DISABLED.value]:
            return
    DiscreteTableEventHandler().process_session_changes_before_flush(session)
