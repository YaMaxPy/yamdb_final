from django.urls import include, path
from rest_framework import routers

from .views import (CategoryViewSet, CommentViewSet, GenreViewSet,
                    ReviewViewSet, TitleViewSet, UsersViewSet,
                    get_confirmation_code, get_current_user, get_jwt_token)

router = routers.DefaultRouter()
router.register(r'users', UsersViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'titles', TitleViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)

urlpatterns = [
    path('v1/users/me/', get_current_user, name='current_user'),
    path('v1/', include(router.urls)),
    path('v1/auth/signup/', get_confirmation_code, name='signup'),
    path('v1/auth/token/', get_jwt_token, name='get_token'),
]
