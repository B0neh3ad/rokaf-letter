from pydantic import BaseModel
from enum import Enum

class SiteInfo(BaseModel):
    cody_menu_seq: str
    site_id: str

class AgencyIndex(Enum):
    기본군사훈련단 = 0
    군수1학교 = 1
    군수2학교 = 2
    정보통신학교 = 3
    행정학교 = 4
    방공포병학교 = 5

agencies = [SiteInfo(cody_menu_seq="156893223", site_id="last2"),
            SiteInfo(cody_menu_seq="157620025", site_id="gisool2"),
            SiteInfo(cody_menu_seq="157615558", site_id="gunsu"),
            SiteInfo(cody_menu_seq="156894686", site_id="tong-new"),
            SiteInfo(cody_menu_seq="159014200", site_id="haengjeong"),
            SiteInfo(cody_menu_seq="158327574", site_id="bangpogyo")
            ]

class TraineeSearchResult(BaseModel):
    name: str
    birthday: str
    member_seq: str
    additional_info: dict


class Trainee(BaseModel):
    name: str
    birthday: str
    member_seq: str = ''
    agency_id: int = AgencyIndex.기본군사훈련단.value


class Letter(BaseModel):
    senderZipcode: str
    senderAddr1: str
    senderAddr2: str
    senderName: str
    relationship: str
    title: str
    contents: str
    password: str

    class Config:
        extra = "forbid"
