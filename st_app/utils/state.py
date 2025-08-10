# st_app/utils/state.py
from typing import Dict, Any, List

def initial_state() -> Dict[str, Any]:
    """그래프에 투입할 기본 상태(dict). 노드들이 공통으로 쓰는 키만 최소 정의."""
    return {
        "session_id": None,
        "user_input": "",     # 이번 턴 사용자의 질문
        "response": "",       # 노드(또는 마무리 chat_node)가 만든 응답
        "route": "chat",      # 'chat' | 'subject' | 'review'
        "context_lines": [],  # RAG에서 뽑힌 텍스트 라인
        "sources": [],        # RAG 검색 결과 원천 메타(있으면)
        "messages": []        # UI에서 렌더링할 대화 로그 [{role, content}]
    }

def append_user_message(state: Dict[str, Any], content: str) -> None:
    state["messages"].append({"role": "user", "content": content})

def append_assistant_message(state: Dict[str, Any], content: str) -> None:
    state["messages"].append({"role": "assistant", "content": content})
