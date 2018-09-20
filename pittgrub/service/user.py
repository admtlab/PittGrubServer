from typing import List, Optional, Union

from db import (
    EmailList,
    User,
    UserFoodPreference,
    UserLocation,
    UserStatus,
    UserVerification,
    session_scope
)
from domain.data import UserData, UserProfileData, FoodPreferenceData
from emailer import send_verification_email
from service.property import get_property, set_property
from . import MissingUserError


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
        verification = UserVerification.get_by_user(session, id)
        if verification is None:
            verification = UserVerification.add(session, user_id=id)
        return verification.code

def get_user_verification_code(id: int) -> Optional[str]:
    with session_scope() as session:
        if not _is_user(session, id):
            raise MissingUserError(f"User not found with id: {id}")
        verification = UserVerification.get_by_user(session, id)
        if verification is None:
            return None
        return verification.code

def get_user(id: int) -> Optional[UserData]:
    with session_scope() as session:
        user = User.get_by_id(session, id)
        return None if not user else UserData(user)

def get_user_profile(id: int) -> Optional[UserProfileData]:
    with session_scope() as session:
        user = User.get_by_id(session, id)
        return None if not user else UserProfileData(user)

def get_user_by_email(email: str) -> Optional[UserData]:
    with session_scope() as session:
        user = User.get_by_email(session, email)
        return None if not user else UserData(user)

def get_all_users() -> List[UserData]:
    with session_scope() as session:
        users = User.get_all(session)
        return UserData.list(users)

def get_user_food_preferences(id: int) -> List[FoodPreferenceData]:
    with session_scope() as session:
        food_preferences = User.get_by_id(session, id).food_preferences
        return FoodPreferenceData.list(food_preferences)

def change_user_password(id: int, old_password: str, new_password: str) -> bool:
    """
    Changes user password from old to new
    :param id:
    :param old_password:
    :param new_password:
    :return: True if succeeded
        False if not (invalid old_password, etc.)
    """
    with session_scope() as session:
        user = User.get_by_id(session, id)
        if user is None:
            raise MissingUserError(f"User not found with id: {id}")
        else:
            if not user.verify_password(old_password):
                return False
            user.password = new_password
    return True

def update_user_password(id: int, password: str) -> bool:
    with session_scope() as session:
        user = User.get_by_id(session, id)
        if user is None:
            raise MissingUserError(f"User not found with id: {id}")
        user.password = password
    return True


def update_user_profile(id: int, food: List[int] = None, pantry: bool=None, eager: int=None):
    with session_scope() as session:
        user = User.get_by_id(session, id)
        if food:
            UserFoodPreference.update(session, id, food)
        if pantry:
            user.pitt_pantry = pantry
        if eager:
            user.eagerness = eager
        session.merge(user)

def update_expo_token(id: int, token: str) -> bool:
    with session_scope() as session:
        user = User.get_by_id(session, id)
        user.expo_token = token
    return True

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

def add_location(id: int, latitude: float, longitude: float, time: 'datetime'=None):
    with session_scope() as session:
        session.add(UserLocation(user=id, lat=latitude, long=longitude, time=time))

def add_to_email_list(email: str) -> bool:
    assert email is not None
    with session_scope() as session:
        if not EmailList.find_by_email(session, email):
            session.add(EmailList(email=email))
        return True
    return False

def remove_from_email_list(email: str) -> bool:
    assert email is not None
    with session_scope() as session:
        if EmailList.find_by_email(session, email):
            EmailList.remove(session, email)
        return True
    return False

def invite_next_users():
    threshold = int(get_property('user.threshold'))
    with session_scope() as session:
        users = UserData.list(User.next_users_to_permit(session))
        for user in users:
            if threshold < 1:
                break
            code = UserVerification.add(session, user.id).code
            send_verification_email(to=user.email, code=code)
            threshold -= 1
    set_property('user.threshold', str(threshold))
