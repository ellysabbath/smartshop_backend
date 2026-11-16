from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    aliyezalisha_name = serializers.CharField(
        source="aliyezalisha.full_name", read_only=True
    )

    class Meta:
        model = Document
        fields = [
            "id",
            "jina",
            "aina",
            "format",
            "hali",
            "ukubwa",
            "kipindi",
            "store",
            "store_name",
            "aliyezalisha",
            "aliyezalisha_name",
            "data_snapshot",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "hali",
            "ukubwa",
            "aliyezalisha",
            "data_snapshot",
            "created_at",
        ]