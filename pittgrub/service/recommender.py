from typing import List, Union

from domain.data import UserData
from db import (
    Event,
    User,
    UserRecommendedEvent,
    session_scope
)


def food_preference_filter(user: User, event: Event) -> bool:
    event_food_preferences = [fp.id for fp in event.food_preferences]
    user_food_preferences = [fp.id for fp in user.food_preferences]
    return all(fp in event_food_preferences for fp in user_food_preferences)


def should_recommend(user: User, event: Event) -> bool:
    return food_preference_filter(user, event)


def _event_recommendation(event: Union[Event, 'EventData']) -> List[User]:
    recommendations = []
    with session_scope() as session:
        users = User.get_all(session)
        event = Event.get_by_id(session, event.id)
        for user in users:
            if should_recommend(user, event):
                user_rec = UserRecommendedEvent(event.id, user.id)
                session.add(user_rec)
                session.expunge(user)
                recommendations.append(user)
    return recommendations


def event_recommendation(event: Union[Event, 'EventData']) -> List[UserData]:
    return [UserData(user) for user in _event_recommendation(event)]
