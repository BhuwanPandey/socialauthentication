import os
from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email','image', 'bio']
    
    def get_image(self, user):
        main_url = os.getenv("MAIN_URL")
        return main_url + user.profile.avatar.url
    
    def get_bio(self, user):
        return user.profile.bio

class JWTSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
