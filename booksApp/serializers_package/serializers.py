from rest_framework import serializers
from django.contrib.auth.models import User
from booksApp.models import (
    Author, Genre, Book, Review, Follow,
    Message, UserLibrary, Wishlist, Listing,
    BookRanking, Activity, Profile, Publisher,
    Conversation, ExchangeOffer  # Dodajemy import Conversation
)
from booksApp.serializers_package.user_serializers import UserSerializer


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
        # write
        author_ids = serializers.PrimaryKeyRelatedField(
            source="authors",
            queryset=Author.objects.all(),
            many=True,
            write_only=True
        )
        genre_ids = serializers.PrimaryKeyRelatedField(
            source="genres",
            queryset=Genre.objects.all(),
            many=True,
            write_only=True
        )

        publisher_id = serializers.PrimaryKeyRelatedField(
            source="publisher",
            queryset=Publisher.objects.all(),
            write_only=True
        )

        # read
        authors = AuthorSerializer(many=True, read_only=True)
        genres = GenreSerializer(many=True, read_only=True)
        publisher = PublisherSerializer(read_only=True)
        added_by = UserSerializer(read_only=True)
        average_rating = serializers.FloatField(read_only=True)

        # Market data (annotated)
        lowest_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
        listings_count = serializers.IntegerField(read_only=True)

        class Meta:
            model = Book
            fields = [
                'id', 'title','authors', 'genres','author_ids', 'genre_ids', 'description',
                'pages', 'isbn', 'publisher', 'publisher_id', 'published_year', 'edition_type',
                'cover_url', 'added_by', 'average_rating', 'created_at', 'lowest_price', 'listings_count'
            ]


class BookCompactSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)
    average_rating = serializers.FloatField(read_only=True)

    lowest_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    listings_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "genres",
            "cover_url",
            "average_rating",
            "lowest_price",
            "listings_count"
        ]


# - REVIEWS

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Review
        fields = ['id', 'user', 'book', 'rating', 'content', 'created_at']


# - OFFERS

class ListingSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(source='book', queryset=Book.objects.all(), write_only=True)

    user = UserSerializer(read_only=True)
    book = BookCompactSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'user', 'book', 'listing_type', 'price',
            'description', 'is_active', 'created_at', 'book_id',
            'city', 'condition', 'allow_exchange'
        ]

class ExchangeOfferSerializer(serializers.ModelSerializer):
    user_a = UserSerializer(read_only=True)
    user_b = UserSerializer(read_only=True)
    book_a = BookCompactSerializer(read_only=True)
    books_b = BookCompactSerializer(many=True, read_only=True)
    chosen_book_b = BookCompactSerializer(read_only=True)

    # write
    user_a_id = serializers.PrimaryKeyRelatedField(source='user_a', queryset=User.objects.all(), write_only=True)
    book_a_id = serializers.PrimaryKeyRelatedField(source='book_a', queryset=Book.objects.all(), write_only=True)
    books_b_ids = serializers.PrimaryKeyRelatedField(
        source='books_b', queryset=Book.objects.all(), many=True, write_only=True
    )
    chosen_book_b_id = serializers.PrimaryKeyRelatedField(
        source='chosen_book_b', queryset=Book.objects.all(),
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ExchangeOffer
        fields = [
            'id',
            'user_a', 'user_a_id',
            'user_b',
            'book_a', 'book_a_id',
            'books_b', 'books_b_ids',
            'chosen_book_b', 'chosen_book_b_id',
            'accepted_a', 'accepted_b', 'rejected',
            'created_at'
        ]
        read_only_fields = ['accepted_a', 'accepted_b', 'rejected', 'created_at', 'user_b']


# - SOCIALS

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    # read
    book = BookCompactSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    exchange_offer = ExchangeOfferSerializer(read_only=True)

    # write
    book_id = serializers.PrimaryKeyRelatedField(
        source='book', queryset=Book.objects.all(), write_only=True, required=False, allow_null=True
    )
    listing_id = serializers.PrimaryKeyRelatedField(
        source='listing', queryset=Listing.objects.all(), write_only=True, required=False, allow_null=True
    )
    exchange_offer_id = serializers.PrimaryKeyRelatedField(
        source='exchange_offer', queryset=ExchangeOffer.objects.all(), write_only=True, required=False, allow_null=True
    )
    conversation_id = serializers.PrimaryKeyRelatedField(
        source='conversation', queryset=Conversation.objects.all(), write_only=True
    )

    class Meta:
        model = Message
        fields = [
            'id', 'conversation_id', 'sender', 'content', 
            'timestamp', 'is_read', 
            'book', 'book_id', 
            'listing', 'listing_id',
            'exchange_offer', 'exchange_offer_id'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        messages = list(obj.messages.all())
        if messages:
            return MessageSerializer(messages[-1]).data
        return None


# - USER LIBRARY

class UserLibrarySerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(source='book', queryset=Book.objects.all(), write_only=True)
    book = BookCompactSerializer(read_only=True)

    class Meta:
        model = UserLibrary
        fields = ['id', 'book', 'book_id', 'added_at']



class WishlistSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(source='book', queryset=Book.objects.all(), write_only=True)
    book = BookCompactSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'book', 'book_id', 'added_at']


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
