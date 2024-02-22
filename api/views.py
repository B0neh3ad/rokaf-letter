from django.http import JsonResponse
from django.views.decorators.http import *

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

import rokaf_crawler
from rokaf_crawler.exceptions import *
from .serializers import *
from .services import *

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(verbose=True)

"""
    trainee: CRUD 모두 구현(create, read, update, delete, retrieve) (O)
    + GET trainees/search?name={name}&birthday={birthday}: 훈련병 목록 조회 (O)
    
    letter: CRUD 모두 구현(마찬가지. 단, list와 detail의 seriallizer 다름) (O)
    + GET letters/received: (trainee 회원 한정) 받은 인편 조회 (테스트 필요)
    
    + GET trainees/{trainee_id}/letters: 특정 trainee의 인편 목록 조회 (구현 중)
    
    + POST letters/{letter_id}: 단순 수정 완료인건지, 전송인건지, 예약인건지 구분해야 됨 (테스트 필요)
    
"""

class GptTest(APIView):
    permission_classes = [AllowAny]
    serializer_class = GptPromptSerializer
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = self.client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': serializer.validated_data['role']},
                {'role': 'user', 'content': serializer.validated_data['query_text']},
            ],
        )
        choices = query.choices
        for i, choice in enumerate(choices):
            print(f"choice #{i}")
            print(choice.message.content)
        response = choices[0].message.content

        return Response({'content': response})


class TraineeSearchView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TraineeSearchSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        trainee_pydantic = rokaf_crawler.models.Trainee(**serializer.validated_data)

        try:
            search_result = rokaf_crawler.crawlers.TraineeSearcher(trainee_pydantic).search_trainee()
            return Response(search_result)
        except TraineeNotFoundException as e:
            return Response({'error': str(e)})


class TraineeViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TraineeSerializer

    def get_queryset(self):
        return self.request.user.like_trainees.all()

    # TODO: trainee 추가 시 user와의 관계 설정도 가능하도록 serializer, view 변경
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        try:
            trainee = serializer.save()
        except AssertionError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # create relationship
        TraineeToUser.objects.create(user = request.user,
                                     trainee = trainee)

        headers = self.get_success_headers(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# TODO: 내가 작성한 편지인 경우 바로 편지 수정/삭제/발송 등이 가능하도록 수정
class LetterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LetterListSerializer

    def get_queryset(self):
        return Letter.objects.filter(sender = self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return LetterListSerializer
        return LetterDetailSerializer

    @action(detail=False, methods=['get'], url_path='sent')
    def get_my_letters(self, request, *args, **kwargs):
        """
        (특정 trainee에게) 보낸 편지 조회
        """
        user = request.user
        queryset = Letter.objects.filter(sender=user)

        receiver_id = request.GET.get('receiver_id', None)
        if receiver_id is not None:
            queryset = queryset.filter(receiver=receiver_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='received')
    def get_received_letters(self, request, *args, **kwargs) -> Response:
        """
        (trainee user의 경우) 받은 편지 조회
        """
        user = self.request.user
        assert user.is_trainee, (
            '현재 사용자는 훈련병이 아닙니다.'
        )

        queryset = Letter.objects.filter(receiver=user.as_trainee.id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path=r'(?P<letter_id>\d+)/send')
    def send(self, request, *args, **kwargs) -> JsonResponse:
        """
        편지를 보냅니다
        """
        letter = Letter.objects.get(pk=self.kwargs['letter_id'])
        return letterService.send_letter(letter)