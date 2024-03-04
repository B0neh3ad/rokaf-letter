import re
from dataclasses import dataclass
from enum import Enum
from typing import List
from urllib import parse

import bs4
import requests
from bs4 import BeautifulSoup
from rokaf_crawler.exceptions import *
from rokaf_crawler.models import *

# 1. 정보 불러오기
class TraineeSearcher:
    def __init__(self, trainee: Trainee):
        self.trainee = trainee
        self.agency = agencies[self.trainee.agency_id]

    @staticmethod
    def get_soup(url: str) -> BeautifulSoup:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    @staticmethod
    def parse_member_seq(trainee_tag: bs4.element.Tag) -> str:
        onclick_func = trainee_tag.input['onclick']
        int_pattern = re.compile('\d+')
        member_seq = int_pattern.findall(onclick_func)[0]
        return member_seq

    @staticmethod
    def parse_additional_info(trainee_tag: bs4.element.Tag) -> dict:
        additional_info = {}
        info_dl_list = trainee_tag.find(class_='info').select('dl')
        for info_dl in info_dl_list:
            key = " ".join(info_dl.dt.text.split())
            value = " ".join(info_dl.dd.text.split()[1:])
            additional_info[key] = value
        return additional_info

    def get_trainee_list_url(self) -> str:
        return f"http://airforce.mil.kr:8081/user/emailPicViewSameMembers.action?" \
               f"siteId={self.agency.site_id}" \
               f"&searchName={self.trainee.name}&searchBirth={self.trainee.birthday}"

    def search_trainee(self) -> List:
        url = self.get_trainee_list_url()
        soup = self.get_soup(url)

        if "잘못된 접근입니다." in soup.text:
            raise WrongAccessException()
        elif "교육생이 없습니다." in soup.text:
            raise TraineeNotFoundException()

        trainee_tags = soup.body.select('li')
        search_result = []
        for trainee_tag in trainee_tags:
            member_seq = self.parse_member_seq(trainee_tag)
            additional_info = self.parse_additional_info(trainee_tag)
            searched_trainee = TraineeSearchResult(name = self.trainee.name, birthday = self.trainee.birthday,
                                                   member_seq = member_seq, additional_info = additional_info)
            search_result.append(searched_trainee.dict())

        # DEBUG CODE
        print(f"{AgencyIndex(self.trainee.agency_id).name} {self.trainee.name} 훈련병(교육생)이 확인되었습니다")
        print(f"검색 결과: {len(search_result)}명")
        print(search_result)
        return search_result

# 2. 편지 보내기
## 편지 목록 페이지 접속
class LetterListPageGetter:
    def __init__(self, trainee: Trainee):
        self.trainee = trainee
        self.agency = agencies[self.trainee.agency_id]

    def get_letter_list_page_url(self) -> str:
        return f"http://www.airforce.mil.kr:8081/user/indexSub.action?" \
              f"codyMenuSeq={self.agency.cody_menu_seq}" \
              f"&siteId={self.agency.site_id}" \
              f"&menuUIType=sub&dum=dum&command2=getEmailList" \
              f"&searchName={parse.quote(self.trainee.name)}" \
              f"&searchBirth={self.trainee.birthday}" \
              f"&memberSeq={self.trainee.member_seq}"

    def get_letter_list_page(self) -> requests.Response:
        if not self.trainee.member_seq:
            raise TraineeNotSearchedException()

        url = self.get_letter_list_page_url()
        response = requests.get(url)
        response.raise_for_status()

        # DEBUG CODE
        print("인편 목록 페이지에 접속했습니다.\n url:", url)

        if "잘못된 접근입니다." in response.text:
            raise WrongAccessException()
        elif "인터넷 편지 작성 기간이 아닙니다." in response.text:
            raise LetterWritingPeriodException()

        return response

## 편지 작성 후 전송
class LetterSender:
    def __init__(self, trainee: Trainee, letter: Letter) -> None:
        self.trainee = trainee
        self.agency = agencies[self.trainee.agency_id]
        self.letter = letter

    def create_request_form_data(self) -> dict:
        return {
            "siteId": agencies[self.trainee.agency_id].site_id,
            "command2": "writeEmail",
            "memberSeqVal": self.trainee.member_seq,
            **self.letter.dict(),
        }

    def get_letter_write_page_url(self) -> str:
        return f"http://www.airforce.mil.kr:8081/user/indexSub.action?" \
               f"codyMenuSeq={self.agency.cody_menu_seq}&siteId={self.agency.site_id}" \
               f"&menuUIType=sub&dum=dum&command2=writeEmail&searchCate=&searchVal=&page=1"

    def get_letter_write_page(self, letter_list_page_url: str, prev_response: requests.Response,
                              session: requests.Session) -> requests.Response :
        additional_headers = {
            "Referer": letter_list_page_url
        }
        letter_write_page_url = self.get_letter_write_page_url()
        letter_write_page_response = session.get(letter_write_page_url, cookies=prev_response.cookies,
                                                 headers=additional_headers)
        letter_write_page_response.raise_for_status()

        # DEBUG CODE
        print("인편 작성 페이지에 접속했습니다.\n url:", letter_write_page_url)
        print("response:", letter_write_page_response)
        return letter_write_page_response

    def submit_letter(self, data, prev_response: requests.Response,
                      session: requests.Session) -> None:
        additional_headers = {
            "Referer": self.get_letter_write_page_url()
        }
        letter_submit_page_url = "http://www.airforce.mil.kr:8081/user/emailPicSaveEmail.action"
        letter_submit_page_response = session.post(letter_submit_page_url, cookies=prev_response.cookies, data=data,
                                                   headers=additional_headers)
        letter_submit_page_response.raise_for_status()

        # DEBUG CODE
        print("인편을 성공적으로 전송했습니다.")
        print("[request]")
        print("url:", letter_submit_page_url)
        print("cookies:", prev_response.cookies)
        print("data:", data)
        print("headers:", additional_headers)

        print("response:", letter_submit_page_response)

    def send_letter(self) -> None:
        letter_list_page_getter = LetterListPageGetter(self.trainee)
        with requests.Session() as s:
            # 편지 목록 페이지 접속
            letter_list_page_url = letter_list_page_getter.get_letter_list_page_url()
            letter_list_page_response = letter_list_page_getter.get_letter_list_page()

            # 편지 작성 페이지 접속
            letter_write_page_response = self.get_letter_write_page(letter_list_page_url,
                                                               prev_response = letter_list_page_response,
                                                               session = s)
            # 편지 request form에 맞게 구성
            http_request_body = self.create_request_form_data()
            # 편지 전송
            self.submit_letter(http_request_body, letter_write_page_response, session=s)

