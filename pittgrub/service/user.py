from typing import List

from . import MissingUserError
from db import (
    FoodPreference,
    User,
    UserFoodPreference,
    UserStatus,
    UserVerification,
    session_scope
)


def _is_user(session, id: int) -> bool:
    user = User.get_by_id(session, id)
    return user is not None

def is_user(id: int) -> bool:
    with session_scope() as session:
        return _is_user(session, id)

def get_user_verification(id: int) -> str:
    with session_scope() as session:
        if not _is_user(session, id):
            raise MissingUserError(f"User not found with id: {id}")
        verification = UserVerification.get_by_user(id)
        if verification is None:
            verification = UserVerification.add(user_id=id)
        return verification.code

def get_user(id: int) -> 'User':
    with session_scope() as session:
        user = User.get_by_id(session, id)
        if user is None:
            raise MissingUserError(f"User not found with id: {id}")
        session.expunge(user)
    return user

def get_user_food_preferences(id: int):
    with session_scope() as session:
        food_preferences = User.get_by_id(session, id).food_preferences
        session.expunge_all()
    return food_preferences

def update_user_food_preferences(id: int, food_preferences: List[int]=None):
    with session_scope() as session:
        UserFoodPreference.update(session, id, food_preferences)

def verify_user(code: str, user_id: int) -> bool:
    assert code is not None
    with session_scope() as session:
        verification = UserVerification.get_by_code(session, code)
        if verification is not None and verification.user_id == user_id:
            user = verification.user
            user.active = True
            user.status = UserStatus.ACCEPTED
            UserVerification.delete(session, code)
            return True
    return False
