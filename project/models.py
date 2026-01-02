from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any

from project.utils import gen_uuid, now, hash_password, age_from_birthdate


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    NONBINARY = "nonbinary"
    OTHER = "other"


@dataclass
class Location:
    lat: float
    lon: float
    city: str = ""
    country: str = ""

    def distance_km_to(self, other: "Location") -> float:
        dx = (self.lat - other.lat) * 111.0
        dy = (self.lon - other.lon) * 111.0
        return (dx * dx + dy * dy) ** 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"lat": self.lat, "lon": self.lon, "city": self.city, "country": self.country}


@dataclass
class Photo:
    photo_id: uuid.UUID = field(default_factory=gen_uuid)
    url: str = ""
    order: int = 0
    uploaded_at: Optional[datetime] = None

    def upload(self):
        self.uploaded_at = now()
        if not self.url:
            self.url = f"https://cdn.example.com/photos/{self.photo_id}.jpg"

    def delete(self):
        self.url = ""
        self.uploaded_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {"photo_id": str(self.photo_id), "url": self.url, "order": self.order, "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None}


@dataclass
class Preferences:
    gender_preference: List[Gender] = field(default_factory=lambda: [Gender.FEMALE, Gender.MALE, Gender.NONBINARY])
    age_min: int = 18
    age_max: int = 99
    max_distance_km: int = 100
    interests: List[str] = field(default_factory=list)

    def matches_age(self, age: int) -> bool:
        return self.age_min <= age <= self.age_max

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gender_preference": [g.value for g in self.gender_preference],
            "age_min": self.age_min,
            "age_max": self.age_max,
            "max_distance_km": self.max_distance_km,
            "interests": list(self.interests),
        }


@dataclass
class Profile:
    profile_id: uuid.UUID = field(default_factory=gen_uuid)
    display_name: str = ""
    birthdate: Optional[date] = None
    gender: Optional[Gender] = None
    bio: str = ""
    photos: List[Photo] = field(default_factory=list)
    location: Optional[Location] = None
    preferences: Preferences = field(default_factory=Preferences)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def complete_percentage(self) -> int:
        score = 0
        total = 6
        if self.display_name:
            score += 1
        if self.birthdate:
            score += 1
        if self.gender:
            score += 1
        if self.bio:
            score += 1
        if self.photos:
            score += 1
        if self.location:
            score += 1
        return int((score / total) * 100)

    def add_photo(self, photo: Photo):
        photo.order = len(self.photos)
        photo.upload()
        self.photos.append(photo)
        self.updated_at = now()

    def remove_photo(self, photo_id: uuid.UUID):
        self.photos = [p for p in self.photos if p.photo_id != photo_id]
        for i, p in enumerate(self.photos):
            p.order = i
        self.updated_at = now()

    def age(self) -> Optional[int]:
        if not self.birthdate:
            return None
        return age_from_birthdate(self.birthdate)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": str(self.profile_id),
            "display_name": self.display_name,
            "birthdate": self.birthdate.isoformat() if self.birthdate else None,
            "gender": self.gender.value if self.gender else None,
            "bio": self.bio,
            "photos": [p.to_dict() for p in self.photos],
            "location": self.location.to_dict() if self.location else None,
            "preferences": self.preferences.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class User:
    user_id: uuid.UUID = field(default_factory=gen_uuid)
    email: str = ""
    password_hash: str = ""
    created_at: datetime = field(default_factory=now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    profile: Optional[Profile] = None
    email_verified: bool = False

    def set_password(self, password: str):
        self.password_hash = hash_password(password)

    def verify_password(self, password: str) -> bool:
        return self.password_hash == hash_password(password)

    def verify_email(self) -> bool:
        self.email_verified = True
        return self.email_verified

    def update_profile(self, p: Profile):
        self.profile = p
        self.profile.updated_at = now()

    def login(self) -> None:
        self.last_login = now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "profile": self.profile.to_dict() if self.profile else None,
        }


