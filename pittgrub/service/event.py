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
    EventImageData,
    EventViewData
)


def create_event(
        title: str,
        organizer: int,
        start_date: 'datetime',
        end_date: 'datetime',
        details: str,
        servings: int,
        address: str,
        location: str,
        latitude,
        longitude) -> EventData:
    with session_scope() as session:
        event = Event(
            title=title,
            organizer=organizer,
            start_date=start_date,
            end_date=end_date,
            details=details,
            servings=servings,
            address=address,
            location=location,
            latitude=latitude,
            longitude=longitude)
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

def get_event_by_user(id: int, user_id: int) -> Optional[EventViewData]:
    with session_scope() as session:
        event = Event.get_by_user(session, id, user_id)
        return EventViewData(event)


def get_events() -> List[EventData]:
    with session_scope() as session:
        events = Event.get_all(session)
        return EventData.list(events)


def get_active() -> List[EventData]:
    with session_scope() as session:
        events = Event.get_all_active(session)
        return [EventData(e) for e in events]


def get_active_by_user(user_id: int) -> List[EventViewData]:
    with session_scope() as session:
        events = Event.get_all_active_by_user(session, user_id)
        return EventViewData.list(events)


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
