# st_app/graph/router.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any

from st_app.rag.llm import chat as call_llm
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

# --- 1) 라우팅 판단 노드 -------------------------------------

ROUTE_SYSTEM = (
    "너는 분류기야. 아래 사용자 질문의 의도를 판단해 아래 중 정확히 하나만 출력해.\n"
    "- 제품의 기본 정보/스펙/성분/보관/브랜드 히스토리 → subject\n"
    "- 리뷰를 근거로 한 질문(맛/탄산/배송/가격/품질/후기 요약 등) → review\n"
    "- 그 밖의 일반 대화/인사/가벼운 질의응답 → chat\n"
    "반드시 'chat' 또는 'subject' 또는 'review' 딱 한 단어만 출력."
)

def decide_route(state: Dict[str, Any]) -> Dict[str, Any]:
    q = state.get("user_input", "").strip()
    if not q:
        state["route"] = "chat"
        return state
    out = call_llm(system=ROUTE_SYSTEM, user=q, temperature=0.0, max_tokens=3)
    route = out.strip().lower()
    if route not in {"chat", "subject", "review"}:
        route = "chat"
    state["route"] = route
    return state

# --- 2) LangGraph 구성 ---------------------------------------

def build_graph():
    g = StateGraph(dict)  # 우리는 dict 상태를 사용

    # 노드 등록
    g.add_node("decide", decide_route)
    g.add_node("chat", chat_node)
    g.add_node("subject", subject_info_node)
    g.add_node("review", rag_review_node)

    # 시작점: 라우팅 결정
    g.set_entry_point("decide")

    # 분기
    def branch(state: Dict[str, Any]) -> str:
        return state.get("route", "chat")

    g.add_conditional_edges(
        "decide",
        branch,
        {
            "chat": "chat",
            "subject": "subject",
            "review": "review",
        },
    )

    # subject/review 이후에는 chat_node로 넘겨서 "사후 정리"를 수행
    g.add_edge("subject", "chat")
    g.add_edge("review", "chat")

    # chat에서 한 턴 종료
    g.add_edge("chat", END)

    return g.compile()

_graph = build_graph()

def run_graph(state: Dict[str, Any]) -> Dict[str, Any]:
    """한 턴 실행. state(dict)를 넣고 최종 state(dict)를 반환."""
    return _graph.invoke(state)
