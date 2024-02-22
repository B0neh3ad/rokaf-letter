from datetime import date
from api.models import Letter, LetterStatus
import rokaf_crawler
from requests.exceptions import HTTPError
from django.http import JsonResponse

class LetterService:
    @staticmethod
    def send_letter(letter: Letter):
        letter_pydantic = rokaf_crawler.models.Letter(senderZipcode=letter.senderZipcode,
                                                      senderAddr1=letter.senderAddr1,
                                                      senderAddr2=letter.senderAddr2,
                                                      senderName=letter.senderName,
                                                      relationship=letter.relationship,
                                                      title=letter.title,
                                                      contents=letter.contents,
                                                      password=letter.password)

        receiver = letter.receiver
        receiver_pydantic = rokaf_crawler.models.Trainee(name=receiver.name,
                                                         birthday=receiver.birthday.strftime('%Y%m%d'),
                                                         member_seq=receiver.member_seq,
                                                         agency_id=receiver.agency_id)

        try:
            rokaf_crawler.crawlers.LetterSender(receiver_pydantic, letter_pydantic).send_letter()
        except HTTPError as e:
            return JsonResponse({'error': str(e), 'status_code': e.response.status_code})

        letter.sent_date = date.today()
        letter.status = LetterStatus.SENDING.value
        letter.save()

        return JsonResponse(letter)


letterService = LetterService()