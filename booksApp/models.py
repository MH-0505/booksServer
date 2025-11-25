from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# - MAIN MODELS

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profil: {self.user.username}"


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    HARDCOVER = 'hardcover'
    PAPERBACK = 'paperback'
    ALBUM = 'album'
    AUDIO_CD = 'audio_cd'
    AUDIO_ONLINE = 'audio_online'
    EBOOK_PDF = 'ebook_pdf'
    EBOOK_EPUB = 'ebook_epub'

    EDITION_TYPES = [
        (HARDCOVER, 'Książka drukowana w oprawie twardej'),
        (PAPERBACK, 'Książka drukowana w oprawie broszurowej'),
        (ALBUM, 'Książka drukowana w wersji albumowej'),
        (AUDIO_CD, 'Audiobook na płycie CD-ROM (mp3)'),
        (AUDIO_ONLINE, 'Audiobook on-line (mp3)'),
        (EBOOK_PDF, 'Książka sprzedawana on-line w postaci .pdf'),
        (EBOOK_EPUB, 'Książka sprzedawana on-line w postaci .epub'),
    ]

    title = models.CharField(max_length=200)
    authors = models.ManyToManyField('Author', related_name='books')
    genres = models.ManyToManyField('Genre', related_name='books')
    description = models.TextField(blank=True, null=True)
    pages = models.PositiveIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=13, unique=True)
    publisher = models.ForeignKey('Publisher', on_delete=models.SET_NULL, null=True, related_name='books')
    published_year = models.PositiveIntegerField(blank=True, null=True)
    edition_type = models.CharField(
        max_length=20,
        choices=EDITION_TYPES,
        default=HARDCOVER,
        verbose_name='Typ wydania'
    )
    cover_url = models.URLField(blank=True, null=True)
    added_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='added_books')
    created_at = models.DateTimeField(auto_now_add=True)
    average_rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.title} ({self.get_edition_type_display()})"


# --- SOCIAL MODELS

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=0)    # 1-5
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user} for {self.book}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower} → {self.following}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.receiver}"


# --- USER LIBRARY MODELS

class UserLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='owned_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')


# --- LISTING MODELS

class Listing(models.Model):
    SALE = 'sale'
    EXCHANGE = 'exchange'
    USED = 'used'
    NEW = 'new'
    LISTING_TYPES = [
        (SALE, 'Sprzedaż'),
        (EXCHANGE, 'Wymiana'),
    ]
    CONDITION_TYPES = [
        (USED, 'Używana'),
        (NEW, 'Nowa'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, default=SALE)
    condition = models.CharField(max_length=10, choices=CONDITION_TYPES, default=NEW)
    city = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book.title} ({self.listing_type}) by {self.user.username}"


# --- ADDITIONAL MODELS

class BookRanking(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='ranking')
    score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} - {self.score}"


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}: {self.action}"

