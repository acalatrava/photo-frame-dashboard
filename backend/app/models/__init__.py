from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RefreshToken(Base):
    """Rotating refresh tokens. Re-using a rotated token revokes the whole family."""
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[str] = mapped_column(String(32), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(200), nullable=True)


class ApiToken(Base):
    """Long-lived, revocable credentials for scripts and AI agents (MCP). Only the SHA-256 of the token is stored."""
    __tablename__ = "api_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    prefix: Mapped[str] = mapped_column(String(12))
    scope: Mapped[str] = mapped_column(String(8), default="read")  # read | full | trigger
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    media_secret: Mapped[str] = mapped_column(String(64))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    config_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")
    hardware: Mapped[dict] = mapped_column(JSON, default=dict)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PairingRequest(Base):
    __tablename__ = "pairing_requests"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(8))
    poll_hash: Mapped[str] = mapped_column(String(64))
    hint: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|delivered|rejected|expired
    device_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConfigDoc(Base):
    """Versioned JSON documents (the global configuration lives in key 'global')."""
    __tablename__ = "config_docs"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Secret(Base):
    __tablename__ = "secrets"
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ShoppingItem(Base):
    """Items of the local shopping provider."""
    __tablename__ = "shopping_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    norm_name: Mapped[str] = mapped_column(String(200), index=True)
    note: Mapped[str] = mapped_column(String(300), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ShoppingOpLog(Base):
    """Idempotency log: a client operation id is applied at most once."""
    __tablename__ = "shopping_op_log"
    op_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Album(Base):
    __tablename__ = "albums"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = (UniqueConstraint("album_id", "sha256", name="uq_photo_album_hash"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    album_id: Mapped[str] = mapped_column(ForeignKey("albums.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    caption: Mapped[str] = mapped_column(String(200), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CalendarEvent(Base):
    """Cached, already expanded calendar occurrences (offline source for the devices)."""
    __tablename__ = "calendar_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(300))
    start: Mapped[str] = mapped_column(String(40))
    end: Mapped[str] = mapped_column(String(40))
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str] = mapped_column(String(300), default="")
    notes: Mapped[str] = mapped_column(Text, default="")


class SourceStatus(Base):
    """Last sync result per integration source (calendar sources, weather, ...)."""
    __tablename__ = "source_status"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    detail: Mapped[str] = mapped_column(String(500), default="")
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)


class Recording(Base):
    __tablename__ = "recordings"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    samples: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(String(300))
    duration_s: Mapped[float] = mapped_column(Float, default=0)


class ChoreLog(Base):
    """One completed check of a chore for a given local day (and person, empty for shared chores)."""
    __tablename__ = "chore_log"
    __table_args__ = (UniqueConstraint("chore_id", "day", "person_id", name="uq_chore_day_person"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chore_id: Mapped[str] = mapped_column(String(32), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)
    person_id: Mapped[str] = mapped_column(String(32), default="")
    done_by_device: Mapped[str | None] = mapped_column(String(32), nullable=True)
    done_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
