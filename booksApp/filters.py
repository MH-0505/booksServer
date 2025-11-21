from django_filters import rest_framework as filters
from .models import Book

class BookFilter(filters.FilterSet):
    published_year__gte = filters.NumberFilter(field_name="published_year", lookup_expr="gte")
    published_year__lte = filters.NumberFilter(field_name="published_year", lookup_expr="lte")

    class Meta:
        model = Book
        fields = ['authors', 'genres', 'publisher', 'published_year__gte', 'published_year__lte']