from django.shortcuts import render

# Create your views here.
# suppliers/views.py
from core.views import list_create_view, detail_view
from .models import Supplier
from .serializers import SupplierSerializer

suppliers_list = list_create_view(Supplier, SupplierSerializer)
suppliers_detail = detail_view(Supplier, SupplierSerializer)
