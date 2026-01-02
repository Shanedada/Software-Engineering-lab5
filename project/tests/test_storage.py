from project.storage import InMemoryDB
from project.models import User, Profile, Preferences, Location, Photo, Swipe, Conversation, Message, Payment, Subscription, Notification, Report
from datetime import date


def make_user_with_profile(index: int, age: int = 30):
    u = User(email=f"u{index}@example.com")
    today = date.today()
    birth_year = today.year - age
    p = Profile(display_name=f"User{index}", birthdate=date(birth_year, 1, 1))
    p.add_photo(Photo())
    u.update_profile(p)
    return u


def test_add_user_and_find_by_email():
    db = InMemoryDB()
    u = User(email="Test@Example.com")
    db.add_user(u)
    found = db.find_user_by_email("test@example.com")
    assert found is not None
    assert found.email == u.email


def test_add_swipe_creates_match_on_mutual_like():
    db = InMemoryDB()
    u1 = make_user_with_profile(1)
    u2 = make_user_with_profile(2)
    db.add_user(u1)
    db.add_user(u2)

    s1 = Swipe(from_user=u1, to_user=u2, direction="like")
    db.add_swipe(s1)
    # second like should return a match
    s2 = Swipe(from_user=u2, to_user=u1, direction="like")
    m = db.add_swipe(s2)
    assert m is not None
    assert m.match_id in db.matches


def test_add_swipe_no_match_on_pass():
    db = InMemoryDB()
    u1 = make_user_with_profile(1)
    u2 = make_user_with_profile(2)
    db.add_user(u1)
    db.add_user(u2)

    db.add_swipe(Swipe(from_user=u1, to_user=u2, direction="pass"))
    m = db.add_swipe(Swipe(from_user=u2, to_user=u1, direction="like"))
    assert m is None


def test_no_duplicate_match_creation():
    db = InMemoryDB()
    u1 = make_user_with_profile(1)
    u2 = make_user_with_profile(2)
    db.add_user(u1)
    db.add_user(u2)

    db.add_swipe(Swipe(from_user=u1, to_user=u2, direction="like"))
    m1 = db.add_swipe(Swipe(from_user=u2, to_user=u1, direction="like"))
    assert m1 is not None

    # another mutual set should not create new match
    db.add_swipe(Swipe(from_user=u1, to_user=u2, direction="like"))
    m2 = db.add_swipe(Swipe(from_user=u2, to_user=u1, direction="like"))
    matches = list(db.matches.values())
    assert len(matches) == 1


def test_add_conversation_stores_conv():
    db = InMemoryDB()
    u1 = make_user_with_profile(1)
    u2 = make_user_with_profile(2)
    conv = Conversation(participants=[u1, u2])
    db.add_conversation(conv)
    assert conv.conversation_id in db.conversations


def test_add_notification_stores():
    db = InMemoryDB()
    u = make_user_with_profile(1)
    note = Notification(user=u, type="match", payload={})
    db.add_notification(note)
    assert note.notification_id in db.notifications


def test_add_report_stores():
    db = InMemoryDB()
    reporter = make_user_with_profile(1)
    reported = make_user_with_profile(2)
    r = Report(reporter=reporter, reported_user=reported, reason="spam")
    db.add_report(r)
    assert r.report_id in db.reports


def test_add_subscription_and_payment_stores():
    db = InMemoryDB()
    u = make_user_with_profile(1)
    p = Payment(user=u, amount=19.99)
    db.add_payment(p)
    s = Subscription(user=u, tier="premium")
    db.add_subscription(s)
    assert p.payment_id in db.payments
    assert s.sub_id in db.subscriptions


def test_find_user_by_email_case_insensitive():
    db = InMemoryDB()
    u = User(email="Cap@Email.COM")
    db.add_user(u)
    assert db.find_user_by_email("cap@email.com") is not None


def test_find_user_returns_none_when_missing():
    db = InMemoryDB()
    assert db.find_user_by_email("doesnotexist@example.com") is None
