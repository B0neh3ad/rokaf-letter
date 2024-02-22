from django.contrib import auth
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from h11 import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from api.models import User
from accounts.serializers import RegisterSerializer


# Create your views here.
class SignUpView(CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # user 생성과 동시에 토큰 생성
        token = Token.objects.create(user=user)
        serializer.data['token'] = token.key

        headers = self.get_success_headers(serializer.data)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        user = auth.authenticate(**request.data)
        if user is not None:
            token = Token.objects.get(user=user)
            return JsonResponse({'token': token.key})
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

