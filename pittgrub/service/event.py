from typing import List, Optional

from db import (
    Event,
    EventFoodPreference,
    EventImage,
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
        session.add(event)
        session.expunge(event)
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
        return EventData.list(events)

def set_food_preferences(id: int, prefs: List[int]):
    with session_scope() as session:
        EventFoodPreference.add(session, id, prefs)

def get_event_image_by_event(id: int) -> Optional[EventImageData]:
    with session_scope() as session:
        event_image = EventImage.get_by_event(session, id)
        return EventImageData(event_image)
