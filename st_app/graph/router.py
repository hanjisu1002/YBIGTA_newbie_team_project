from typing import Dict, Any
from langgraph.graph import StateGraph, END

from st_app.utils.state import ChatState, initial_state
from st_app.rag.llm import chat as call_llm
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

print("[ROUTER LOADED]", __file__)

# -----------------------
# 인메모리 세션 (파일 추가 없이 모듈 전역 보관)
# -----------------------
_SESSIONS: Dict[str, ChatState] = {}

# -----------------------
# LLM 기반 라우팅 프롬프트
# -----------------------
ROUTE_SYSTEM = (
    "너는 사용자 질문의 의도를 분석하는 분류기야. 아래 세 노드 중 하나로 라우팅해.\n\n"
    "**subject**: 제품의 객관적 정보나 사실을 묻는 질문\n"
    "**review**: 다른 사람들의 경험이나 주관적 평가를 묻는 질문\n"
    "**chat**: 일반적인 대화나 제품과 무관한 질문\n\n"
    "**판단 기준**:\n"
    "- 질문의 본질적 의도가 무엇인지 파악해라\n"
    "- 직전 대화 맥락을 고려해라\n"
    "- 키워드가 아닌 의미를 중시해라\n\n"
    "**예시**:\n"
    "- '성분이 뭐야?' → subject (제품 정보)\n"
    "- '맛이 어때?' → review (경험/평가)\n"
    "- '다른 사람들은?' → review (다른 사람 의견)\n"
    "- '안녕하세요' → chat (일반 대화)\n\n"
    "'chat', 'subject', 'review' 중 하나만 출력."
)

# -----------------------
# 키워드 (휴리스틱용)
# -----------------------
REVIEW_KWS = {"리뷰", "후기", "평", "평가", "요약", "추천", "맛", "탄산", "가격", "배송", "품질"}
SUBJECT_KWS = {"성분", "원재료", "스펙", "보관", "브랜드", "히스토리", "유래"}
AFFIRM_KWS = {"응", "네", "맞아", "그래", "웅", "ㅇㅇ", "예", "요"}

PRODUCT_KWS = {
    "코카콜라": "코카콜라",
    "코카콜라 제로": "코카콜라 제로",
    "제로콜라": "코카콜라 제로",
    "coca-cola": "코카콜라",
    "coke": "코카콜라",
    # "콜라": "코카콜라",  # "콜라"는 제거 - 너무 광범위함
}
CATEGORY_KWS = {
    "탄산음료": "탄산음료",
    "탄산": "탄산음료",
    "음료": "음료",
}

# -----------------------
# 유틸
# -----------------------
def _extract_product(text: str) -> str | None:
    t = text.lower()
    for k, v in PRODUCT_KWS.items():
        if k in t:
            return v
    return None

def _extract_category(text: str) -> str | None:
    t = text.lower()
    for k, v in CATEGORY_KWS.items():
        if k in t:
            return v
    return None

# 휴리스틱 라우팅 함수 (현재는 LLM 기반으로 대체됨)
# def _heuristic_route(text: str, last_intent: str | None, last_prod: str | None, last_cat: str | None) -> str | None:
#     t = text.strip().lower()
# 
#     # 단답 긍정 → 직전 의도 유지
#     if (len(t) <= 2 or t in AFFIRM_KWS) and last_intent in {"subject", "review"}:
#         return last_intent
# 
#     # 직전 제품이 있고, 리뷰 관련 키워드면 review로
#     if last_prod and any(kw in t for kw in ["맛", "배송", "가격", "품질", "추천", "어때", "좋아", "나빠"]):
#         return "review"
#     
#     # 직전 제품이 있고, 정보 관련 키워드면 subject로  
#     if last_prod and any(kw in t for kw in ["성분", "원산지", "보관", "브랜드", "어떻게", "뭐로"]):
#         return "subject"
# 
#     # 일반적인 리뷰/서브젝트 키워드
#     if any(kw in t for kw in REVIEW_KWS):
#         return "review"
#     if any(kw in t for kw in SUBJECT_KWS):
#         return "subject"
# 
#     # 제품/카테고리만 언급 + 직전이 review면 review 유지
#     if (_extract_product(text) or _extract_category(text)) and last_intent == "review":
#         return "review"
# 
#     return None

