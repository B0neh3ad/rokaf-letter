import json
import uuid
from enum import Enum

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser
from rokaf_crawler.models import AgencyIndex

class LetterStatus(Enum):
    EDITING = 0
    RESERVED = 1
    SENDING = 2
    RECEIVED = 3

class IntEnumField(models.IntegerField):
    """
    django model field with Enum(integer type)
    https://vixxcode.tistory.com/249
    """
    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        super().__init__(*args, **kwargs)

    def get_default(self):
        default = super().get_default()
        self.validate_enum(default)
        return default

    def to_python(self, value):
        return super().to_python(self.validate_enum(value))

    def get_prep_value(self, value):
        return super().get_prep_value(self.validate_enum(value))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        return name, path, args, kwargs

    def validate_enum(self, value) -> int:
        for name, member in self.enum.__members__.items():
            if member == value:
                return value.value
            if member.value == value:
                return value
        raise AttributeError('Not Found Enum Member')


class Trainee(models.Model):
    name = models.CharField(max_length=20)
    birthday = models.DateField()
    member_seq = models.CharField(max_length=100)
    agency_id = IntEnumField(AgencyIndex, default=AgencyIndex.기본군사훈련단.value)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_trainee = models.BooleanField(default=False)
    as_trainee = models.OneToOneField(Trainee, null=True, on_delete=models.CASCADE, related_name="as_user")

    like_trainees = models.ManyToManyField(Trainee, through="TraineeToUser")

    zipcode = models.CharField(max_length=7)
    addr1 = models.CharField(max_length=200)
    addr2 = models.CharField(max_length=200)
    name = models.CharField(max_length=20)

    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Letter(models.Model):
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sent_letters')
    receiver = models.ForeignKey(Trainee, on_delete=models.PROTECT, related_name='received_letters')

    senderZipcode = models.CharField(max_length=7, blank=True)
    senderAddr1 = models.CharField(max_length=200, blank=True)
    senderAddr2 = models.CharField(max_length=200, blank=True)
    senderName = models.CharField(max_length=100, blank=True)
    relationship = models.CharField(max_length=100, blank=True)

    title = models.CharField(max_length=100)
    contents = models.TextField()
    password = models.CharField(max_length=100)

    sent_date = models.DateField(null=True)
    status = IntEnumField(enum=LetterStatus, default=LetterStatus.EDITING.value)

    def __str__(self):
        return self.title


class TraineeToUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.trainee.name + " TO " + self.user.email
