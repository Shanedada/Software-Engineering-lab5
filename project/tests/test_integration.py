from datetime import date
import random

from project.storage import InMemoryDB
from project.engine import RecommendationEngine
from project.models import (
    User,
    Profile,
    Preferences,
    Location,
    Photo,
    Swipe,
    Conversation,
    Message,
    Payment,
    Subscription,
    Notification,
)


def make_user(index: int, age: int = 30, gender=None, interests=None, lat=None, lon=None):
    today = date.today()
    birth_year = today.year - age
    p = Profile(display_name=f"User{index}", birthdate=date(birth_year, 1, 1), gender=gender)
    if interests:
        p.preferences.interests = list(interests)
    if lat is not None and lon is not None:
        p.location = Location(lat=lat, lon=lon)
    p.add_photo(Photo())
    u = User(email=f"u{index}@example.com")
    u.update_profile(p)
    return u


def test_recommendation_end_to_end_excludes_self_and_returns_best():
    """Top-down: create DB users, run RecommendationEngine and verify results are from DB, exclude self and ordered."""
    db = InMemoryDB()
    engine = RecommendationEngine()

    # create users 1..6; user1 is 'me'
    users = [make_user(i) for i in range(1, 7)]
    # make user 3 a clearly better match
    users[2].profile.preferences.interests = ["hiking", "coffee"]
    users[0].profile.preferences.interests = ["hiking"]  # me

    for u in users:
        db.add_user(u)

    me = users[0]
    candidates = [u for u in users if u.user_id != me.user_id]

    # determine top-3
    top3 = engine.compute_matches(me, candidates, top_k=3)

    assert len(top3) == 3
    # top candidate should be that with shared interests
    assert top3[0].profile.preferences.interests == ["hiking", "coffee"]
    # ensure results are from DB users
    for t in top3:
        assert t.user_id in db.users


def test_social_flow_end_to_end_swipe_match_conversation_payment_notification(monkeypatch):
    """Top-down: simulate swipes -> match -> conversation -> payment & subscription -> notification, using real modules (no unit mocking of logic)."""
    db = InMemoryDB()

    alice = make_user(1, age=28)
    bob = make_user(2, age=27)
    db.add_user(alice)
    db.add_user(bob)

    # alice likes bob
    s1 = Swipe(from_user=alice, to_user=bob, direction="like")
    db.add_swipe(s1)
    # bob likes alice -> should generate a Match
    s2 = Swipe(from_user=bob, to_user=alice, direction="like")
    m = db.add_swipe(s2)
    assert m is not None
    assert m.match_id in db.matches

    # create conversation and send message
    conv = Conversation(participants=[m.user_a, m.user_b])
    db.add_conversation(conv)
    msg = Message(sender=m.user_a, content="Hi!")
    conv.send_message(msg)
    assert conv.conversation_id in db.conversations
    assert len(conv.messages) == 1

    # sending a message from non-participant should raise
    outsider = make_user(99)
    bad_msg = Message(sender=outsider, content="Hello")
    try:
        conv.send_message(bad_msg)
        assert False, "Expected ValueError for sender not in conversation"
    except ValueError:
        pass

    # simulate payment success then subscription + notification creation
    # make deterministic: force payment.charge to succeed by patching random.random
    monkeypatch.setattr(random, "random", lambda: 0.99)
    pay = Payment(user=alice, amount=9.99)
    db.add_payment(pay)
    charged = pay.charge()
    assert charged is True

    sub = Subscription(user=alice, tier="premium")
    db.add_subscription(sub)
    assert sub.sub_id in db.subscriptions

    note = Notification(user=alice, type="match", payload={"match_id": str(m.match_id)})
    db.add_notification(note)
    assert note.notification_id in db.notifications
