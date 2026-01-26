import uuid

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    affected_uncertainties: set[uuid.UUID] = Field(default_factory=set)  # type: ignore
    affected_utilities: set[uuid.UUID] = Field(default_factory=set)  # type: ignore
    issues_from_which_to_remove_stratigy_options: set[uuid.UUID] = Field(default_factory=set)  # type: ignore
    is_event_disabled: bool = False


class SessionInfoHandler:
    @staticmethod
    def get_session_info(session: Session) -> SessionInfo:
        return SessionInfo(**session.info)

    @staticmethod
    def update_session_info(session: Session, session_info: SessionInfo):
        session.info.update(session_info)

    @staticmethod
    def add_to_session_info(
        current: SessionInfo, additional_session_data: SessionInfo
    ) -> SessionInfo:
        if additional_session_data.affected_uncertainties:
            current.affected_uncertainties.update(additional_session_data.affected_uncertainties)

        if additional_session_data.affected_utilities:
            current.affected_utilities.update(additional_session_data.affected_utilities)

        return current
