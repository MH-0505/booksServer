from django.urls import path, include
from rest_framework.routers import DefaultRouter
from booksApp import views
from booksApp.views import upload_cover

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'genres', views.GenreViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'follows', views.FollowViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'library', views.UserLibraryViewSet)
router.register(r'wishlist', views.WishlistViewSet)
router.register(r'listings', views.ListingViewSet)
router.register(r'rankings', views.BookRankingViewSet)
router.register(r'activities', views.ActivityViewSet)


urlpatterns = [
    path('', include(router.urls)),

    path('upload-cover/', upload_cover, name='upload-cover'),
]