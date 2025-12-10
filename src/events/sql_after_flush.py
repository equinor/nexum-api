from typing import Any
from sqlalchemy import event
from sqlalchemy.orm import Session
from events.discrete_table_event_handler import DiscreteTableEventHandler

@event.listens_for(Session, 'after_flush')
def after_flush_event_handler(session: Session, flush_context: Any) -> None:
    DiscreteTableEventHandler().process_session_changes_after_flush(session)