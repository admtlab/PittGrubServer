from db import Activity, UserActivity, session_scope


def log_activity(user_id: int, activity: Activity):
    with session_scope() as session:
        session.add(UserActivity(user_id, activity))
