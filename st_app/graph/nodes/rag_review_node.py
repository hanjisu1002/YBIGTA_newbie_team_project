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
        
        system = "You are an assistant that answers based on product reviews. Use only the provided review excerpts as evidence. If the information is insufficient, reply exactly with: '제공된 리뷰로는 확답하기 어렵습니다.' Always respond in Korean. Summarize the core points concisely (2–5 sentences)."
        user = f"[Review Excerpts]\n{context}\n\n[Question]\n{user_q}"
        
        ans = chat(system=system, user=user, temperature=0.2, max_tokens=700)
        state["response"] = ans
        state["sources"] = retriever.search(user_q)["results"]
        
    except Exception as e:
        state["response"] = f"리뷰 분석 중 오류가 발생했습니다: {str(e)}"
        state["context_lines"] = ["오류로 인해 컨텍스트를 불러올 수 없습니다."]
    
    return state
