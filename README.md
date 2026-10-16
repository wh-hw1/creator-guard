# 🛡️ 크리에이터 권리 지킴이 (프로토타입 v0.1)

청년 크리에이터를 위한 AI 기반 권리 보호 서비스의 첫 번째 웹 프로토타입입니다.
유튜브 영상의 댓글을 분석해 악성 댓글과 저작권 침해 제보를 찾아내고 대응 방법을 안내합니다.

> 이번 버전은 **화면과 사용자 흐름 확인용**입니다.
> 실제 YouTube API·LLM API는 연결하지 않았고, 가상 댓글 3개와 미리 준비된 분석 결과를 사용합니다.

## 주요 기능

1. 서비스 소개 화면
2. 유튜브 영상 URL 입력 (주소 형식 확인)
3. 댓글 분석 시작 버튼
4. 테스트용 가상 댓글 3개 표시
5. 댓글 선택 시 상세 분석 결과 표시 (위험도, 유형, 요약, 판단 근거, 권장 대응)

## 파일 구성

| 파일 | 설명 |
| --- | --- |
| `app.py` | 화면(UI)과 사용자 흐름 |
| `mock_data.py` | 가상 댓글·분석 결과 데이터. 나중에 실제 API로 교체할 부분 |
| `requirements.txt` | 실행에 필요한 라이브러리 목록 |
| `.gitignore` | GitHub에 올리지 않을 파일 목록 (API 키 파일 등) |

## 실행 방법

### 방법 A. 내 컴퓨터 없이 웹에서 실행 (Streamlit Community Cloud, 추천)

1. 이 파일들을 GitHub 저장소에 올립니다.
2. <https://share.streamlit.io> 에 GitHub 계정으로 로그인합니다.
3. **Create app** → 저장소와 브랜치를 고르고, Main file path에 `app.py`를 입력합니다.
4. **Deploy**를 누르면 몇 분 뒤 웹 주소가 생성됩니다.

### 방법 B. 컴퓨터에서 실행 (Python 3.10 이상 필요)

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 <http://localhost:8501> 이 자동으로 열립니다.

## 사용 방법

1. 유튜브 영상 주소(예: `https://www.youtube.com/watch?v=abc123`)를 입력합니다.
2. **댓글 분석 시작**을 누르면 가상 댓글 3개가 나타납니다.
3. 댓글 아래 **이 댓글 분석하기**를 누르면 상세 분석 결과가 표시됩니다.

## 다음 단계 (예정)

- YouTube Data API로 실제 댓글 불러오기 → `mock_data.py`의 `get_comments()` 교체
- LLM API로 댓글 분석하기 → `mock_data.py`의 `analyze_comment()` 교체
- API 키는 코드에 직접 쓰지 말고 Streamlit의 **Secrets** 기능에 저장

※ 분석 결과는 참고용이며 법률 자문이 아닙니다.
