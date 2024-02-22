from django.contrib import auth
from django.db.utils import IntegrityError
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from api.models import User
from accounts.serializers import RegisterSerializer, LoginSerializer
from rokafLetter import settings


class SignUpView(CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        headers = self.get_success_headers(serializer.data)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = auth.authenticate(**serializer.validated_data)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': token.key})
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        # 한 장치에서 로그아웃 시 다같이 로그아웃 됨
        # TODO: 장치별 로그인/로그아웃 구현
        request.user.auth_token.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

