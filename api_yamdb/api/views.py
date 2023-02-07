from http import HTTPStatus

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title
from users.models import User
from .filters import TitlesFilter
from .pagination import UsersPagination
from .permissions import (IsAdmin, IsAdminModeratorAuthorOrReadOnly,
                          IsAdminUserOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          ConfirmationCodeSerializer, GenreSerializer,
                          JwtTokenSerializer, ReadOnlyTitleSerializer,
                          ReviewSerializer, TitleSerializer, UserSerializer)

EMAIL = 'admin@mail.com'


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_confirmation_code(request):
    if User.objects.filter(username=request.data.get('username'),
                           email=request.data.get('email')).exists():
        user = User.objects.get(username=request.data.get('username'),
                                email=request.data.get('email'))
        code = default_token_generator.make_token(user)
        send_mail('Confirmation code',
                  f'Confirmation code: {code}',
                  EMAIL,
                  [request.data.get('email')],
                  fail_silently=False)
        return Response(request.data, status=HTTPStatus.OK)
    serializer = ConfirmationCodeSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        if serializer.validated_data['username'] == 'me':
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        serializer.save()
        user = get_object_or_404(User,
                                 username=serializer.data.get('username'))
        code = default_token_generator.make_token(user)
        send_mail('Confirmation code',
                  f'Confirmation code: {code}',
                  EMAIL,
                  [serializer.data.get('email')],
                  fail_silently=False)
        return Response(serializer.data, status=HTTPStatus.OK)
    return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_jwt_token(request):
    serializer = JwtTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(User,
                             username=request.data.get('username'))
    confirmation_code = request.data.get('confirmation_code')
    if default_token_generator.check_token(user, confirmation_code):
        refresh = RefreshToken.for_user(user)
        context = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(context, status=HTTPStatus.OK)
    return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes((IsAuthenticated,))
def get_current_user(request):
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=HTTPStatus.OK)
    obj = User.objects.get(id=request.user.id)
    serializer = UserSerializer(obj,
                                data=request.data,
                                partial=True)
    if serializer.is_valid(raise_exception=True):
        if 'role' in serializer.validated_data:
            serializer.validated_data.pop('role')
            serializer.save()
            return Response(serializer.data)
        serializer.save()
        return Response(serializer.data)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    pagination_class = UsersPagination
    filter_backends = (filters.SearchFilter,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    search_fields = ('=username',)
    lookup_field = 'username'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(
        Avg('reviews__score')).order_by('name')
    serializer_class = TitleSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return ReadOnlyTitleSerializer
        return TitleSerializer


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet,):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet,):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAdminModeratorAuthorOrReadOnly)

    def get_queryset(self):
        title = get_object_or_404(Title,
                                  id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title,
                                  id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAdminModeratorAuthorOrReadOnly)

    def get_queryset(self):
        review = get_object_or_404(Review,
                                   id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review,
                                   id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)
