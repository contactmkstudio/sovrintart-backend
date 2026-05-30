from rest_framework import serializers
from .models import FAQ, NavigationLinks

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"

class NavigationLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationLinks
        fields = "__all__"        

class ContactEmailSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100 , required=True)
    email = serializers.EmailField(required=True)
    message = serializers.CharField(required=True)        