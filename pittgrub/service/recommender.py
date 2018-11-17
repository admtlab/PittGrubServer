import logging
from typing import List, Union, Dict, Any
from random import shuffle
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
    return user.active and not user.disabled and food_preference_filter(user, event)


def _event_recommendation(event: Union[Event, 'EventData'], with_params: Dict[str,Any]=None) -> List[User]:
    recommendations = []
    with session_scope() as session:
        users = list(User.get_all(session))
        event = Event.get_by_id(session, event.id)
        capacity  = len(users)
        if with_params is not None and 'avg_prob' in with_params:
            avprob = float(with_params['avg_prob'])
            capacity = event.servings / avprob if avprob > 0 else len(users)
            shuffle(users); pushed = 0
        for user in users:
            if should_recommend(user, event) and pushed <= capacity:
                user_rec = UserRecommendedEvent(event.id, user.id)
                session.add(user_rec)
                session.expunge(user)
                recommendations.append(user)
                pushed += 1
            elif pushed > capacity:
                break
    return recommendations


def event_recommendation(event: Union[Event, 'EventData']) -> List[UserData]:
    return [UserData(user) for user in _event_recommendation(event)]
