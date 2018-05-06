import datetime
from typing import List

from . import MissingUserError
from domain.data import UserReferralData, UserHostRequestData
from db import User, UserHostRequest, UserReferral, UserRole, session_scope

class AdminPermissionError(Exception):
    pass

def _is_admin(session, id: int) -> bool:
    user = User.get_by_id(session, id)
    if user is None:
        raise MissingUserError(f"User not found with id: {id}")
    return user.is_admin

def is_admin(id: int) -> bool:
    with session_scope() as session:
        return _is_admin(session, id)

def get_pending_host_requests():
    with session_scope() as session:
        host_requests = UserHostRequest.get_all_pending(session)
        return UserHostRequestData.list(host_requests)

def get_referrals(reference: int) -> List[UserReferralData]:
    with session_scope() as session:
        refs = UserReferral.get_all_by_reference(session, reference)
        return UserReferralData.list(refs)

def host_approval(user_id: int, admin_id: int) -> bool:
    with session_scope() as session:
        if not _is_admin(session, admin_id):
            raise AdminPermissionError(f"User {admin_id} does not have admin permission")
        user_host_req = UserHostRequest.get_by_user_id(session, user_id)
        if user_host_req is None or user_host_req.approved is not None:
            return False
        user_host_req.approved = datetime.datetime.utcnow()
        user_host_req.approved_by = admin_id
        session.merge(user_host_req)
    return True
