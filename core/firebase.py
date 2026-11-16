"""Firebase Realtime Database client."""
import logging
import firebase_admin
from firebase_admin import credentials, db
from django.conf import settings

logger = logging.getLogger(__name__)
_app = None


def _ensure_init():
    global _app
    if _app is not None:
        return _app
    if not getattr(settings, "FIREBASE_REALTIME_ENABLED", False):
        return None
    if firebase_admin._apps:
        _app = firebase_admin.get_app()
        return _app
    try:
        cred = credentials.Certificate(str(settings.FIREBASE_CREDENTIALS))
        _app = firebase_admin.initialize_app(cred, {
            "databaseURL": settings.FIREBASE_DATABASE_URL,
        })
        logger.info("Firebase initialized: %s", settings.FIREBASE_DATABASE_URL)
    except Exception:
        logger.exception("Firebase init failed")
        _app = None
    return _app


def is_enabled():
    return _ensure_init() is not None


def ref(path: str = "/"):
    _ensure_init()
    return db.reference(path.strip("/"))


def push(table: str, uuid: str, data: dict) -> None:
    if not is_enabled():
        return
    try:
        ref(f"{table}/{uuid}").set(data)
    except Exception:
        logger.exception("Firebase push failed")


def remove(table: str, uuid: str) -> None:
    if not is_enabled():
        return
    try:
        ref(f"{table}/{uuid}").delete()
    except Exception:
        logger.exception("Firebase remove failed")