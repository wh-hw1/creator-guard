import re

import streamlit as st

from mock_data import analyze_comment, get_comments

YOUTUBE_URL_PATTERN = re.compile(r"^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/\S+$")
RISK_BADGE = {"높음": "🔴 높음", "중간": "🟡 중간", "낮음": "🟢 낮음"}

st.set_page_config(page_title="크리에이터 권리 지킴이", page_icon="🛡️", layout="centered")

if "comments" not in st.session_state:
    st.session_state.comments = None
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None


# 1. 서비스 소개
st.title("🛡️ 크리에이터 권리 지킴이")
st.markdown(
    "청년 크리에이터를 위한 **AI 기반 권리 보호 서비스**입니다.  \n"
    "영상에 달린 댓글을 분석해 **악성 댓글**과 **저작권 침해 제보**를 찾아내고, "
    "어떻게 대응하면 좋을지 알려드립니다."
)
st.info("현재는 프로토타입입니다. 실제 영상 대신 테스트용 가상 댓글로 분석 흐름을 보여드립니다.", icon="ℹ️")

st.divider()

# 2. 유튜브 URL 입력 + 3. 분석 시작 버튼
st.subheader("1단계 · 영상 주소 입력")
video_url = st.text_input(
    "유튜브 영상 URL",
    placeholder="https://www.youtube.com/watch?v=...",
)

if st.button("댓글 분석 시작", type="primary", width="stretch"):
    if not video_url.strip():
        st.warning("영상 URL을 입력해 주세요.")
    elif not YOUTUBE_URL_PATTERN.match(video_url.strip()):
        st.error("유튜브 영상 주소 형식이 아닙니다. youtube.com 또는 youtu.be 주소를 입력해 주세요.")
    else:
        with st.spinner("댓글을 불러오는 중..."):
            st.session_state.comments = get_comments(video_url.strip())
        st.session_state.selected_id = None

# 4. 가상 댓글 목록
if st.session_state.comments:
    st.divider()
    st.subheader("2단계 · 댓글 선택")
    st.caption(f"댓글 {len(st.session_state.comments)}개를 불러왔습니다. 분석할 댓글을 선택하세요.")

    for comment in st.session_state.comments:
        is_selected = comment["id"] == st.session_state.selected_id
        with st.container(border=True):
            st.markdown(f"**{comment['author']}** · {comment['date']}")
            st.write(comment["text"])
            if st.button(
                "✔ 선택됨" if is_selected else "이 댓글 분석하기",
                key=f"select_{comment['id']}",
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.selected_id = comment["id"]
                st.rerun()

# 5. 선택한 댓글의 상세 분석 결과
selected = next(
    (c for c in st.session_state.comments or [] if c["id"] == st.session_state.selected_id),
    None,
)
if selected:
    result = analyze_comment(selected)

    st.divider()
    st.subheader("3단계 · 분석 결과")
    st.markdown(f"> {selected['text']}")

    col1, col2 = st.columns(2)
    col1.metric("위험도", RISK_BADGE.get(result["risk"], result["risk"]))
    col2.metric("유형", result["category"])

    st.markdown("**요약**")
    st.write(result["summary"])

    st.markdown("**판단 근거**")
    st.markdown("\n".join(f"- {item}" for item in result["evidence"]))

    st.markdown("**권장 대응**")
    st.markdown("\n".join(f"{i}. {item}" for i, item in enumerate(result["actions"], start=1)))

    st.caption("※ 이 결과는 참고용이며 법률 자문이 아닙니다. 실제 법적 대응이 필요하면 전문가와 상담하세요.")