@dataclass
class Swipe:
    swipe_id: uuid.UUID = field(default_factory=gen_uuid)
    from_user: User = None
    to_user: User = None
    direction: str = "pass"
    timestamp: datetime = field(default_factory=now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swipe_id": str(self.swipe_id),
            "from_user": str(self.from_user.user_id) if self.from_user else None,
            "to_user": str(self.to_user.user_id) if self.to_user else None,
            "direction": self.direction,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Match:
    match_id: uuid.UUID = field(default_factory=gen_uuid)
    user_a: User = None
    user_b: User = None
    created_at: datetime = field(default_factory=now)
    is_active: bool = True

    def unmatch(self):
        self.is_active = False

    def other(self, user: User) -> Optional[User]:
        if user.user_id == self.user_a.user_id:
            return self.user_b
        if user.user_id == self.user_b.user_id:
            return self.user_a
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": str(self.match_id),
            "user_a": str(self.user_a.user_id) if self.user_a else None,
            "user_b": str(self.user_b.user_id) if self.user_b else None,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }


@dataclass
class Message:
    message_id: uuid.UUID = field(default_factory=gen_uuid)
    sender: User = None
    content: str = ""
    sent_at: datetime = field(default_factory=now)
    edited_at: Optional[datetime] = None
    is_read: bool = False

    def edit(self, new_content: str):
        self.content = new_content
        self.edited_at = now()

    def mark_read(self):
        self.is_read = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": str(self.message_id),
            "sender": str(self.sender.user_id) if self.sender else None,
            "content": self.content,
            "sent_at": self.sent_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "is_read": self.is_read,
        }


@dataclass
class Conversation:
    conversation_id: uuid.UUID = field(default_factory=gen_uuid)
    participants: List[User] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    last_message_at: Optional[datetime] = None
    messages: List[Message] = field(default_factory=list)

    def send_message(self, m: Message) -> Message:
        if not any(p.user_id == m.sender.user_id for p in self.participants):
            raise ValueError("Sender not in conversation participants")
        self.messages.append(m)
        self.last_message_at = m.sent_at
        return m

    def add_participant(self, user: User):
        if not any(u.user_id == user.user_id for u in self.participants):
            self.participants.append(user)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": str(self.conversation_id),
            "participants": [str(p.user_id) for p in self.participants],
            "created_at": self.created_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "messages": [m.to_dict() for m in self.messages],
        }


@dataclass
class Notification:
    notification_id: uuid.UUID = field(default_factory=gen_uuid)
    user: User = None
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    sent_at: datetime = field(default_factory=now)
    read_at: Optional[datetime] = None

    def read(self):
        self.read_at = now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": str(self.notification_id),
            "user": str(self.user.user_id) if self.user else None,
            "type": self.type,
            "payload": self.payload,
            "sent_at": self.sent_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


@dataclass
class Report:
    report_id: uuid.UUID = field(default_factory=gen_uuid)
    reporter: User = None
    reported_user: User = None
    reason: str = ""
    created_at: datetime = field(default_factory=now)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None

    def resolve(self, resolution: str):
        self.resolution = resolution
        self.resolved_at = now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": str(self.report_id),
            "reporter": str(self.reporter.user_id) if self.reporter else None,
            "reported_user": str(self.reported_user.user_id) if self.reported_user else None,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
        }


@dataclass
class Subscription:
    sub_id: uuid.UUID = field(default_factory=gen_uuid)
    user: User = None
    tier: str = "free"
    started_at: datetime = field(default_factory=now)
    expires_at: Optional[datetime] = None

    def is_active(self) -> bool:
        if self.tier == "free":
            return True
        if not self.expires_at:
            return False
        return now() < self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_id": str(self.sub_id),
            "user": str(self.user.user_id) if self.user else None,
            "tier": self.tier,
            "started_at": self.started_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


import random


@dataclass
class Payment:
    payment_id: uuid.UUID = field(default_factory=gen_uuid)
    user: User = None
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    created_at: datetime = field(default_factory=now)

    def charge(self) -> bool:
        """Attempt to charge and return True on success, False on failure.

        This method should not raise for normal numeric amounts. Validate the
        amount input and avoid dangerous arithmetic that could raise exceptions.
        """
        if not isinstance(self.amount, (int, float)):
            raise TypeError("amount must be a number")
        success = random.random() > 0.1
        self.status = "succeeded" if success else "failed"
        return success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_id": str(self.payment_id),
            "user": str(self.user.user_id) if self.user else None,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
