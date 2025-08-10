from typing import Dict, Any, List, Optional, TypedDict, Literal

class ChatState(TypedDict, total=False):
    session_id: Optional[str]
    user_input: str
    response: str
    route: Literal["chat", "subject", "review"]
    context_lines: List[str]
    sources: List[Dict[str, Any]]
    messages: List[Dict[str, str]]

    # --- 메모리 슬롯 ---
    last_intent: Literal["chat", "subject", "review"]
    last_product: Optional[str]
    last_category: Optional[str]

def initial_state() -> ChatState:
    return {
        "session_id": None,
        "user_input": "",
        "response": "",
        "route": "chat",
        "context_lines": [],
        "sources": [],
        "messages": [],
        "last_intent": "chat",
        "last_product": None,
        "last_category": None,
    }

def append_user_message(state: ChatState, content: str) -> None:
    state.setdefault("messages", []).append({"role": "user", "content": content})

def append_assistant_message(state: ChatState, content: str) -> None:
    state.setdefault("messages", []).append({"role": "assistant", "content": content})
