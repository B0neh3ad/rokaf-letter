from django.http import JsonResponse
from django.views.decorators.http import *

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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

@require_GET
@permission_classes([AllowAny, ])
def gpt_test(request) -> JsonResponse:
    """
    주어진 text prompt에 대하여
    gpt 3.5 model의 response를 출력합니다.
    """
    default_role = """
    대한민국 공군 훈련병들의 인터넷 편지를 책임지는 AI 인편지기
    """
    role = request.GET.get('role', default_role)

    default_prompt = """
    매일 고생하며 훈련받는 공군 훈련병들을 위한 편지를 적어줘!
    """
    prompt = request.GET.get('prompt', default_prompt)

    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    query = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role':'system', 'content': role},
            {'role':'user', 'content': prompt},
        ],
    )
    choices = query.choices
    print("candidate letters:", len(choices))
    response = choices[0].message.content

    return JsonResponse({'content': response})

@require_GET
@permission_classes([AllowAny, ])
def search_trainee(request):
    name = request.GET.get('name', None)
    birthday = request.GET.get('birthday', None)
    try:
        agency_id = request.GET.get('agency_id', None)
    except ValueError as e:
        return JsonResponse({'error': 'agency_id 값의 형식이 잘못되었습니다.'}, status=400)

    trainee_pydantic = rokaf_crawler.models.Trainee(name=name, birthday=birthday)
    if agency_id is not None:
        trainee_pydantic.agency_id = int(agency_id)

    try:
        search_result = rokaf_crawler.crawlers.TraineeSearcher(trainee_pydantic).search_trainee()
        return JsonResponse(search_result, safe=False)
    except TraineeNotFoundException as e:
        return JsonResponse({'error': str(e)})

class TraineeViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Trainee.objects.all()
    serializer_class = TraineeSerializer


# TODO: 내가 작성한 편지인 경우 바로 편지 수정/삭제/발송 등이 가능하도록 수정
class LetterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Letter.objects.all()
    serializer_class = LetterListSerializer

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