"""
Representations of database entities
Author: Mark Silvis
"""

from abc import ABC
from typing import Any, Dict, List, Type, TypeVar

from db.schema import Base

D = TypeVar('Data', bound='Data')


class Data(ABC):

    @classmethod
    def list(cls: Type[D], data: List[Base]) -> List[D]:
        return [cls(i) for i in data]

    def json(self) -> Dict[str, Any]:
        return self.__dict__


class EventData(Data):

    def __init__(self, event: 'Event'):
        self.id = event.id
        self.organizer = event.organizer_id
        self.organization = event.organization
        self.title = event.title
        self.start_date = event.start_date.isoformat()
        self.end_date = event.end_date.isoformat()
        self.details = event.details
        self.servings = event.servings
        self.address = event.address
        self.location = event.location
        self.food_preferences = [FoodPreferenceData(f) for f in event.food_preferences]

    def json(self) -> Dict[str, Any]:
        data = self.__dict__
        data['food_preferences'] = [{'id': f.id, 'name': f.name} for f in self.food_preferences]
        return data


class EventImageData(Data):

    def __init__(self, event_image: 'EventImage'):
        self.id = event_image.id
        self.event_id = event_image.event_id


class EventViewData(Data):

    def __init__(self, event: 'Event', accepted: bool, recommended: bool):
        self.id = event.id
        self.organizer = event.organizer_id
        self.organization = event.organization
        self.title = event.title
        self.start_date = event.start_date.isoformat()
        self.end_date = event.end_date.isoformat()
        self.details = event.details
        self.servings = event.servings
        self.address = event.address
        self.location = event.location
        self.latitude = float(event.latitude) if event.latitude is not None else None
        self.longitude = float(event.longitude) if event.longitude is not None else None
        self.food_preferences = [FoodPreferenceData(f) for f in event.food_preferences]
        self.accepted = bool(accepted) 
        self.recommended = bool(recommended)

    def json(self) -> Dict[str, Any]:
        data = self.__dict__
        data['food_preferences'] = [{'id': f.id, 'name': f.name} for f in self.food_preferences]
        return data


class FoodPreferenceData(Data):

    def __init__(self, fp: 'FoodPreference'):
        self.id = fp.id
        self.name = fp.name
        self.description = fp.description


class UserData(Data):

    def __init__(self, user: 'User'):
        self.id = user.id
        self.email = user.email
        self.name = user.name
        self.status = user.status.name
        self.roles = [UserRoleData(role) for role in user.roles]
        self.active = user.active
        self.disabled = user.disabled

    def json(self) -> Dict[str, Any]:
        data = self.__dict__
        data['roles'] = [{'id': r.id, 'name': r.name} for r in self.roles]
        return data


class UserProfileData(Data):

    def __init__(self, user: 'User'):
        self.id = user.id
        self.pitt_pantry = user.pitt_pantry
        self.eagerness = user.eagerness
        self.food_preferences = [FoodPreferenceData(f) for f in user.food_preferences]

    def json(self) -> Dict[str, Any]:
        data = self.__dict__
        data['food_preferences'] = [{'id': f.id, 'name': f.name} for f in self.food_preferences]
        return data


class UserRoleData(Data):

    def __init__(self, role: 'UserRole'):
        self.id = role.id
        self.name = role.name
        self.description = role.description


class UserHostRequestData(Data):

    def __init__(self, req: 'UserHostRequest'):
        self.id = req.id
        self.organization = req.organization
        self.directory = req.directory
        self.reason = req.reason
        self.created = req.created.isoformat()
        self.approved = req.approved
        self.approved_by = req.approved_by
        self.user = {'id': req.user_id, 'email': req.user.email, 'name': req.user.name}


class UserReferralData(Data):

    def __init__(self, ref: 'UserReferral'):
        self.user = ref.requester
