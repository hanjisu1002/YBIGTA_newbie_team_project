# streamlit_app.py
import os
import streamlit as st

from st_app.utils.state import initial_state, append_user_message, append_assistant_message
from st_app.graph.router import run_graph

st.set_page_config(page_title="RAG + Agent Demo", layout="wide")
st.title("코카콜라 리뷰 챗봇 (RAG + LangGraph)")

# 1) Secrets에서 Upstage API 키 읽기 (Cloud/로컬 겸용)
if "UPSTAGE_API_KEY" in st.secrets:
    os.environ["UPSTAGE_API_KEY"] = st.secrets["UPSTAGE_API_KEY"]

# 2) 세션 상태 준비
if "graph_state" not in st.session_state:
    st.session_state.graph_state = initial_state()

# 3) 사이드바 디버그
with st.sidebar:
    st.markdown("### 상태/디버그")
    show_debug = st.checkbox("상태 보기", value=False)
    st.markdown("---")
    if os.getenv("UPSTAGE_API_KEY"):
        st.success("UPSTAGE_API_KEY loaded")
    else:
        st.warning("UPSTAGE_API_KEY not set (Secrets에 키를 넣어주세요)")

# 4) 기존 대화 로그 렌더링
for m in st.session_state.graph_state["messages"]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# 5) 입력받고 그래프 한 턴 실행
user_msg = st.chat_input("질문을 입력하세요…")
if user_msg:
    append_user_message(st.session_state.graph_state, user_msg)

    st.session_state.graph_state["user_input"] = user_msg
    st.session_state.graph_state["response"] = ""
    st.session_state.graph_state["route"] = "chat"  # 기본값 (decide가 덮어씀)

    st.session_state.graph_state = run_graph(st.session_state.graph_state)

    ans = st.session_state.graph_state.get("response", "")
    append_assistant_message(st.session_state.graph_state, ans)

    with st.chat_message("assistant"):
        st.write(ans)

# 6) 컨텍스트/출처 패널
with st.expander("🔎 컨텍스트 / 출처 (있을 때만)"):
    ctx = st.session_state.graph_state.get("context_lines") or []
    src = st.session_state.graph_state.get("sources") or []
    if ctx:
        st.markdown("**컨텍스트 발췌:**")
        st.write("\n".join(f"- {c}" for c in ctx))
    if src:
        st.markdown("**출처(검색 메타):**")
        st.json(src)

# 7) 디버그 상태 보기
if show_debug:
    st.markdown("### Debug State")
    st.json(st.session_state.graph_state)
