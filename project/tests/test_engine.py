import random
from datetime import date

import pytest

from project.engine import RecommendationEngine
from project.models import User, Profile, Preferences, Location, Gender, Photo


def make_user_with_profile(index: int, gender: Gender = Gender.FEMALE, age: int = 30, interests=None, lat=None, lon=None):
    u = User(email=f"u{index}@example.com")
    # compute birthdate such that age is roughly `age`
    today = date.today()
    birth_year = today.year - age
    bd = date(birth_year, 1, 1)
    p = Profile(display_name=f"User{index}", birthdate=bd, gender=gender, bio="bio")
    if interests is not None:
        p.preferences.interests = list(interests)
    if lat is not None and lon is not None:
        p.location = Location(lat=lat, lon=lon)
    # add a photo to increase completeness if desired
    p.add_photo(Photo())
    u.update_profile(p)
    return u


def test_score_missing_profile_returns_negative():
    eng = RecommendationEngine()
    a = User(email="a@example.com")
    b = User(email="b@example.com")
    assert eng.score(a, b) == -1.0


def test_gender_match_higher_than_mismatch(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1, gender=Gender.FEMALE)
    # prefer FEMALE
    a.profile.preferences.gender_preference = [Gender.FEMALE]

    b_match = make_user_with_profile(2, gender=Gender.FEMALE)
    b_mismatch = make_user_with_profile(3, gender=Gender.MALE)

    # make randomness deterministic
    monkeypatch.setattr(random, "random", lambda: 0.0)

    score_match = eng.score(a, b_match)
    score_mismatch = eng.score(a, b_mismatch)
    assert score_match > score_mismatch


def test_age_within_range_vs_outside(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1)
    a.profile.preferences.age_min = 25
    a.profile.preferences.age_max = 35

    b_inside = make_user_with_profile(2, age=30)
    b_below = make_user_with_profile(3, age=20)
    b_above = make_user_with_profile(4, age=50)

    monkeypatch.setattr(random, "random", lambda: 0.0)

    s_inside = eng.score(a, b_inside)
    s_below = eng.score(a, b_below)
    s_above = eng.score(a, b_above)

    assert s_inside > s_below
    assert s_inside > s_above


def test_shared_interests_increase(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1, interests=["hiking", "coffee"])
    b_shared = make_user_with_profile(2, interests=["hiking", "music"])
    b_none = make_user_with_profile(3, interests=["movies"])

    monkeypatch.setattr(random, "random", lambda: 0.0)

    s_shared = eng.score(a, b_shared)
    s_none = eng.score(a, b_none)
    assert s_shared > s_none


def test_profile_completeness_increases_score(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1, interests=[])
    b_incomplete = make_user_with_profile(2, interests=[])
    # make b_complete more complete (add photo already exists then add bio and location)
    b_complete = make_user_with_profile(3, interests=[])
    b_complete.profile.bio = "long bio"
    b_complete.profile.location = Location(lat=0.0, lon=0.0)

    monkeypatch.setattr(random, "random", lambda: 0.0)

    s_incomplete = eng.score(a, b_incomplete)
    s_complete = eng.score(a, b_complete)
    assert s_complete > s_incomplete


def test_distance_penalty_and_bonus(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1, lat=37.0, lon=-122.0)
    # set a pref max_distance small so far user is penalized
    a.profile.preferences.max_distance_km = 5

    b_near = make_user_with_profile(2, lat=37.001, lon=-122.001)
    b_far = make_user_with_profile(3, lat=38.0, lon=-123.0)

    monkeypatch.setattr(random, "random", lambda: 0.0)

    s_near = eng.score(a, b_near)
    s_far = eng.score(a, b_far)
    assert s_near > s_far


def test_compute_matches_returns_top_k(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1)
    candidates = [make_user_with_profile(i) for i in range(2, 12)]
    # adjust one candidate to be clearly best
    candidates[3].profile.preferences.interests = ["hiking", "coffee"]
    a.profile.preferences.interests = ["hiking"]

    monkeypatch.setattr(random, "random", lambda: 0.0)

    top5 = eng.compute_matches(a, candidates, top_k=5)
    assert len(top5) == 5
    # ensure ordering: best candidate is first
    assert top5[0].profile.preferences.interests == candidates[3].profile.preferences.interests


def test_random_tiebreaker_effect(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1)
    b1 = make_user_with_profile(2)
    b2 = make_user_with_profile(3)

    # force deterministic different random values
    monkeypatch.setattr(random, "random", lambda: 0.0)
    s1 = eng.score(a, b1)
    # change random to a higher value
    monkeypatch.setattr(random, "random", lambda: 1.0)
    s2 = eng.score(a, b2)
    # since base characteristics similar, s2 likely >= s1 due to bigger random
    assert s2 >= s1


def test_score_is_finite(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1)
    b = make_user_with_profile(2)
    monkeypatch.setattr(random, "random", lambda: 0.5)
    s = eng.score(a, b)
    assert isinstance(s, float)
    assert not (s != s)  # not NaN


def test_compute_matches_excludes_self_and_ordering(monkeypatch):
    eng = RecommendationEngine()
    a = make_user_with_profile(1)
    # create candidates including 'a' itself
    candidates = [a] + [make_user_with_profile(i) for i in range(2, 7)]
    # make candidate 2 clearly the best match
    candidates[1].profile.preferences.interests = ["hiking", "coffee"]
    a.profile.preferences.interests = ["hiking"]

    monkeypatch.setattr(random, "random", lambda: 0.0)

    top3 = eng.compute_matches(a, candidates, top_k=3)
    # self should be excluded
    assert all(u.user_id != a.user_id for u in top3)
    # best candidate (candidate 2) should be first
    assert top3[0].profile.preferences.interests == candidates[1].profile.preferences.interests
