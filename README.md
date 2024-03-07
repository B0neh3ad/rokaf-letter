# rokaf-letter
공군 친구들에게 편지쓰기
백엔드 서버입니다.
- Backend: Django
- Crawler: requests + beautifulsoap(bs4)

## Structure
- Django apps
  - accounts: 계정 관리 관련 api(회원가입, 로그인/로그아웃 등)
  - api: 백엔드 서버 api
- rokaf_crawler: 공군 인편 페이지와 상호작용(훈련병 정보 불러오기, 편지 전송 등)
