from __future__ import annotations
from typing import Dict, Optional
import uuid

from project.models import User, Swipe, Match, Conversation, Notification, Report, Subscription, Payment


class InMemoryDB:
    def __init__(self):
        self.users: Dict[uuid.UUID, User] = {}
        self.swipes: Dict[uuid.UUID, Swipe] = {}
        self.matches: Dict[uuid.UUID, Match] = {}
        self.conversations: Dict[uuid.UUID, Conversation] = {}
        self.notifications: Dict[uuid.UUID, Notification] = {}
        self.reports: Dict[uuid.UUID, Report] = {}
        self.subscriptions: Dict[uuid.UUID, Subscription] = {}
        self.payments: Dict[uuid.UUID, Payment] = {}

    def add_user(self, user: User):
        self.users[user.user_id] = user

    def find_user_by_email(self, email: str) -> Optional[User]:
        for u in self.users.values():
            if u.email.lower() == email.lower():
                return u
        return None

    def add_swipe(self, swipe: Swipe):
        self.swipes[swipe.swipe_id] = swipe
        if swipe.direction == "like":
            for other in self.swipes.values():
                if other.from_user.user_id == swipe.to_user.user_id and other.to_user.user_id == swipe.from_user.user_id and other.direction == "like":
                    if not self._match_exists_between(swipe.from_user, swipe.to_user):
                        m = Match(user_a=swipe.from_user, user_b=swipe.to_user)
                        self.matches[m.match_id] = m
                        return m
        return None

    def _match_exists_between(self, a: User, b: User) -> bool:
        for m in self.matches.values():
            if (m.user_a.user_id == a.user_id and m.user_b.user_id == b.user_id) or (m.user_a.user_id == b.user_id and m.user_b.user_id == a.user_id):
                return True
        return False

    def add_match(self, match: Match):
        self.matches[match.match_id] = match

    def add_conversation(self, conv: Conversation):
        self.conversations[conv.conversation_id] = conv

    def add_notification(self, note: Notification):
        self.notifications[note.notification_id] = note

    def add_report(self, report: Report):
        self.reports[report.report_id] = report

    def add_subscription(self, sub: Subscription):
        self.subscriptions[sub.sub_id] = sub

    def add_payment(self, payment: Payment):
        self.payments[payment.payment_id] = payment
