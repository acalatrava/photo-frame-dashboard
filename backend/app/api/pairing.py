from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..devices import service
from ..models import PairingRequest
from .deps import RateLimiter, client_ip

router = APIRouter(prefix="/api/v1/pairing", tags=["pairing"])
req_limiter = RateLimiter(6, 600)
poll_limiter = RateLimiter(120, 600)


class PairingBody(BaseModel):
    name: str = Field("", max_length=80)
    model: str = Field("", max_length=80)
    app_version: str = Field("", max_length=32)
    screen: str = Field("", max_length=32)


class PollBody(BaseModel):
    poll_secret: str = Field(max_length=100)


@router.post("/request")
def request_pairing(body: PairingBody, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    if not req_limiter.check(ip):
        raise HTTPException(429, "Demasiadas solicitudes de emparejamiento")
    try:
        req, secret = service.create_request(db, body.model_dump(), ip)
    except ValueError as exc:
        raise HTTPException(429, str(exc)) from exc
    return {"request_id": req.id, "code": req.code, "poll_secret": secret, "expires_at": req.expires_at.isoformat()}


@router.post("/{request_id}/poll")
def poll(request_id: str, body: PollBody, request: Request, db: Session = Depends(get_db)):
    if not poll_limiter.check(client_ip(request)):
        raise HTTPException(429, "Demasiadas consultas")
    req = db.get(PairingRequest, request_id)
    if not req:
        raise HTTPException(404, "Solicitud desconocida")
    res = service.collect(db, req, body.poll_secret)
    if res["status"] == "invalid":
        raise HTTPException(403, "Secreto no válido")
    return res
