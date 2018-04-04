from db import User, UserHostRequest, UserRole, session_scope


def is_admin(user_id: int) -> bool:
    with session_scope() as session:
        user = User.get_by_id(session, user_id)
        assert user is not None
        return 'Admin' in [r.name for r in user.roles]


def get_pending_host_requests():
    with session_scope() as session:
        host_requests = UserHostRequest.get_all_pending(session)
        session.expunge_all()
        return host_requests


def host_approval(user_id: int, admin_id: int) -> bool:
    with session_scope() as session:
        return UserHostRequest.approve_host(session, user_id, admin_id)