# -----------------------
# 핵심: LLM 기반 라우팅
# -----------------------
def decide_route(state: ChatState) -> ChatState:
    print(f"[DECIDE_ROUTE IN] Full state: {state}")
    
    # 상태가 비어있거나 user_input이 없는 경우 방어
    if not state or not state.get("user_input"):
        print(f"[DECIDE_ROUTE WARN] Empty state or missing user_input, using default chat route")
        return {
            "route": "chat",
            "last_intent": "chat",
            "user_input": "",
            "response": "",
            "context_lines": [],
            "sources": [],
            "messages": [],
            "last_product": None,
            "last_category": None,
        }
    
    q = (state.get("user_input") or "").strip()
    print(f"[DECIDE_ROUTE IN] user_input='{state.get('user_input')}' q='{q}' last_intent={state.get('last_intent')} last_product={state.get('last_product')}")
    last_intent = state.get("last_intent") or "chat"
    last_product = state.get("last_product")
    last_category = state.get("last_category")

    # 일반적인 인사말은 무조건 chat 노드로
    greeting_keywords = {"안녕", "안녕하세요", "안녕하십니까", "하이", "hi", "hello", "반가워", "반갑습니다"}
    if q.lower() in greeting_keywords or any(greeting in q.lower() for greeting in greeting_keywords):
        route = "chat"
        print(f"[DECIDE_ROUTE] Greeting detected: '{q}' -> chat")
    else:
        # 제품명과 카테고리 추출 (LLM 호출 전에)
        prod_now = _extract_product(q)
        cat_now = _extract_category(q)
        
        # 현재 추출된 값이나 직전 값 사용
        current_product = prod_now or last_product
        current_category = cat_now or last_category
        
        # 맥락 정보를 포함한 프롬프트 구성 (제품명 키워드 정보 포함)
        context_info = f"직전 의도: {last_intent}, 현재 제품: {current_product or '없음'}, 현재 카테고리: {current_category or '없음'}"
        
        # 제품명 키워드가 추출된 경우 추가 정보 제공
        if prod_now:
            context_info += f", 이번 질문에서 제품명 '{prod_now}' 감지됨"
        if cat_now:
            context_info += f", 이번 질문에서 카테고리 '{cat_now}' 감지됨"
            
        enhanced_prompt = f"질문: {q}\n\n맥락: {context_info}\n\n이 질문은 어떤 노드로 라우팅해야 할까요?"
        
        print(f"[DECIDE_ROUTE] Calling LLM with context: {context_info}")
        out = call_llm(system=ROUTE_SYSTEM, user=enhanced_prompt, temperature=0.0, max_tokens=3)
        route = out.strip().lower()
        
        if route not in {"chat", "subject", "review"}:
            print(f"[DECIDE_ROUTE] LLM returned invalid route: '{route}', defaulting to chat")
            route = "chat"
        
        print(f"[DECIDE_ROUTE] LLM decided route: {route}")

    # 상태를 복사하여 수정 (원본 상태 보존)
    new_state = state.copy()
    
    # 슬롯 업데이트(이번 턴 값 우선, 없으면 과거 값)
    prod_now = _extract_product(q)
    cat_now = _extract_category(q)
    product = prod_now or last_product
    category = cat_now or last_category

    if product:
        new_state["last_product"] = product
    if category:
        new_state["last_category"] = category

    new_state["route"] = route
    new_state["last_intent"] = route
    
    # user_input이 제대로 반환되도록 보장
    new_state["user_input"] = q
    
    print(f"[DECIDE_ROUTE OUT] route={route} last_product={new_state.get('last_product')} last_category={new_state.get('last_category')} user_input={new_state.get('user_input')}")
    return new_state

