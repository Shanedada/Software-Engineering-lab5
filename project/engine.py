from __future__ import annotations
from typing import List
import random

from project.models import User, Preferences


class RecommendationEngine:
    """Simple in-memory recommendation engine using heuristics."""

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
        if not a.profile or not b.profile:
            return -1.0

        score = 0.0

        pref: Preferences = a.profile.preferences
        if b.profile.gender and b.profile.gender in pref.gender_preference:
            score += 20.0
        else:
            score -= 10.0

        b_age = b.profile.age()
        if b_age:
            if pref.matches_age(b_age):
                score += 15.0
            else:
                if b_age < pref.age_min:
                    score -= float(pref.age_min - b_age)
                elif b_age > pref.age_max:
                    score -= float(b_age - pref.age_max)

        shared = set(pref.interests).intersection(set(b.profile.preferences.interests))
        score += 5.0 * len(shared)

        score += 0.1 * b.profile.complete_percentage()

        if a.profile.location and b.profile.location:
            dist = a.profile.location.distance_km_to(b.profile.location)
            if dist > pref.max_distance_km:
                score -= (dist - pref.max_distance_km) * 0.2
            else:
                score += max(0, (pref.max_distance_km - dist) / max(1, pref.max_distance_km)) * 10.0

        score += random.random() * 2.0
        return score
