from django.db.models.signals import post_save, post_delete
from core import firebase
from firebase_sync.serializer import model_to_dict

SYNC_MODELS = {}


def register(app_label, model_name, table, model):
    SYNC_MODELS[f"{app_label}.{model_name}"] = {"table": table, "model": model}


def _on_save(sender, instance, created, **kwargs):
    cfg = SYNC_MODELS.get(f"{sender._meta.app_label}.{sender.__name__}")
    if not cfg:
        return
    firebase.push(cfg["table"], str(instance.pk), model_to_dict(instance))


def _on_delete(sender, instance, **kwargs):
    cfg = SYNC_MODELS.get(f"{sender._meta.app_label}.{sender.__name__}")
    if not cfg:
        return
    firebase.remove(cfg["table"], str(instance.pk))


def connect():
    for cfg in SYNC_MODELS.values():
        m = cfg["model"]
        post_save.connect(_on_save, sender=m,
                          dispatch_uid=f"fb_save_{m._meta.label}")
        post_delete.connect(_on_delete, sender=m,
                            dispatch_uid=f"fb_del_{m._meta.label}")