from datetime import date
from api.models import Letter, LetterStatus
import rokaf_crawler

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

        rokaf_crawler.crawlers.LetterSender(receiver_pydantic, letter_pydantic).send_letter()

        letter.sent_date = date.today()
        letter.status = LetterStatus.SENDING.value
        letter.save()

        return letter


letterService = LetterService()