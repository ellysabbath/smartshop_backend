from django.shortcuts import render

# Create your views here.
# customers/views.py
from core.views import list_create_view, detail_view
from .models import Customer
from .serializers import CustomerSerializer


customers_list = list_create_view(Customer, CustomerSerializer)
customers_detail = detail_view(Customer, CustomerSerializer)