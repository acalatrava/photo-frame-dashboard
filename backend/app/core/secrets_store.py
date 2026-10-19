from sqlalchemy.orm import Session

from ..models import Secret
from . import security


def set_secret(db: Session, name: str, value: str) -> None:
    row = db.get(Secret, name)
    cipher = security.encrypt(value)
    if row:
        row.ciphertext = cipher
    else:
        db.add(Secret(name=name, ciphertext=cipher))
    db.flush()


def get_secret(db: Session, name: str) -> str | None:
    row = db.get(Secret, name)
    return security.decrypt(row.ciphertext) if row else None


def has_secret(db: Session, name: str) -> bool:
    return db.get(Secret, name) is not None


def delete_secret(db: Session, name: str) -> None:
    row = db.get(Secret, name)
    if row:
        db.delete(row)
        db.flush()
