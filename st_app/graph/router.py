# st_app/graph/router.py
from langgraph.graph import StateGraph, END
from st_app.utils.state import ChatState
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node
from st_app.rag.llm import chat as call_llm

ROUTER_SYS = (
    "Decide intent. Output exactly one of: chat, subject, review. No extra words, lowercase."
)

def _routing_node(state: ChatState) -> ChatState:
    try:
        q = state["user_input"]
        user = (
            "[User]\n"
            f"{q}\n\n"
            "Rules:\n- info/spec/brand/category -> subject\n"
            "- review/experience/summary/evaluation -> review\n"
            "- else -> chat"
        )
        out = call_llm(system=ROUTER_SYS, user=user, temperature=0.0, max_tokens=5).strip().lower()
        route = out if out in {"chat","subject","review"} else "chat"
        state["route"] = route
    except Exception as e:
        print(f"라우팅 오류: {e}")
        state["route"] = "chat"
    
    return state

def build_graph():
    g = StateGraph(ChatState)

    g.add_node("router", _routing_node)
    g.add_node("chat_node", chat_node)
    g.add_node("subject_info_node", subject_info_node)
    g.add_node("rag_review_node", rag_review_node)  # k=3은 함수 내부에서 기본값으로 설정

    g.set_entry_point("router")

    g.add_conditional_edges(
        "router",
        lambda s: s.get("route","chat"),
        {
            "chat": "chat_node",
            "subject": "subject_info_node",
            "review": "rag_review_node",
        },
    )

    g.add_edge("subject_info_node", "chat_node")
    g.add_edge("rag_review_node", "chat_node")

    g.add_edge("chat_node", END)

    return g.compile()
