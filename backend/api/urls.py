from django.urls import include, path, re_path
from myprofile.views import (ChangePasswordView, SubscriptionListView,
                             SubscriptionViewSet, UserAvatarView,
                             UserDetailView, UserListCreateView, UserMeView)
from recipes.views import (IngredientsViewSet, RecipesViewSet, TagsViewSet,
                           redirect_short_link)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'tags', TagsViewSet)
router.register(r'ingredients', IngredientsViewSet)
router.register(r'recipes', RecipesViewSet)

urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path(
        'users/set_password/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    path(
        'users/subscriptions/',
        SubscriptionListView.as_view(),
        name='subscription-list'
    ),
    path('users/<int:id>/subscribe/',
         SubscriptionViewSet.as_view(
             {'post': 'create', 'delete': 'destroy'}
         ),
         name='subscribe'),
    path(
        's/<str:short_link>/',
        redirect_short_link,
        name='redirect_short_link'
    ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
