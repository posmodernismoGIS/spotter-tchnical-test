from rest_framework import serializers

class RouteQuerySerializer(serializers.Serializer):
    start = serializers.CharField(max_length=120, help_text="'City, ST' or 'lat,lon'")
    finish = serializers.CharField(max_length=120, help_text="'City, ST' or 'lat,lon'")