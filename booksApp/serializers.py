from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Author, Genre, Book, Review, Follow,
    Message, UserLibrary, Wishlist, Listing,
    BookRanking, Activity, Profile, Publisher
)


# - USERS

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(source='followers.count', read_only=True)
    following_count = serializers.IntegerField(source='following.count', read_only=True)
    avatar = serializers.URLField(source='profile.avatar', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'followers_count', 'following_count', 'avatar']


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


# - BOOKS DATA

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'bio']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description']

class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    genres = serializers.PrimaryKeyRelatedField(queryset=Genre.objects.all(), many=True)
    publisher_id = serializers.PrimaryKeyRelatedField(
        source="publisher",
        queryset=Publisher.objects.all(),
        write_only=True
    )

    publisher = PublisherSerializer(read_only=True)
    added_by = UserSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'authors', 'genres', 'description',
            'pages', 'isbn', 'publisher', 'publisher_id',
            'published_year', 'edition_type', 'cover_url',
            'added_by', 'average_rating'
        ]


# - REVIEWS

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Review
        fields = ['id', 'user', 'book', 'rating', 'content', 'created_at']


# - SOCIALS

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'is_read']


# - USER LIBRARY

class UserLibrarySerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = UserLibrary
        fields = ['id', 'book', 'added_at']


class WishlistSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'book', 'added_at']


# - OFFERS

class ListingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'user', 'book', 'listing_type', 'price',
            'description', 'is_active', 'created_at'
        ]


# - RANKING

class BookRankingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = BookRanking
        fields = ['book', 'score', 'last_updated']


class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'user', 'action', 'timestamp']
