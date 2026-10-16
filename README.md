# 🛡️ 크리에이터 권리 지킴이 (프로토타입 v0.2)

청년 크리에이터를 위한 AI 기반 권리 보호 서비스의 웹 프로토타입입니다.
유튜브 영상의 댓글을 분석해 악성 댓글과 저작권 침해 제보를 찾아내고 대응 방법을 안내하는 것이 목표입니다.

> **v0.2:** YouTube Data API v3를 연결해 실제 공개 댓글을 불러옵니다.
> AI 분석 기능은 아직 없으며 다음 버전에서 추가할 예정입니다.

## 주요 기능

1. 서비스 소개 화면
2. 유튜브 영상 URL 입력
   - 지원 형식: `youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...`
3. **댓글 분석 시작** 버튼을 누르면 최상위 공개 댓글을 최대 50개 불러옵니다.
4. 댓글 목록에 작성자, 작성 시각(한국 시간), 내용을 표시합니다.
5. 댓글을 선택하면 작성자, 작성 시각, 댓글 ID 등 상세 정보를 표시합니다.

다음 경우에는 안내 메시지를 표시합니다.
- 잘못된 URL
- 댓글이 비활성화된 영상
- 존재하지 않거나 비공개인 영상
- API 키 없음, 잘못된 API 키, 하루 요청량 초과

## 파일 구성

| 파일 | 설명 |
| --- | --- |
| `app.py` | 화면(UI)과 사용자 흐름 |
| `youtube.py` | URL에서 영상 ID를 추출하고, YouTube API로 댓글을 가져옴 |
| `requirements.txt` | 실행에 필요한 라이브러리 목록 |
| `.streamlit/secrets.toml.example` | API 키 설정 파일 예시 (실제 키는 넣지 않음) |
| `.gitignore` | GitHub에 올리지 않을 파일 목록 (실제 키가 든 `secrets.toml` 포함) |

## 1. YouTube API 키 발급받기

1. <https://console.cloud.google.com> 에 Google 계정으로 로그인합니다.
2. 위쪽 프로젝트 선택 메뉴에서 **새 프로젝트**를 만듭니다. (예: `creator-guard`)
3. **API 및 서비스 → 라이브러리**에서 `YouTube Data API v3`를 검색하고 **사용**을 누릅니다.
4. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → API 키**를 누르면 키가 만들어집니다.
5. (권장) 생성된 키의 **API 제한사항**에서 `YouTube Data API v3`만 허용하도록 설정합니다.

> ⚠️ API 키는 비밀번호와 같습니다. 코드, README, GitHub 이슈 등 어디에도 직접 붙여넣지 마세요.

## 2. API 키 등록하기

### Streamlit Community Cloud에 배포한 경우 (추천)

1. <https://share.streamlit.io> 에서 내 앱 오른쪽의 **⋮ → Settings → Secrets**로 들어갑니다.
2. 아래처럼 입력하고 **Save**를 누릅니다.

   ```toml
   YOUTUBE_API_KEY = "발급받은_API_키"
   ```

3. 앱이 자동으로 다시 시작되며, 1분 정도 지나면 적용됩니다.

### 내 컴퓨터에서 실행하는 경우

1. `.streamlit/secrets.toml.example` 파일을 복사해 같은 폴더에 `secrets.toml`로 저장합니다.
2. `secrets.toml` 안의 값을 실제 API 키로 바꿉니다.
   - 이 파일은 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다.

환경 변수 `YOUTUBE_API_KEY`로 설정해도 동작합니다.

## 3. 실행 방법

### 웹에서 실행 (Streamlit Community Cloud)

1. <https://share.streamlit.io> 에 GitHub 계정으로 로그인합니다.
2. **Create app**을 누르고 이 저장소, `main` 브랜치, `app.py`를 선택한 뒤 **Deploy**를 누릅니다.
3. 위의 **API 키 등록하기**를 따라 Secrets를 설정합니다.

### 내 컴퓨터에서 실행 (Python 3.10 이상)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 참고: API 사용량

YouTube Data API는 하루 무료 사용량(기본 10,000 단위)이 정해져 있습니다.
댓글을 한 번 불러올 때마다 약 1 단위를 사용합니다.
같은 영상을 10분 안에 다시 조회하면 저장해 둔 결과를 보여 주므로 사용량이 늘지 않습니다.

## 다음 단계 (예정)

- LLM API로 댓글을 분석해 위험도, 유형, 권장 대응을 표시
- 50개를 넘는 댓글 불러오기 (페이지 넘김)

※ 분석 결과는 참고용이며 법률 자문이 아닙니다.
