from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from booksApp import views
from booksApp.views import upload_cover, RegisterView, me, profile_view, upload_avatar, add_author

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
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', me, name='me'),
    path('profile/', profile_view, name='profile'),
    path('upload-avatar/', upload_avatar, name='upload-avatar'),
    path('upload-cover/', upload_cover, name='upload-cover'),
    path('authors/add', add_author, name='add-author'),
]