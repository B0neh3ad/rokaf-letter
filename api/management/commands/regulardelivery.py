from django.core.management.base import BaseCommand, CommandError
from api.models import Letter, LetterStatus
from api.services import *

class Command(BaseCommand):

    def handle(self, *args, **options):
        reserved_letters = Letter.objects.filter(status=LetterStatus.RESERVED.value)
        self.stdout.write(
            self.style.SUCCESS(f'loaded all reserved letters - counts: {reserved_letters.count()}')
        )
        for letter in reserved_letters:
            print(f'인편 제목: {letter}\n전송을 시작합니다.')
            letterService.send_letter(letter)
