import os
import re

import streamlit as st

from youtube import MAX_COMMENTS, YouTubeError, extract_video_id, fetch_comments

st.set_page_config(page_title="크리에이터 권리 지킴이", page_icon="🛡️", layout="centered")

if "comments" not in st.session_state:
    st.session_state.comments = None
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None


def get_api_key() -> str | None:
    """Streamlit Secrets → 환경 변수 순서로 API 키를 찾습니다."""
    try:
        key = st.secrets.get("YOUTUBE_API_KEY")
    except Exception:  # secrets.toml 파일이 아예 없는 경우
        key = None
    return key or os.environ.get("YOUTUBE_API_KEY")


def escape_md(text: str) -> str:
    """댓글 속 특수문자가 마크다운 서식으로 바뀌지 않도록 이스케이프합니다."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~$])", r"\\\1", text)


@st.cache_data(ttl=600, show_spinner=False)
def load_comments(video_id: str, _api_key: str) -> list[dict]:
    # 같은 영상을 10분 안에 다시 조회하면 API를 호출하지 않아 사용량을 아낍니다.
    return fetch_comments(video_id, _api_key)


api_key = get_api_key()

# 1. 서비스 소개
st.title("🛡️ 크리에이터 권리 지킴이")
st.markdown(
    "청년 크리에이터를 위한 **AI 기반 권리 보호 서비스**입니다.  \n"
    "영상에 달린 댓글을 분석해 **악성 댓글**과 **저작권 침해 제보**를 찾아내고, "
    "어떻게 대응하면 좋을지 알려드립니다."
)
st.info("현재는 유튜브 공개 댓글 불러오기까지 제공합니다. AI 분석 기능은 다음 버전에서 추가됩니다.", icon="ℹ️")

if not api_key:
    st.warning(
        "YouTube API 키가 설정되지 않았습니다. "
        "Streamlit Secrets에 `YOUTUBE_API_KEY`를 등록해야 댓글을 불러올 수 있습니다. "
        "(설정 방법은 README.md 참고)",
        icon="🔑",
    )

st.divider()

# 2. 유튜브 URL 입력 + 3. 분석 시작 버튼
st.subheader("1단계 · 영상 주소 입력")
video_url = st.text_input(
    "유튜브 영상 URL",
    placeholder="https://www.youtube.com/watch?v=... 또는 https://youtu.be/...",
)

if st.button("댓글 분석 시작", type="primary", width="stretch", disabled=not api_key):
    # 실패했을 때 이전 영상의 댓글이 남아 보이지 않도록 먼저 비웁니다.
    st.session_state.comments = None
    st.session_state.selected_id = None
    video_id = extract_video_id(video_url)

    if not video_url.strip():
        st.warning("영상 URL을 입력해 주세요.")
    elif not video_id:
        st.error("유튜브 영상 주소를 인식하지 못했습니다. youtube.com/watch?v=... 또는 youtu.be/... 형식의 주소를 입력해 주세요.")
    else:
        try:
            with st.spinner("유튜브에서 댓글을 불러오는 중..."):
                comments = load_comments(video_id, api_key)
        except YouTubeError as e:
            st.error(str(e))
        else:
            if comments:
                st.session_state.comments = comments
                st.session_state.video_id = video_id
            else:
                st.info("이 영상에는 아직 공개 댓글이 없습니다.")

# 4. 댓글 목록
if st.session_state.comments:
    st.divider()
    st.subheader("2단계 · 댓글 선택")
    st.caption(
        f"[영상](https://www.youtube.com/watch?v={st.session_state.video_id})의 최신 공개 댓글 "
        f"{len(st.session_state.comments)}개를 불러왔습니다. (최대 {MAX_COMMENTS}개) 살펴볼 댓글을 선택하세요."
    )

    with st.container(height=520, border=False):
        for comment in st.session_state.comments:
            is_selected = comment["id"] == st.session_state.selected_id
            with st.container(border=True):
                st.markdown(f"**{escape_md(comment['author'])}** · {comment['published_at']}")
                st.markdown(escape_md(comment["text"]))
                if st.button(
                    "✔ 선택됨" if is_selected else "이 댓글 살펴보기",
                    key=f"select_{comment['id']}",
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state.selected_id = comment["id"]
                    st.rerun()

# 5. 선택한 댓글 상세
selected = next(
    (c for c in st.session_state.comments or [] if c["id"] == st.session_state.selected_id),
    None,
)
if selected:
    st.divider()
    st.subheader("3단계 · 댓글 상세")
    st.markdown("> " + escape_md(selected["text"]).replace("\n", "  \n> "))

    col1, col2 = st.columns(2)
    col1.markdown(f"**작성자**  \n{escape_md(selected['author'])}")
    col2.markdown(f"**작성 시각**  \n{selected['published_at']} (KST)")
    st.markdown(f"**댓글 ID**  \n`{selected['id']}`")

    st.info("AI 분석(위험도·유형·권장 대응)은 다음 버전에서 제공될 예정입니다.", icon="🛠️")
