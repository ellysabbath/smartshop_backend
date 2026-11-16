from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from core import firebase


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({
        "enabled": firebase.is_enabled(),
        "url": settings.FIREBASE_DATABASE_URL if firebase.is_enabled() else None,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def read_node(request, path: str):
    if not firebase.is_enabled():
        return Response({"detail": "Firebase imezimwa."}, status=503)
    try:
        data = firebase.ref(path).get()
        return Response({"path": path, "data": data})
    except Exception as exc:
        return Response({"detail": str(exc)}, status=500)