from rest_framework import serializers

from .models import Lecture


class LectureListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture
        fields = ('id', 'title', 'uploaded_by', 'created_at')
        read_only_fields = ('id', 'uploaded_by', 'created_at')


class LectureUploadSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(write_only=True)

    class Meta:
        model = Lecture
        fields = ('id', 'title', 'video_file', 'created_at')
        read_only_fields = ('id', 'created_at')
