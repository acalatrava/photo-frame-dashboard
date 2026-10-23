from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..schemas.config import MenuConfig
from ..services import config_service
from ..services.menu import service as menu_service
from .deps import admin_required

router = APIRouter(prefix="/api/v1/admin/menu", tags=["admin-menu"], dependencies=[Depends(admin_required)])


class CurrentWeek(BaseModel):
    week: int = Field(ge=1, le=12)


def _view(db: Session) -> dict:
    g, _ = config_service.get_global(db)
    today = menu_service.today_in(g.general.timezone)
    return {"menu": g.menu.model_dump(mode="json"), **menu_service.describe(g.menu, today)}


@router.get("")
def get_menu(db: Session = Depends(get_db)):
    return _view(db)


@router.put("")
def put_menu(body: MenuConfig, db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    if body.weeks and not body.start_date:
        body = body.model_copy(update={"start_date": menu_service.monday(menu_service.today_in(g.general.timezone)).isoformat()})
    config_service.save_global(db, g.model_copy(update={"menu": body}))
    return _view(db)


@router.post("/current-week")
def current_week(body: CurrentWeek, db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    try:
        updated = menu_service.set_current_week(g.menu, body.week, menu_service.today_in(g.general.timezone))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    config_service.save_global(db, g.model_copy(update={"menu": updated}))
    return _view(db)
