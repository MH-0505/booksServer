import mimetypes
import os
import uuid
import requests

from django.shortcuts import render

from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import (
    Author, Genre, Book, Review, Follow,
    Message, UserLibrary, Wishlist, Listing,
    BookRanking, Activity
)
from .serializers import (
    UserSerializer, AuthorSerializer, GenreSerializer, BookSerializer,
    ReviewSerializer, FollowSerializer, MessageSerializer,
    UserLibrarySerializer, WishlistSerializer, ListingSerializer,
    BookRankingSerializer, ActivitySerializer, RegisterSerializer, ProfileSerializer
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
    })


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    profile = request.user.profile

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name']


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_author(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    bio = request.data.get('bio', '')

    if not first_name or not last_name:
        return Response(
            {'error': 'Imię i nazwisko są wymagane.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Sprawdzenie, czy autor już istnieje
    existing = Author.objects.filter(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip()
    ).first()

    if existing:
        return Response(
            {'error': 'Autor już istnieje.', 'id': existing.id},
            status=status.HTTP_409_CONFLICT
        )

    author = Author.objects.create(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        bio=bio.strip()
    )

    serializer = AuthorSerializer(author)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().select_related('added_by').prefetch_related('authors', 'genres')
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'authors__last_name', 'genres__name']
    ordering_fields = ['title', 'published_year']

    def perform_create(self, serializer):
        cover_file = self.request.FILES.get('cover')
        cover_url = None

        if cover_file:
            SUPABASE_URL = os.getenv('SUPABASE_URL')
            SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'covers')
            SUPABASE_KEY = os.getenv('SUPABASE_KEY')

            filename = f"{uuid.uuid4()}_{cover_file.name}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"

            content_type, _ = mimetypes.guess_type(cover_file.name)
            if content_type is None:
                content_type = "application/octet-stream"  # fallback

            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": content_type,
            }

            response = requests.post(upload_url, headers=headers, data=cover_file.read())

            if response.status_code in (200, 201):
                cover_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
            else:
                raise Exception(f"Błąd uploadu do Supabase: {response.text}")

        serializer.save(added_by=self.request.user, cover_url=cover_url)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('user', 'book')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.select_related('follower', 'following')
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related('sender', 'receiver')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class UserLibraryViewSet(viewsets.ModelViewSet):
    queryset = UserLibrary.objects.all()
    serializer_class = UserLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.select_related('book', 'user')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['book__title', 'description']
    ordering_fields = ['created_at', 'price']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookRankingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BookRanking.objects.select_related('book')
    serializer_class = BookRankingSerializer
    ordering_fields = ['score']


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activity.objects.select_related('user')
    serializer_class = ActivitySerializer





@api_view(['POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def upload_cover(request):
    """
    Uploaduje obraz okładki do Supabase Storage
    """
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'Brak pliku'}, status=status.HTTP_400_BAD_REQUEST)

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_BUCKET = os.getenv('SUPABASE_COVERS_BUCKET', 'covers')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    filename = f"{uuid.uuid4()}_{file.name}"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"

    content_type, _ = mimetypes.guess_type(file.name)
    if content_type is None:
        content_type = "application/octet-stream"  # fallback

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": content_type,
    }

    response = requests.post(upload_url, headers=headers, data=file.read())

    if response.status_code not in (200, 201):
        return Response(
            {'error': 'Nie udało się wysłać pliku', 'details': response.text},
            status=response.status_code
        )

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"

    return Response({'url': public_url}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_avatar(request):
    """
    Uploaduje zdjęcie profilowe do Supabase Storage
    """
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'Brak pliku'}, status=status.HTTP_400_BAD_REQUEST)

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_BUCKET = os.getenv('SUPABASE_AVATAR_BUCKET', 'avatars')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    filename = f"{uuid.uuid4()}_{file.name}"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"

    content_type, _ = mimetypes.guess_type(file.name)
    if content_type is None:
        content_type = "application/octet-stream"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": content_type,
    }

    response = requests.post(upload_url, headers=headers, data=file.read())

    if response.status_code not in (200, 201):
        return Response(
            {
                'error': 'Nie udało się wysłać pliku',
                'details': response.text
            },
            status=response.status_code
        )

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"

    profile = request.user.profile
    profile.avatar = public_url
    profile.save()

    return Response({'avatar_url': public_url}, status=status.HTTP_201_CREATED)