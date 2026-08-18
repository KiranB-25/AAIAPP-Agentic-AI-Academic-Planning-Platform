from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import User
from .permissions import IsAdministrator
from .serializers import LoginSerializer, LogoutSerializer, RegistrationSerializer, UserManagementSerializer, UserSerializer
from .services import authenticate_login, issue_tokens, logout_refresh_token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_login(request=request, **serializer.validated_data)
        return Response({**issue_tokens(user), "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logout_refresh_token(serializer.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        return Response(UserSerializer(User.objects.select_related("role").order_by("id"), many=True).data)


class UserManagementView(APIView):
    permission_classes = [IsAdministrator]

    def get_object(self, pk: int) -> User:
        return get_object_or_404(User, pk=pk)

    def patch(self, request, pk: int):
        user = self.get_object(pk)
        serializer = UserManagementSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(UserSerializer(serializer.save()).data)
