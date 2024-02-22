class CrawlerException(Exception):
    pass

class TraineeNotFoundException(CrawlerException):
    def __init__(self, message="존재하지 않는 훈련병/교육생입니다."):
        self.message = message
        super().__init__(self.message)

class WrongAccessException(CrawlerException):
    def __init__(self, message="인편 사이트에 접근이 거부되었습니다."):
        self.message = message
        super().__init__(self.message)

class LetterWritingPeriodException(CrawlerException):
    def __init__(self, message="인터넷 편지 작성 기간이 아닙니다."):
        self.message = message
        super().__init__(self.message)

class TraineeNotSearchedException(CrawlerException):
    def __init__(self, message="member_seq이 필요합니다. 훈련병/교육생 검색을 먼저 해주세요."):
        self.message = message
        super().__init__(self.message)

TRAINEE_NOT_FOUND = "교육생이 없습니다."
WRONG_ACCESS = "잘못된 접근입니다."
LETTER_WRITING_PERIOD = "인터넷 편지 작성 기간이 아닙니다."
