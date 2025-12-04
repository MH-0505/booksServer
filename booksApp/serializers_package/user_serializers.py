from django.contrib.auth.models import User
from rest_framework import serializers

from booksApp.models import Profile, UserLibrary


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    avatar = serializers.URLField(source='profile.avatar', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'followers_count', 'following_count', 'avatar', 'bio']


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'avatar', 'bio']