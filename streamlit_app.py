# streamlit_app.py
import os
import streamlit as st

from st_app.utils.state import initial_state
from st_app.graph.router import run_graph

st.set_page_config(page_title="RAG + Agent Demo", layout="wide")
st.title("코카콜라 리뷰 챗봇 (RAG + LangGraph)")

# 1) Secrets에서 Upstage API 키 읽기
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

# 5) 입력받고 그래프 한 턴 실행 (A방법 + 중복 방지 가드)
user_msg = st.chat_input("질문을 입력하세요…")
if user_msg:
    state = st.session_state.graph_state

    # 5-1) state 세팅
    state["user_input"] = user_msg
    state["response"] = ""
    state["route"] = "chat"  # decide_route가 덮어씀

    # 5-2) 사용자 메시지 '선(先)추가' (중복 방지)
    # 백엔드가 이전 턴에서 같은 유저 메시지를 이미 넣었을 수도 있으니, 마지막만 확인
    last_msg = state["messages"][-1] if state["messages"] else None
    if not (last_msg and last_msg.get("role") == "user" and last_msg.get("content") == user_msg):
        state["messages"].append({"role": "user", "content": user_msg})

    # 5-3) 사용자 버블 즉시 표시
    with st.chat_message("user"):
        st.write(user_msg)

    # 5-4) 그래프 실행
    state = run_graph(state)
    st.session_state.graph_state = state

    ans = state.get("response", "")

    # 5-5) 어시스턴트 버블 즉시 표시
    if ans:
        with st.chat_message("assistant"):
            st.write(ans)

        # 5-6) 어시스턴트 메시지 히스토리 추가 (중복 방지)
        # 백엔드가 이미 같은 답변을 messages 끝에 넣었을 수 있으므로 마지막만 검사
        last_msg = state["messages"][-1] if state["messages"] else None
        if not (last_msg and last_msg.get("role") == "assistant" and last_msg.get("content") == ans):
            state["messages"].append({"role": "assistant", "content": ans})

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
