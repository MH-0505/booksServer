import mimetypes
import os
import uuid
import requests

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Min, Q, Prefetch

from .filters import BookFilter
from .models import (
    Author, Genre, Book, Review, Follow,
    Message, UserLibrary, Wishlist, Listing,
    BookRanking, Activity, Publisher,
    Conversation, ExchangeOffer  # Import Conversation
)
from booksApp.serializers_package.serializers import (
    UserSerializer, AuthorSerializer, GenreSerializer, BookSerializer,
    ReviewSerializer, FollowSerializer, MessageSerializer,
    UserLibrarySerializer, WishlistSerializer, ListingSerializer,
    BookRankingSerializer, ActivitySerializer,
    PublisherSerializer, BookCompactSerializer,
    ConversationSerializer, ExchangeOfferSerializer  # Import ConversationSerializer
)
from .serializers_package.user_serializers import RegisterSerializer, ProfileSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related('profile').annotate(
        followers_count=Count('followers', distinct=True),
        following_count=Count('following', distinct=True)
    )
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']


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
        "avatar": user.profile.avatar
    })

def upload_avatar_to_supabase(user_id, avatar_file):
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_bucket = os.getenv('SUPABASE_BUCKET', 'avatars')
    supabase_key = os.getenv('SUPABASE_KEY')

    filename = f"{user_id}_{uuid.uuid4()}_{avatar_file.name}"
    upload_url = f"{supabase_url}/storage/v1/object/{supabase_bucket}/{filename}"

    content_type, _ = mimetypes.guess_type(avatar_file.name)
    if content_type is None:
        content_type = "application/octet-stream"

    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": content_type,
    }

    response = requests.post(upload_url, headers=headers, data=avatar_file.read())

    if response.status_code in (200, 201):
        return f"{supabase_url}/storage/v1/object/public/{supabase_bucket}/{filename}"
    else:
        raise Exception(f"Błąd uploadu do Supabase: {response.text}")


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
            avatar_file = request.FILES.get('avatarFile')
            save_kwargs = {}

            if avatar_file:
                try:
                    avatar_url = upload_avatar_to_supabase(request.user.id, avatar_file)
                    save_kwargs['avatar'] = avatar_url
                except Exception as e:
                    return Response({'detail': str(e)}, status=400)

            serializer.save(**save_kwargs)
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
    last_name = request.data.get('last_name', '')
    bio = request.data.get('bio', '')

    if not first_name:
        return Response(
            {'error': 'Imię jest wymagane.'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().select_related('added_by').prefetch_related('authors', 'genres')
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'authors__last_name']
    ordering_fields = ['title', 'published_year', 'average_rating', 'created_at', 'lowest_price']
    ordering = ['-created_at']
    filterset_class = BookFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(
            lowest_price=Min('listings__price', filter=Q(listings__is_active=True)),
            listings_count=Count('listings', filter=Q(listings__is_active=True))
        )

    def perform_create(self, serializer):
        cover_file = self.request.FILES.get('coverFile')
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

    @action(methods=['get'], detail=False)
    def compact(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = BookCompactSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def in_library(self, request, pk=None):
        user = request.user
        book = self.get_object()

        exists = UserLibrary.objects.filter(user=user, book=book).exists()
        return Response({"in_library": exists})

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def in_wishlist(self, request, pk=None):
        user = request.user
        book = self.get_object()

        exists = Wishlist.objects.filter(user=user, book=book).exists()
        return Response({"in_wishlist": exists})


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('user', 'book')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'book']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.select_related('follower', 'following')
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('messages')

    def create(self, request, *args, **kwargs):
        target_user_id = request.data.get('target_user_id')
        
        if not target_user_id:
            return Response({'error': 'target_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        me = request.user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Sprawdzamy czy istnieje rozmowa zawierająca DOKŁADNIE tych dwóch uczestników
        existing_conversation = Conversation.objects.filter(participants=me).filter(participants=target_user).first()

        if existing_conversation:
            return Response(self.get_serializer(existing_conversation).data)

        # Jeśli nie istnieje, tworzymy nową
        conversation = Conversation.objects.create()
        conversation.participants.add(me, target_user)
        
        return Response(self.get_serializer(conversation).data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Pozwala filtrować wiadomości po ID rozmowy: /api/messages/?conversation=5
        queryset = Message.objects.filter(conversation__participants=self.request.user)
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=self.request.user)
        conversation = serializer.validated_data['conversation']
        conversation.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()

        if message.sender == request.user:
            return Response(
                {'error': 'Użytkownik nie może oznaczyć własnej wiadomości jako przeczytanej.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message.is_read = True
        message.save()
        return Response({'status': 'marked as read', 'is_read': True})


class UserLibraryViewSet(viewsets.ModelViewSet):
    queryset = UserLibrary.objects.all()
    serializer_class = UserLibrarySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user_id = self.request.query_params.get('user')
        if user_id and self.request.method in permissions.SAFE_METHODS:
            return self.queryset.filter(user=user_id)

        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        books_queryset = Book.objects.annotate(
            lowest_price=Min('listings__price', filter=Q(listings__is_active=True)),
            listings_count=Count('listings', filter=Q(listings__is_active=True))
        )
        return self.queryset.filter(user=self.request.user).prefetch_related(
            Prefetch('book', queryset=books_queryset)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.select_related('book', 'user')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['book__title', 'description']
    filterset_fields = ['book', 'user', 'listing_type', 'city']
    ordering_fields = ['created_at', 'price']
    ordering = ['price']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExchangeOfferViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExchangeOffer.objects.filter(
            Q(user_a=self.request.user) | Q(user_b=self.request.user)
        ).select_related('user_a', 'user_b', 'book_a', 'chosen_book_b').prefetch_related('books_b')

    def perform_create(self, serializer):
        exchange_offer = serializer.save(user_b=self.request.user)

        user_a = exchange_offer.user_a
        user_b = exchange_offer.user_b

        conversation = Conversation.objects.filter(participants=user_a).filter(participants=user_b).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(user_a, user_b)

        Message.objects.create(
            conversation=conversation,
            sender=self.request.user,
            content="oferta wymiany",
            exchange_offer=exchange_offer
        )

    @action(detail=True, methods=['post'])
    def choose_book(self, request, pk=None):
        """
        User A wybiera książkę z listy proponowanej przez Usera B i wstępnie akceptuje ofertę.
        """
        offer = self.get_object()

        if request.user != offer.user_a:
            return Response({'error': 'Tylko właściciel oferty (User A) może wybrać książkę.'},
                            status=status.HTTP_403_FORBIDDEN)

        if offer.rejected:
            return Response({'error': 'Ta oferta została już odrzucona.'}, status=status.HTTP_400_BAD_REQUEST)

        chosen_book_id = request.data.get('book_id')
        if not chosen_book_id:
            return Response({'error': 'Wymagane podanie book_id.'}, status=status.HTTP_400_BAD_REQUEST)

        if not offer.books_b.filter(id=chosen_book_id).exists():
            return Response({'error': 'Wybrana książka nie znajduje się w ofercie.'},
                            status=status.HTTP_400_BAD_REQUEST)

        chosen_book = Book.objects.get(id=chosen_book_id)
        offer.chosen_book_b = chosen_book
        offer.accepted_a = True
        offer.save()

        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        User B widzi, że A wybrał książkę i ostatecznie potwierdza wymianę.
        """
        offer = self.get_object()

        if request.user != offer.user_b:
            return Response({'error': 'Tylko inicjator wymiany (User B) może ostatecznie potwierdzić.'},
                            status=status.HTTP_403_FORBIDDEN)

        if not offer.accepted_a or not offer.chosen_book_b:
            return Response({'error': 'User A jeszcze nie zaakceptował oferty lub nie wybrał książki.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if offer.rejected:
            return Response({'error': 'Oferta została odrzucona.'}, status=status.HTTP_400_BAD_REQUEST)

        offer.accepted_b = True
        offer.save()

        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Odrzucenie oferty przez którąkolwiek ze stron.
        """
        offer = self.get_object()

        if request.user not in [offer.user_a, offer.user_b]:
            return Response({'error': 'Brak uprawnień do tej oferty.'}, status=status.HTTP_403_FORBIDDEN)

        offer.rejected = True
        offer.save()
        return Response(self.get_serializer(offer).data)


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

