def disabled_session_handler(session: Session) -> bool:  # noqa: F821
    if "session_info" in session.info:
        session_info = session.info["session_info"]
        if session_info.is_event_disabled:
            return
