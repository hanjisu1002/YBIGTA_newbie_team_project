# st_app/graph/nodes/rag_review_node.py
from st_app.rag.llm import chat
from st_app.rag.prompt import get_rag_prompt
from st_app.rag.retriever import load_retriever

def rag_review_node(state):
    """RAG 기반 리뷰 분석 노드"""
    try:
        user_q = state["user_input"]
        retriever = load_retriever(k=3)  
        ctx_lines = retriever.get_relevant_texts(user_q)
        state["context_lines"] = ctx_lines  

        context = "\n- " + "\n- ".join(ctx_lines) if ctx_lines else "(검색 결과 없음)"
        
        # 대화 맥락을 고려한 프롬프트
        last_intent = state.get("last_intent", "chat")
        last_product = state.get("last_product")
        
        context_info = ""
        if last_product:
            context_info += f"\n현재 대화 중인 제품: {last_product}"
        if last_intent != "review":
            context_info += f"\n직전 대화 의도: {last_intent}"
        
        system = f"""당신은 제품 리뷰를 분석해주는 도우미입니다.

**답변 방식:**
1. 제공된 리뷰 내용을 바탕으로 답변해주세요. 하지만 리뷰가 제공되었다는 언급을 하면 안 됩니다.
2. 리뷰에 관련 정보가 있으면 그 내용을 바탕으로 상세히 답변해주세요
3. 리뷰 정보가 부족해도 가능한 한 도움이 되는 답변을 해주세요
4. 한국어로 자연스럽게 대화하듯 답변해주세요
5. 리뷰의 패턴(평점, 공통 테마, 사용자 감정)을 분석해주세요
6. 구체적인 예시가 있으면 포함해주세요
7. 4-6문장 정도로 충분한 정보를 제공해주세요
8. 너무 형식적이지 말고 자연스러운 대화체로 답변해주세요

**현재 맥락:**{context_info}

**주의사항:** "제공된 리뷰로는 확답하기 어렵습니다" 같은 말은 하지 말고, 가능한 한 도움이 되는 답변을 해주세요. 자연스러운 대화를 나누는 것처럼 답변해주세요."""
        
        user = f"[리뷰 내용]\n{context}\n\n[질문]\n{user_q}"
        
        ans = chat(system=system, user=user, temperature=0.3, max_tokens=900)
        state["response"] = ans
        state["sources"] = retriever.search(user_q)["results"]
        
    except Exception as e:
        state["response"] = f"리뷰 분석 중 오류가 발생했습니다: {str(e)}"
        state["context_lines"] = ["오류로 인해 컨텍스트를 불러올 수 없습니다."]
    
    return state
