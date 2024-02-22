from django.contrib.auth import password_validation
from rest_framework import serializers, validators
from api.models import User

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[password_validation.validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )
    token = serializers.CharField(
        read_only=True,
    )

    name = serializers.CharField(required=False, allow_blank=True)
    zipcode = serializers.CharField(required=False, allow_blank=True)
    addr1 = serializers.CharField(required=False, allow_blank=True)
    addr2 = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "email", "password", "password2", # 필수 입력 정보
            "is_trainee", # 회원 유형 분류(일반/훈련병)
            "name", "zipcode", "addr1", "addr2", # 편지 연동 정보
            "token",
        ]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password": "비밀번호가 일치하지 않습니다."}
            )
        return data

    def create(self, validated_data):
        print(validated_data)
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user
