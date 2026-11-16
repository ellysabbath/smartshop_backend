from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Category, Unit, Product
from .serializers import (
    CategorySerializer,
    UnitSerializer,
    ProductSerializer,
)


# ==================================================================
# PRODUCTS — GET (list) + POST (create)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def products_list_create(request):
    if request.method == "GET":
        qs = Product.objects.select_related(
            "category", "unit"
        ).all().order_by("-created_at")
        return Response(ProductSerializer(qs, many=True).data)

    # POST
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.save()
        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )


# ==================================================================
# PRODUCT DETAIL — GET + PATCH + DELETE
# ==================================================================
@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "GET":
        return Response(ProductSerializer(product).data)

    if request.method == "PATCH":
        serializer = ProductSerializer(
            product, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ==================================================================
# CATEGORIES — GET + POST
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def categories_list_create(request):
    if request.method == "GET":
        qs = Category.objects.all().order_by("name")
        return Response(CategorySerializer(qs, many=True).data)

    name = (request.data.get("name") or "").strip()
    if not name:
        return Response(
            {"name": ["Jina la kundi linahitajika."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = Category.objects.filter(name__iexact=name).first()
    if existing:
        return Response(
            CategorySerializer(existing).data,
            status=status.HTTP_200_OK,
        )

    cat = Category.objects.create(name=name)
    return Response(
        CategorySerializer(cat).data,
        status=status.HTTP_201_CREATED,
    )


# ==================================================================
# UNITS — GET + POST
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def units_list_create(request):
    if request.method == "GET":
        qs = Unit.objects.all().order_by("name")
        return Response(UnitSerializer(qs, many=True).data)

    name = (request.data.get("name") or "").strip()
    if not name:
        return Response(
            {"name": ["Jina la kipimo linahitajika."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = Unit.objects.filter(name__iexact=name).first()
    if existing:
        return Response(
            UnitSerializer(existing).data,
            status=status.HTTP_200_OK,
        )

    unit = Unit.objects.create(name=name)
    return Response(
        UnitSerializer(unit).data,
        status=status.HTTP_201_CREATED,
    )