import logging
from datetime import datetime
from typing import List, Optional

from db import (
    Event,
    EventFoodPreference,
    EventImage,
    User,
    UserAcceptedEvent,
    UserRecommendedEvent,
    session_scope
)
from domain.data import (
    EventData,
    EventImageData
)


def create_event(
        title: str,
        start_date: 'datetime',
        end_date: 'datetime',
        details: str,
        servings: int,
        address: str,
        location: str) -> EventData:
    with session_scope() as session:
        event = Event(
            title=title,
            start_date=start_date,
            end_date=end_date,
            details=details,
            servings=servings,
            address=address,
            location=location)
        if event is None:
            return None
        session.add(event)
        session.commit(event)
        session.refresh(event)
        return EventData(event)


def get_event(id: int) -> Optional[EventData]:
    with session_scope() as session:
        event = Event.get_by_id(session, id)
        return EventData(event)


def get_events() -> List[EventData]:
    with session_scope() as session:
        events = Event.get_all(session)
        return EventData.list(events)


def get_newest() -> List[EventData]:
    with session_scope() as session:
        events = Event.get_all_newest(session)
        return [EventData(e) for e in events]


def user_accept_event(event: int, user: int):
    with session_scope() as session:
        accepted = UserAcceptedEvent(event, user)
        session.add(accepted)


def user_accepted_events(user_id: int):
    with session_scope() as session:
        user = User.get_by_id(session, user_id)
        accepted = user.accepted_events
        return EventData.list(accepted)


def user_recommended_events(user_id: int):
    with session_scope() as session:
        user = User.get_by_id(session, user_id)
        recommended = user.recommended_events
        return EventData.list(recommended)


def user_recommended_events_valid(user_id: int):
    with session_scope() as session:
        user = User.get_by_id(session, user_id)
        recommended = user.recommended_events
        accepted = set([a.id for a in user.accepted_events])
        return EventData.list(
            [e for e in recommended
            if e.end_date > datetime.now()
            and e.id not in accepted])


def set_food_preferences(id: int, prefs: List[int]):
    with session_scope() as session:
        EventFoodPreference.add(session, id, prefs)


def get_event_image_by_event(id: int) -> Optional[EventImageData]:
    with session_scope() as session:
        event_image = EventImage.get_by_event(session, id)
        return EventImageData(event_image)


def add_event_image(id: int) -> Optional[EventImageData]:
    with session_scope() as session:
        event_image = EventImage(event_id=id)
        if event_image is None:
            return None
        session.add(event_image)
        session.commit(event_image)
        session.refresh(event_image)
        return EventImageData(event_image)
