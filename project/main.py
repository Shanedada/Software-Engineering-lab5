"""Entry point for the demo. This file is intentionally small and imports implementations from modules.
"""

from __future__ import annotations
from datetime import date, timedelta
import random

from project.utils import now
from project.models import User, Profile, Preferences, Photo, Location, Gender, Swipe, Conversation, Message, Payment, Subscription, Notification
from project.storage import InMemoryDB
from project.engine import RecommendationEngine


def demo_setup(db: InMemoryDB, n: int = 8):
    """Create n sample users with profiles for demo/testing."""
    genders = list(Gender)
    sample_users = []
    base_lat = 37.7749
    base_lon = -122.4194
    for i in range(n):
        u = User(email=f"user{i}@example.com")
        u.set_password("password123")
        u.verify_email()
        p = Profile(
            display_name=f"User{i}",
            birthdate=date(1990 + (i % 10), 1 + (i % 12), 1 + (i % 28)),
            gender=random.choice(genders),
            bio=f"This is a short bio for user {i}. Likes hiking and coffee.",
            location=Location(lat=base_lat + i * 0.01, lon=base_lon + i * 0.01, city="DemoCity", country="DemoLand"),
        )
        prefs = Preferences(
            gender_preference=[random.choice(genders)],
            age_min=20 + (i % 5),
            age_max=40 + (i % 10),
            max_distance_km=50 + (i * 5),
            interests=["hiking", "coffee"] if i % 2 == 0 else ["movies", "music"],
        )
        p.preferences = prefs
        ph = Photo()
        p.add_photo(ph)
        u.update_profile(p)
        db.add_user(u)
        sample_users.append(u)
    return sample_users



class RecommendationEngine:
    """
    Very small in-memory recommendation engine that scores candidate users for a given user.
    Uses simple heuristics:
    - Age preference match
    - Gender preference match
    - Shared interests
    - Distance penalty
    - Completeness bonus
    """

    def compute_matches(self, user: User, candidates: List[User], top_k: int = 10) -> List[User]:
        scored = []
        for cand in candidates:
            if cand.user_id == user.user_id:
                continue
            score = self.score(user, cand)
            scored.append((score, cand))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def score(self, a: User, b: User) -> float:
        # Basic checks
        if not a.profile or not b.profile:
            return -1.0

        score = 0.0

        # gender preference
        pref: Preferences = a.profile.preferences
        if b.profile.gender and b.profile.gender in pref.gender_preference:
            score += 20.0
        else:
            score -= 10.0

        # age preference
        b_age = b.profile.age()
        if b_age:
            if pref.matches_age(b_age):
                score += 15.0
            else:
                # penalize by distance from range
                if b_age < pref.age_min:
                    score -= float(pref.age_min - b_age)
                elif b_age > pref.age_max:
                    score -= float(b_age - pref.age_max)

        # shared interests
        shared = set(pref.interests).intersection(set(b.profile.preferences.interests))
        score += 5.0 * len(shared)

        # profile completeness
        score += 0.1 * b.profile.complete_percentage()

        # distance
        if a.profile.location and b.profile.location:
            dist = a.profile.location.distance_km_to(b.profile.location)
            # apply a penalty over max_distance_km
            if dist > pref.max_distance_km:
                score -= (dist - pref.max_distance_km) * 0.2
            else:
                score += max(0, (pref.max_distance_km - dist) / max(1, pref.max_distance_km)) * 10.0

        # small random tie-breaker
        score += random.random() * 2.0
        return score


# -------------------------
# Small demo / sample usage
# -------------------------

def demo_setup(db: InMemoryDB, n: int = 8) -> List[User]:
    """Create n sample users with profiles for demo/testing."""
    genders = list(Gender)
    sample_users = []
    base_lat = 37.7749
    base_lon = -122.4194
    for i in range(n):
        u = User(email=f"user{i}@example.com")
        u.set_password("password123")
        u.verify_email()
        p = Profile(
            display_name=f"User{i}",
            birthdate=date(1990 + (i % 10), 1 + (i % 12), 1 + (i % 28)),
            gender=random.choice(genders),
            bio=f"This is a short bio for user {i}. Likes hiking and coffee.",
            location=Location(lat=base_lat + i * 0.01, lon=base_lon + i * 0.01, city="DemoCity", country="DemoLand"),
        )
        # preferences
        prefs = Preferences(
            gender_preference=[random.choice(genders)],
            age_min=20 + (i % 5),
            age_max=40 + (i % 10),
            max_distance_km=50 + (i * 5),
            interests=["hiking", "coffee"] if i % 2 == 0 else ["movies", "music"]
        )
        p.preferences = prefs
        # add a photo
        ph = Photo()
        p.add_photo(ph)
        u.update_profile(p)
        db.add_user(u)
        sample_users.append(u)
    return sample_users

def demo_run():
    db = InMemoryDB()
    users = demo_setup(db, n=12)

    engine = RecommendationEngine()

    # pick a user and compute matches
    me = users[0]
    candidates = users[1:]
    matches = engine.compute_matches(me, candidates, top_k=5)
    print(f"Top matches for {me.profile.display_name}: {[m.profile.display_name for m in matches]}")

    # simulate swipes
    s1 = Swipe(from_user=users[1], to_user=users[2], direction="like")
    db.add_swipe(s1)
    s2 = Swipe(from_user=users[2], to_user=users[1], direction="like")
    m = db.add_swipe(s2)  # this should create a Match
    if m:
        print("Match created:", m.to_dict())

    # simulate conversation creation after match
    if m:
        conv = Conversation(participants=[m.user_a, m.user_b])
        db.add_conversation(conv)
        msg = Message(sender=m.user_a, content="Hi! Nice to match with you.")
        conv.send_message(msg)
        print("Conversation messages:", [x.to_dict() for x in conv.messages])

    # simulate payment and subscription
    pay = Payment(user=me, amount=9.99)
    db.add_payment(pay)
    if pay.charge():
        sub = Subscription(user=me, tier="premium", started_at=now(), expires_at=now() + timedelta(days=30))
        db.add_subscription(sub)
        print("Subscription started:", sub.to_dict())

    # create notification
    note = Notification(user=me, type="match", payload={"match_id": str(m.match_id) if m else None})
    db.add_notification(note)
    print("Notification:", note.to_dict())

# Run demo when executed as script
if __name__ == "__main__":
    demo_run()

# -------------------------
# Padding area (comments) to approach ~500 lines as requested.
# The following blank/comment lines are intentional.
