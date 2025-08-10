from st_app.rag.llm import chat
from st_app.rag.prompt import get_chat_prompt

def chat_node(state):
    """기본 대화 또는 사후 정리 역할.
    - route=="chat": 일반 대화
    - 그 외(route=="subject"/"review"): 이전 노드 response를 그대로 반환(라이트한 마무리)
    """
    route = state.get("route", "chat")
    if route == "chat":
        prompt = get_chat_prompt()
        user = prompt.format(question=state["user_input"])
        
        system = "You are a friendly Korean-speaking chatbot. Assist the user with casual conversation, greetings, and guidance on available functions in a concise manner. Always use polite Korean language (존댓말). Always respond in Korean."
        ans = chat(system=system, user=user, temperature=0.4, max_tokens=512)
        state["response"] = ans
        return state
    else:
        system = "You are an assistant that reformats text into concise, polite Korean (2-3 sentences)."
        user = f"다음 내용을 공손하고 간결하게 정리:\n\n{state.get('response','')}"
        ans = chat(system=system, user=user, temperature=0.2, max_tokens=256)
        state["response"] = ans
        return state