# -----------------------
# 그래프 구성
# -----------------------
def build_graph():
    g = StateGraph(ChatState)

    g.add_node("decide", decide_route)
    g.add_node("chat", chat_node)
    g.add_node("subject", subject_info_node)
    g.add_node("review", rag_review_node)

    g.set_entry_point("decide")

    def branch(state: ChatState) -> str:
        return state.get("route", "chat")

    g.add_conditional_edges("decide", branch, {
        "chat": "chat",
        "subject": "subject",
        "review": "review",
    })

    # 각 노드가 직접 END로 연결 (후속 chat 노드 제거)
    g.add_edge("chat", END)
    g.add_edge("subject", END)
    g.add_edge("review", END)

    return g.compile()

_app = build_graph()

# -----------------------
# 실행 엔트리 (세션 유지 포함)
# -----------------------
def run_graph(state: ChatState) -> ChatState:
    print("[RUN_GRAPH] called with session_id=", state.get("session_id"))
    sid = state.get("session_id") or "default"

    base = _SESSIONS.get(sid)
    if base is None:
        base = initial_state()
        base["session_id"] = sid
        _SESSIONS[sid] = base

    # user_input 처리 - 직접 전달된 값 우선, 없으면 messages에서 추출
    new_text = (state.get("user_input") or "").strip()
    if not new_text:
        # messages에서 마지막 user 발화 추출
        msgs = state.get("messages") or base.get("messages") or []
        for m in reversed(msgs):
            if m.get("role") == "user" and m.get("content"):
                new_text = m["content"].strip()
                break
    
    # user_input이 비어있으면 경고
    if not new_text:
        print("[WARN] empty user_input (no text found).")
        return base

    # 이번 턴 입력 반영 (나머지 메모리는 유지)
    base["user_input"] = new_text
    print(f"[RUN_GRAPH] user_input set to: '{new_text}'")
    print(f"[RUN_GRAPH] base state keys: {list(base.keys())}")
    print(f"[RUN_GRAPH] base user_input: '{base.get('user_input')}'")

    # 상태를 명시적으로 복사해서 전달 (깊은 복사로 메모리 보존)
    input_state = {
        "session_id": base.get("session_id"),
        "user_input": base.get("user_input"),
        "response": base.get("response", ""),
        "route": base.get("route", "chat"),
        "context_lines": base.get("context_lines", []),
        "sources": base.get("sources", []),
        "messages": base.get("messages", []).copy(),  # 리스트 복사
        "last_intent": base.get("last_intent", "chat"),
        "last_product": base.get("last_product"),
        "last_category": base.get("last_category"),
    }
    print(f"[RUN_GRAPH] input_state keys: {list(input_state.keys())}")
    print(f"[RUN_GRAPH] input_state user_input: '{input_state.get('user_input')}'")

    out = _app.invoke(input_state)
    
    # 응답 후 메모리 상태 업데이트 (중복 방지)
    if out.get("response"):
        # 기존 메시지 배열 복사
        if "messages" not in out:
            out["messages"] = base.get("messages", []).copy()
        else:
            out["messages"] = out["messages"].copy()
        
        # 사용자 메시지가 이미 있는지 확인 (중복 방지)
        user_msg_exists = any(msg.get("role") == "user" and msg.get("content") == new_text for msg in out["messages"])
        if not user_msg_exists:
            out["messages"].append({"role": "user", "content": new_text})
        
        # 어시스턴트 응답이 이미 있는지 확인 (중복 방지)
        assistant_msg_exists = any(msg.get("role") == "assistant" and msg.get("content") == out["response"] for msg in out["messages"])
        if not assistant_msg_exists:
            out["messages"].append({"role": "assistant", "content": out["response"]})
    
    # user_input이 제대로 반환되도록 보장
    out["user_input"] = new_text
    
    # 세션 상태 업데이트
    _SESSIONS[sid] = out
    return out

