# streamlit_app.py
import os
import streamlit as st

from st_app.utils.state import initial_state, append_user_message, append_assistant_message
from st_app.graph.router import run_graph

st.set_page_config(page_title="RAG + Agent Demo", layout="wide")

# --- Secrets에서 API 키 로드 (Cloud/로컬 겸용) ---
if "UPSTAGE_API_KEY" in st.secrets:
    os.environ["UPSTAGE_API_KEY"] = st.secrets["UPSTAGE_API_KEY"]

st.title("코카콜라 리뷰 챗봇 (RAG + LangGraph)")

# --- 세션 상태 준비 ---
if "graph_state" not in st.session_state:
    st.session_state.graph_state = initial_state()

# 사이드바(디버그/설정)
with st.sidebar:
    st.markdown("### 상태/디버그")
    show_debug = st.checkbox("상태 보기", value=False)
    st.markdown("---")
    st.caption("키는 Streamlit Secrets에 저장되어야 합니다.")
    if os.getenv("UPSTAGE_API_KEY"):
        st.success("UPSTAGE_API_KEY loaded")
    else:
        st.warning("UPSTAGE_API_KEY not set")

# --- 채팅 UI ---
for m in st.session_state.graph_state["messages"]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_msg = st.chat_input("질문을 입력하세요…")
if user_msg:
    # 1) UI 로그에 사용자 메시지 기록
    append_user_message(st.session_state.graph_state, user_msg)

    # 2) 그래프 실행용 입력 세팅
    st.session_state.graph_state["user_input"] = user_msg
    st.session_state.graph_state["response"] = ""
    st.session_state.graph_state["route"] = "chat"  # 기본값(라우터가 바꿔줌)

    # 3) LangGraph 한 턴 실행
    st.session_state.graph_state = run_graph(st.session_state.graph_state)

    # 4) 어시스턴트 응답을 UI 메시지에 추가
    ans = st.session_state.graph_state.get("response", "")
    append_assistant_message(st.session_state.graph_state, ans)

    # 5) 화면에 바로 렌더
    with st.chat_message("assistant"):
        st.write(ans)

# --- 부가 정보 패널 ---
with st.expander("🔎 컨텍스트 / 출처 (있을 때만)", expanded=False):
    ctx = st.session_state.graph_state.get("context_lines") or []
    src = st.session_state.graph_state.get("sources") or []
    if ctx:
        st.markdown("**컨텍스트 발췌:**")
        st.write("\n".join(f"- {c}" for c in ctx))
    if src:
        st.markdown("**출처(검색 메타):**")
        st.json(src)

if show_debug:
    st.markdown("### Debug State")
    st.json(st.session_state.graph_state)
