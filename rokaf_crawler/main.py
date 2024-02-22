from crawlers import *
import requests
from urllib import parse
from models import *

test_trainee = Trainee(
    name = '김진수',
    birthday = '20020801',
    agency_id = AgencyIndex.정보통신학교.value
)

letter = Letter(
    senderZipcode = "52364",
    senderAddr1 = "경상남도 진주시 금산면 송백로 46",
    senderAddr2 = "사서함",
    senderName = "test",
    relationship = "test",
    title = "제목입니다",
    contents = "반갑습니다",
    password = "반갑습니다"
)

searched_trainee = TraineeSearcher(test_trainee).search_trainee()
