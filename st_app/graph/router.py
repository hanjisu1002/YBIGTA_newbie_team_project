from typing import Dict, Any
from langgraph.graph import StateGraph, END

from st_app.utils.state import ChatState
from st_app.rag.llm import chat as call_llm
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

# --- 라우팅 프롬프트 (LLM) ---
ROUTE_SYSTEM = (
    "너는 분류기야. 아래 사용자 질문의 의도를 판단해 아래 중 정확히 하나만 출력해.\n"
    "- 제품의 기본 정보/스펙/성분/보관/브랜드 히스토리 → subject\n"
    "- 리뷰를 근거로 한 질문(맛/탄산/배송/가격/품질/후기 요약/추천 등) → review\n"
    "- 그 밖의 일반 대화/인사/가벼운 질의응답 → chat\n"
    "반드시 'chat' 또는 'subject' 또는 'review' 딱 한 단어만 출력."
)

# --- 휴리스틱 키워드 (LLM 보정/단절 입력 대비) ---
REVIEW_KWS = {"리뷰", "후기", "평", "평가", "요약", "추천", "맛", "탄산", "가격", "배송", "품질"}
SUBJECT_KWS = {"성분", "원재료", "스펙", "보관", "브랜드", "히스토리", "유래"}

AFFIRM_KWS = {"응", "네", "맞아", "그래", "웅", "ㅇㅇ", "웅웅", "예", "요"}  # 짧은 긍정
PRODUCT_KWS = {
    # 간단 제품 추출기 (필요 시 확장)
    "코카콜라": "코카콜라",
    "콜라": "코카콜라",           # 일반 콜라도 기본값은 코카콜라로 매핑
    "제로콜라": "코카콜라 제로",
    "코카콜라 제로": "코카콜라 제로",
    "coca-cola": "코카콜라",
    "coke": "코카콜라",
}

print("[DEBUG] decide_route loaded")


def _extract_product(text: str) -> str | None:
    t = text.lower().strip()
    for k, v in PRODUCT_KWS.items():
        if k in t:
            return v
    return None

def _heuristic_route(text: str, last_intent: str | None) -> str | None:
    """명확한 키워드 또는 긍정/짧은 응답일 때 휴리스틱으로 라우트 확정."""
    t = text.strip().lower()

    # 짧은 긍정/단답이면 직전 의도 유지
    if (len(t) <= 2 or t in AFFIRM_KWS) and last_intent in {"subject", "review"}:
        return last_intent

    # 한국어 키워드 강제 라우팅
    if any(kw in t for kw in REVIEW_KWS):
        return "review"
    if any(kw in t for kw in SUBJECT_KWS):
        return "subject"

    # 제품 단독 언급 + 직전이 review라면 review 유지
    if _extract_product(text) and last_intent == "review":
        return "review"

    return None  # 결정 못하면 LLM에 위임

def decide_route(state: ChatState) -> ChatState:
    q = (state.get("user_input") or "").strip()
    last_intent = state.get("last_intent") or "chat"
    last_product = state.get("last_product")

    # 1) 휴리스틱 우선 적용
    h = _heuristic_route(q, last_intent)
    if h in {"chat", "subject", "review"}:
        route = h
    else:
        # 2) LLM 분류
        if not q:
            route = "chat"
        else:
            out = call_llm(system=ROUTE_SYSTEM, user=q, temperature=0.0, max_tokens=3)
            route = out.strip().lower()
            if route not in {"chat", "subject", "review"}:
                route = "chat"

        # 3) 후처리: 제품 단독 언급인데 LLM이 chat이라고 한 경우, 직전이 review면 review로 승격
        if route == "chat" and _extract_product(q) and last_intent == "review":
            route = "review"

    # 제품명 추출/승계
    product = _extract_product(q) or last_product
    # 리뷰 의도인데 제품이 아직 없고 바로 앞 대화에서 제품을 말했으면 승계됨 (위 한 줄로 처리)

    # 상태 업데이트
    state["route"] = route
    state["last_intent"] = route  # 현재 의도를 다음 턴 기본값으로
    state["last_product"] = product

    # downstream 노드들이 참조할 수 있도록 힌트 필드 남기기
    if product:
        state["product_name"] = product  # rag_review_node/subject_info_node에서 사용

    print(f"[DEBUG] q={q}, last_intent={last_intent}, last_product={last_product}, product={product}")

    return state

# --- 그래프 구성 ---
def build_graph():
    g = StateGraph(dict)  # dict 상태 사용 (ChatState는 타입 힌트용)

    # 노드 등록
    g.add_node("decide", decide_route)
    g.add_node("chat", chat_node)
    g.add_node("subject", subject_info_node)
    g.add_node("review", rag_review_node)

    # 시작점
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

    # subject/review 처리 후 chat으로 넘겨서 사후 정리(요약/후속 멘트)
    g.add_edge("subject", "chat")
    g.add_edge("review", "chat")

    # chat에서 종료
    g.add_edge("chat", END)

    return g.compile()

_app = build_graph()

def run_graph(state: ChatState) -> ChatState:
    """한 턴 실행: 입력 state를 받아 최종 state 반환."""
    return _app.invoke(state)
