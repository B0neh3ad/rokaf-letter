from datetime import datetime, date
from rest_framework import serializers
from api.models import *

class GptPromptSerializer(serializers.Serializer):
    role = serializers.CharField(default="""
        대한민국 공군 훈련병들의 인터넷 편지를 책임지는 AI 인편지기
        """)
    query_text = serializers.CharField(default="""
        매일 고생하며 훈련받는 공군 훈련병들을 위한 편지를 적어줘!
        """)

class TraineeSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainee
        exclude = ['member_seq']

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        ret['birthday'] = ret['birthday'].strftime('%Y%m%d')
        return ret


# TODO: trainee 추가 시 user와의 관계 설정도 가능하도록 serializer, view 변경
class TraineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainee
        fields = '__all__'

    def create(self, validated_data):
        # 기존의 trainee를 즐겨찾기에 추가하기 위해서도 create가 호출될 수 있다.
        # 이러한 경우에 동일 trainee가 중복 생성되는 것을 막기 위해 get_or_create를 사용한다.
        instance, _ = Trainee.objects.get_or_create(**validated_data)
        return instance


class LetterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = ['id', 'title', 'contents', 'sender', 'status']


class LetterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = '__all__'
        read_only_fields = ['sender']

    def create(self, validated_data):
        # get sender and receiver
        sender = self.context['request'].user
        receiver = validated_data.get('receiver')

        # set relationship field
        try:
            relationship = TraineeToUser.objects.get(user=sender.id, trainee=receiver.id).relationship
            validated_data['relationship'] = relationship
        except TraineeToUser.DoesNotExist:
            raise AssertionError('내가 추가한 훈련병에게만 편지를 보낼 수 있습니다.')

        # set fields about sender
        sender_default_values = {'zipcode': '52364',
                          'addr1': '경상남도 진주시 금산면 송백로 46',
                          'addr2': '사서함',
                          'name': 'ㅇㅇ'}

        for field in sender_default_values.keys():
            curr_value = validated_data.get('sender' + field.title())
            sender_value = getattr(sender, field)
            default_value = sender_default_values.get(field)

            if curr_value == "":
                validated_data['sender' + field.title()] = sender_value if sender_value != "" else default_value


        status = validated_data.get('status')
        # set date none when editing
        if status == LetterStatus.EDITING.value:
            validated_data['sent_date'] = None
        # set date today when sending
        elif status == LetterStatus.SENDING.value:
            validated_data['sent_date'] = datetime.today()
        # validate reservation date
        elif status == LetterStatus.RESERVED.value:
            assert validated_data['sent_date'] > datetime.today(), (
                '예약 발송은 내일 이후의 날짜로만 가능합니다.'
            )

        validated_data['sender'] = sender
        instance = Letter.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        assert instance.status in [LetterStatus.EDITING.value, LetterStatus.RESERVED.value], (
            '이미 전송된 편지는 수정이 불가능합니다.'
        )

        # set date when status is changed to sending
        if validated_data.get('status') == LetterStatus.SENDING.value:
            validated_data['sent_date'] = date.today()
        # validate reservation date
        elif validated_data.get('status') == LetterStatus.RESERVED.value:
            assert validated_data['sent_date'] is not None, (
                '예약 발송 날짜를 입력해주세요.'
            )
            assert validated_data['sent_date'] > date.today(), (
                '예약 발송은 내일 이후의 날짜로만 가능합니다.'
            )

        instance = super().update(instance, validated_data)
        return instance
