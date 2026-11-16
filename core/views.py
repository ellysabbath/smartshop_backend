from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


def list_create_view(model, serializer_class, perform_create=None):
    """
    Rudisha view function inayoshughulikia GET (list) na POST (create).
    perform_create(serializer, request) inaweza kubadilisha save().
    """
    @api_view(["GET", "POST"])
    @permission_classes([IsAuthenticated])
    def view(request):
        if request.method == "GET":
            qs = model.objects.all()
            serializer = serializer_class(qs, many=True)
            return Response(serializer.data)

        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            if perform_create:
                perform_create(serializer, request)
            else:
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return view


def detail_view(model, serializer_class):
    """
    Rudisha view function inayoshughulikia GET / PUT / PATCH / DELETE kwa record moja.
    """
    @api_view(["GET", "PUT", "PATCH", "DELETE"])
    @permission_classes([IsAuthenticated])
    def view(request, pk):
        obj = get_object_or_404(model, pk=pk)

        if request.method == "GET":
            return Response(serializer_class(obj).data)

        if request.method in ("PUT", "PATCH"):
            partial = request.method == "PATCH"
            serializer = serializer_class(obj, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return view