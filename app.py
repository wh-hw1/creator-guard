import os
import re

import streamlit as st

from analyzer import AnalysisError, analyze_comment
from legal_basis import CHECKED_ON, lookup
from youtube import MAX_COMMENTS, YouTubeError, extract_video_id, fetch_comments, fetch_video_info

st.set_page_config(page_title="크리에이터 권리 지킴이", page_icon="🛡️", layout="centered")

if "comments" not in st.session_state:
    st.session_state.comments = None
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "analyses" not in st.session_state:
    st.session_state.analyses = {}  # 댓글 ID → AI 분석 결과

LEVEL_BADGE = {
    "검토 필요성 높음": "🔴 검토 필요성 높음",
    "검토 필요": "🟠 검토 필요",
    "검토 필요성 낮음": "🟡 검토 필요성 낮음",
    "해당 없음": "⚪ 해당 없음",
}


def get_secret(name: str) -> str | None:
    """Streamlit Secrets → 환경 변수 순서로 비밀 값을 찾습니다."""
    try:
        value = st.secrets.get(name)
    except Exception:  # secrets.toml 파일이 아예 없는 경우
        value = None
    return value or os.environ.get(name)


def escape_md(text: str) -> str:
    """댓글 속 특수문자가 마크다운 서식으로 바뀌지 않도록 이스케이프합니다."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~$])", r"\\\1", text)


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {escape_md(item)}" for item in items)


@st.cache_data(ttl=600, show_spinner=False)
def load_comments(video_id: str, _api_key: str) -> list[dict]:
    # 같은 영상을 10분 안에 다시 조회하면 API를 호출하지 않아 사용량을 아낍니다.
    return fetch_comments(video_id, _api_key)


@st.cache_data(ttl=600, show_spinner=False)
def load_video_info(video_id: str, _api_key: str) -> dict | None:
    return fetch_video_info(video_id, _api_key)


def show_analysis(result: dict) -> None:
    st.warning(
        "아래 내용은 범죄 여부를 판단한 것이 아니라, **법적으로 검토해 볼 만한 쟁점과 추가로 확인할 사실**을 정리한 참고 자료입니다.",
        icon="⚖️",
    )

    st.markdown(f"**종합 판단:** {result['comment_type']}")
    st.write(result["summary"])
    st.markdown(
        f"**댓글 대상:** {escape_md(result['target'])} · 피해자 특정 여부: {result['target_identifiable']}"
    )

    for issue in result["issues"]:
        with st.container(border=True):
            st.markdown(f"#### {issue['issue']} · {LEVEL_BADGE[issue['review_level']]}")
            if issue["quoted_expressions"]:
                st.markdown("**근거가 된 표현**")
                st.markdown(bullet_list([f"“{q}”" for q in issue["quoted_expressions"]]))
            st.markdown("**판단 기준 적용**")
            st.write(issue["reasoning"])
            if issue["supporting_factors"]:
                st.markdown("**쟁점이 인정되는 방향의 사정**")
                st.markdown(bullet_list(issue["supporting_factors"]))
            if issue["opposing_factors"]:
                st.markdown("**쟁점이 부정되는 방향의 사정**")
                st.markdown(bullet_list(issue["opposing_factors"]))
            if issue["facts_to_verify"]:
                st.markdown("**추가로 확인해야 할 사실**")
                st.markdown(bullet_list(issue["facts_to_verify"]))
            refs = [lookup(i) for i in issue["basis_ids"] if lookup(i)]
            if refs:
                with st.expander("관련 법령·판례 (국가법령정보센터 원문)"):
                    for ref in refs:
                        detail = ref.get("point") or ref.get("text")
                        st.markdown(f"[{ref['title']}]({ref['url']})  \n{detail}")

    if result["common_facts_to_verify"]:
        st.markdown("**공통으로 확인할 사실**")
        st.markdown(bullet_list(result["common_facts_to_verify"]))

    st.caption(
        f"법령·판례는 국가법령정보센터 원문 기준({CHECKED_ON} 확인)이며, AI 분석은 오류가 있을 수 있습니다. "
        "이 결과는 법률 자문이 아닙니다. 고소·신고 등 실제 대응은 변호사 등 전문가와 상담하세요."
    )


youtube_key = get_secret("YOUTUBE_API_KEY")
anthropic_key = get_secret("ANTHROPIC_API_KEY")

# 1. 서비스 소개
st.title("🛡️ 크리에이터 권리 지킴이")
st.markdown(
    "청년 크리에이터를 위한 **AI 기반 권리 보호 서비스**입니다.  \n"
    "영상에 달린 댓글을 분석해 **악성 댓글**과 **저작권 침해 제보**를 찾아내고, "
    "어떻게 대응하면 좋을지 알려드립니다."
)
st.info(
    "현재는 유튜브 공개 댓글 불러오기와, 댓글 하나에 대한 **AI 법적 쟁점 분석(모욕·명예훼손·협박)** 을 제공합니다.",
    icon="ℹ️",
)

if not youtube_key:
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

if st.button("댓글 분석 시작", type="primary", width="stretch", disabled=not youtube_key):
    # 실패했을 때 이전 영상의 댓글이 남아 보이지 않도록 먼저 비웁니다.
    st.session_state.comments = None
    st.session_state.video_info = None
    st.session_state.selected_id = None
    video_id = extract_video_id(video_url)

    if not video_url.strip():
        st.warning("영상 URL을 입력해 주세요.")
    elif not video_id:
        st.error("유튜브 영상 주소를 인식하지 못했습니다. youtube.com/watch?v=... 또는 youtu.be/... 형식의 주소를 입력해 주세요.")
    else:
        try:
            with st.spinner("유튜브에서 댓글을 불러오는 중..."):
                comments = load_comments(video_id, youtube_key)
        except YouTubeError as e:
            st.error(str(e))
        else:
            if comments:
                st.session_state.comments = comments
                st.session_state.video_id = video_id
                st.session_state.video_info = load_video_info(video_id, youtube_key)
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

# 5. 선택한 댓글 상세 + AI 분석
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

    st.divider()
    st.subheader("4단계 · AI 법적 쟁점 분석")
    st.caption("대한민국 법률을 기준으로 모욕·명예훼손·협박 쟁점 후보와 추가로 확인할 사실을 정리합니다.")

    result = st.session_state.analyses.get(selected["id"])
    if result:
        show_analysis(result)
    elif not anthropic_key:
        st.warning(
            "Anthropic API 키가 설정되지 않았습니다. Streamlit Secrets에 `ANTHROPIC_API_KEY`를 등록해야 AI 분석을 사용할 수 있습니다. "
            "(설정 방법은 README.md 참고)",
            icon="🔑",
        )
    elif st.button("이 댓글 AI 분석하기", type="primary", width="stretch"):
        try:
            with st.spinner("AI가 댓글을 분석하는 중입니다... (최대 1분 정도 걸릴 수 있습니다)"):
                analysis = analyze_comment(selected, st.session_state.video_info, anthropic_key)
        except AnalysisError as e:
            st.error(str(e))
        else:
            st.session_state.analyses[selected["id"]] = analysis.model_dump()
            st.rerun()
