from django.shortcuts import render

# Create your views here.
from core.views import list_create_view, detail_view
from .models import Store
from .serializers import StoreSerializer


def _perform_create(serializer, request):
    serializer.save(owner=request.user)


stores_list_create = list_create_view(Store, StoreSerializer, _perform_create)
stores_detail = detail_view(Store, StoreSerializer)