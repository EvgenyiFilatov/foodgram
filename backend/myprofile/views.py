from api.paginators import CustomPageLimitPagination
from django.shortcuts import get_object_or_404
from myprofile.models import MyProfile, Subscription
from myprofile.serializers import (ChangePasswordSerializer,
                                   SubscriptionSerializer,
                                   UserCreateSerializer, UserSerializer)
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response


class UserListCreateView(generics.ListCreateAPIView):
    queryset = MyProfile.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = CustomPageLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        serializer.save()


class UserDetailView(generics.RetrieveAPIView):
    queryset = MyProfile.objects.all()
    serializer_class = UserSerializer


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserAvatarView(generics.UpdateAPIView):
    queryset = MyProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            avatar_url = user.avatar.url
            return Response(
                {"avatar": request.build_absolute_uri(avatar_url)},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.avatar.delete(save=False)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "Пароль успешно изменен."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageLimitPagination

    def get_queryset(self):
        """Возвращает все подписки пользователя."""
        user = self.request.user
        return Subscription.objects.filter(subscriber=user)


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def create(self, request, id=None):
        if request.user.id == id:
            return Response(
                {'detail': 'Невозможно подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscribe_to = get_object_or_404(MyProfile, pk=id)

        subscription, created = Subscription.objects.get_or_create(
            subscriber=request.user, subscribe_to=subscribe_to)

        if not created:
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(SubscriptionSerializer(
            subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, id=None):
        subscription = Subscription.objects.filter(
            subscriber=request.user,
            subscribe_to_id=get_object_or_404(MyProfile, pk=id)
        ).first()

        if not subscription:
            return Response(
                {'detail': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(
            {'detail': 'Подписка удалена.'},
            status=status.HTTP_204_NO_CONTENT
        )
