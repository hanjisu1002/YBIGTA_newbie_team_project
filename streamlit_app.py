# streamlit_app.py
import os
import streamlit as st

from st_app.utils.state import initial_state, reset_session_state, is_session_expired
from st_app.graph.router import run_graph

st.set_page_config(page_title="RAG + Agent Demo", layout="wide")
st.title("코카콜라 리뷰 챗봇 (RAG + LangGraph)")

# 1) Secrets에서 Upstage API 키 읽기
if "UPSTAGE_API_KEY" in st.secrets:
    os.environ["UPSTAGE_API_KEY"] = st.secrets["UPSTAGE_API_KEY"]

# 2) 세션 상태 준비 및 사용자 구분
if "graph_state" not in st.session_state:
    st.session_state.graph_state = initial_state()
    st.session_state.is_new_user = True
    st.session_state.session_initialized = True
else:
    # 기존 세션이 있는 경우 새 사용자 여부 확인
    if "is_new_user" not in st.session_state:
        st.session_state.is_new_user = False
    
    # 세션 만료 확인 (24시간)
    current_state = st.session_state.graph_state
    if current_state.get("created_at") and is_session_expired(current_state["created_at"]):
        st.session_state.graph_state = reset_session_state()
        st.session_state.is_new_user = True
        st.rerun()
    
    # 세션 초기화 완료 표시
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True

# 3) 사이드바 디버그 및 세션 관리
with st.sidebar:
    st.markdown("### 상태/디버그")
    show_debug = st.checkbox("상태 보기", value=False)
    
    # 현재 세션 정보 표시
    st.markdown("### 📊 현재 세션")
    current_session = st.session_state.graph_state
    if current_session.get("session_id"):
        st.text(f"세션 ID: {current_session['session_id'][:8]}...")
    
    if current_session.get("created_at"):
        import datetime
        created_time = datetime.datetime.fromtimestamp(current_session["created_at"])
        st.text(f"시작: {created_time.strftime('%H:%M:%S')}")
    
    message_count = len(current_session.get("messages", []))
    st.text(f"대화 수: {message_count}")
    
    # 세션 관리 버튼들
    st.markdown("### 세션 관리")
    if st.button("🔄 새로 시작", help="대화 기록을 모두 지우고 새로 시작합니다"):
        st.session_state.graph_state = reset_session_state()
        st.session_state.is_new_user = True
        st.rerun()
    
    if st.button("🗑️ 대화 기록만 지우기", help="대화 기록만 지우고 다른 설정은 유지합니다"):
        st.session_state.graph_state["messages"] = []
        st.rerun()
    
    st.markdown("---")
    if os.getenv("UPSTAGE_API_KEY"):
        st.success("UPSTAGE_API_KEY loaded")
    else:
        st.warning("UPSTAGE_API_KEY not set (Secrets에 키를 넣어주세요)")

# 4) 새 사용자 환영 메시지
if st.session_state.get("is_new_user", False):
    st.info("🎉 새로운 사용자님, 환영합니다! 코카콜라 리뷰에 대해 무엇이든 물어보세요.")
    st.session_state.is_new_user = False

# 5) 기존 대화 로그 렌더링
for m in st.session_state.graph_state["messages"]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# 6) 입력받고 그래프 한 턴 실행 (A방법 + 중복 방지 가드)
user_msg = st.chat_input("질문을 입력하세요…")
if user_msg:
    state = st.session_state.graph_state

    # 6-1) state 세팅
    state["user_input"] = user_msg
    state["response"] = ""
    state["route"] = "chat"  # decide_route가 덮어씀

    # 6-2) 사용자 메시지 '선(先)추가' (중복 방지)
    # 백엔드가 이전 턴에서 같은 유저 메시지를 이미 넣었을 수도 있으니, 마지막만 확인
    last_msg = state["messages"][-1] if state["messages"] else None
    if not (last_msg and last_msg.get("role") == "user" and last_msg.get("content") == user_msg):
        state["messages"].append({"role": "user", "content": user_msg})

    # 6-3) 사용자 버블 즉시 표시
    with st.chat_message("user"):
        st.write(user_msg)

    # 6-4) 그래프 실행
    state = run_graph(state)
    st.session_state.graph_state = state

    ans = state.get("response", "")

    # 6-5) 어시스턴트 버블 즉시 표시
    if ans:
        with st.chat_message("assistant"):
            st.write(ans)

        # 6-6) 어시스턴트 메시지 히스토리 추가 (중복 방지)
        # 백엔드가 이미 같은 답변을 messages 끝에 넣었을 수 있으므로 마지막만 검사
        last_msg = state["messages"][-1] if state["messages"] else None
        if not (last_msg and last_msg.get("role") == "assistant" and last_msg.get("content") == ans):
            state["messages"].append({"role": "assistant", "content": ans})

# 7) 컨텍스트/출처 패널
with st.expander("🔎 컨텍스트 / 출처 (있을 때만)"):
    ctx = st.session_state.graph_state.get("context_lines") or []
    src = st.session_state.graph_state.get("sources") or []
    if ctx:
        st.markdown("**컨텍스트 발췌:**")
        st.write("\n".join(f"- {c}" for c in ctx))
    if src:
        st.markdown("**출처(검색 메타):**")
        st.json(src)

# 8) 디버그 상태 보기
if show_debug:
    st.markdown("### Debug State")
    st.json(st.session_state.graph_state)
