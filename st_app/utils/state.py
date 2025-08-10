from typing import Dict, Any, List, Optional, TypedDict, Literal
import uuid
import time

class ChatState(TypedDict, total=False):
    session_id: Optional[str]
    user_input: str
    response: str
    route: Literal["chat", "subject", "review"]
    context_lines: List[str]
    sources: List[Dict[str, Any]]
    messages: List[Dict[str, str]]
    created_at: float  # 세션 생성 시간 추가

    # --- 메모리 슬롯 ---
    last_intent: Literal["chat", "subject", "review"]
    last_product: Optional[str]
    last_category: Optional[str]

def generate_session_id() -> str:
    """고유한 세션 ID를 생성합니다."""
    return str(uuid.uuid4())

def is_session_expired(created_at: float, max_age_hours: int = 24) -> bool:
    """세션이 만료되었는지 확인합니다."""
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    return (current_time - created_at) > max_age_seconds

def initial_state() -> ChatState:
    """새로운 사용자 세션을 위한 초기 상태를 생성합니다."""
    return {
        "session_id": generate_session_id(),
        "user_input": "",
        "response": "",
        "route": "chat",
        "context_lines": [],
        "sources": [],
        "messages": [],
        "created_at": time.time(),
        "last_intent": "chat",
        "last_product": None,
        "last_category": None,
    }

def reset_session_state() -> ChatState:
    """기존 세션을 완전히 초기화합니다."""
    return initial_state()

def append_user_message(state: ChatState, content: str) -> None:
    state.setdefault("messages", []).append({"role": "user", "content": content})

def append_assistant_message(state: ChatState, content: str) -> None:
    state.setdefault("messages", []).append({"role": "assistant", "content": content})
