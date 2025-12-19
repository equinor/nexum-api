from sqlalchemy import event
from sqlalchemy.orm import Session
from src.events.discrete_table_event_handler import DiscreteTableEventHandler

@event.listens_for(Session, 'before_commit')
def before_commit_event_handler(session: Session) -> None:
    DiscreteTableEventHandler().recalculate_affected_probabilities(session)
    DiscreteTableEventHandler().recalculate_affected_utilities(session)