from st_app.rag.llm import chat
from st_app.rag.prompt import get_chat_prompt

def chat_node(state):
    """기본 대화 또는 사후 정리 역할.
    - route=="chat": 일반 대화
    - 그 외(route=="subject"/"review"): 이전 노드 response를 그대로 반환(라이트한 마무리)
    """
    route = state.get("route", "chat")
    if route == "chat":
        # 대화 맥락을 고려한 프롬프트 구성
        messages = state.get("messages", [])
        last_intent = state.get("last_intent", "chat")
        last_product = state.get("last_product")
        last_category = state.get("last_category")
        
        # 맥락 정보 구성
        context_info = ""
        if last_product:
            context_info += f"\n현재 대화 중인 제품: {last_product}"
        if last_category:
            context_info += f"\n현재 카테고리: {last_category}"
        if last_intent != "chat":
            context_info += f"\n직전 의도: {last_intent}"
        
        # 대화 히스토리에서 최근 3개 메시지만 사용
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        conversation_history = ""
        if recent_messages:
            conversation_history = "\n\n[대화 히스토리]\n" + "\n".join([
                f"{'사용자' if msg['role'] == 'user' else '어시스턴트'}: {msg['content']}"
                for msg in recent_messages
            ])
        
        system = f"""당신은 친근한 한국어 챗봇입니다.

**답변 방식:**
1. 사용자와 자연스러운 대화를 나누고, 인사와 안내를 도와주세요
2. 한국어로 공손하게 답변해주세요
3. 도움이 되고 유용한 제안을 해주세요
4. 2-3문장으로 간결하게 답변해주세요
5. 개성과 따뜻함을 보여주되 전문성을 유지해주세요
6. 대화 맥락과 논의 중인 제품을 고려해주세요
7. 특정 제품에 대해 질문하는 경우 자연스럽게 인정해주세요

**현재 맥락:**{context_info}

**주의사항:** 대화가 자연스럽고 매력적이어야 하며, 단순히 기능적이지 않아야 합니다. 맥락을 활용해서 더 관련성 있는 답변을 제공해주세요."""
        
        user = f"사용자 질문: {state['user_input']}{conversation_history}"
        
        ans = chat(system=system, user=user, temperature=0.4, max_tokens=700)
        state["response"] = ans
        return state
    else:
        # 이 부분은 더 이상 사용되지 않음 (그래프 구조 변경으로)
        system = "You are an assistant that reformats text into concise, polite Korean (2-3 sentences)."
        user = f"다음 내용을 공손하고 간결하게 정리:\n\n{state.get('response','')}"
        ans = chat(system=system, user=user, temperature=0.2, max_tokens=256)
        state["response"] = ans
        return state
