import logging
import logging.handlers

from .config import get_settings


def setup_logging() -> None:
    s = get_settings()
    s.logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(s.log_level.upper())
    for h in list(root.handlers):
        root.removeHandler(h)
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    root.addHandler(stream)
    rotating = logging.handlers.RotatingFileHandler(
        s.logs_dir / "homehq.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    rotating.setFormatter(fmt)
    root.addHandler(rotating)
    logging.getLogger("httpx").setLevel(logging.WARNING)
