# st_app/graph/nodes/subject_info_node.py
import json, os, re
from st_app.rag.llm import chat
from st_app.rag.prompt import get_subject_prompt

SUBJECTS_PATH = "st_app/db/subject_information/subjects.json"

def _load_subjects():
    try:
        if not os.path.exists(SUBJECTS_PATH):
            raise FileNotFoundError(f"제품 정보 파일을 찾을 수 없습니다: {SUBJECTS_PATH}")
        
        with open(SUBJECTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"제품 정보 로드 실패: {e}")
        return []

def _pick_subject(user_input: str, subjects):
    if not subjects:
        return None
        
    text = user_input.lower()
    print(f"[SUBJECT_NODE] Searching for product in: '{text}'")
    
    for item in subjects:
        # 더 다양한 키워드 매칭
        keys = [
            item.get("id", ""),
            item.get("name", ""),
            *(item.get("popular_variants", []) or []),
            *(item.get("key_features", []) or [])
        ]
        
        # 부분 매칭도 허용 (예: "콜라" -> "코카콜라")
        for key in keys:
            if key and str(key).lower() in text:
                print(f"[SUBJECT_NODE] Found product: {item.get('name')}")
                return item
            # 역방향 매칭도 시도 (사용자 입력이 제품명에 포함되는지)
            if key and text in str(key).lower():
                print(f"[SUBJECT_NODE] Found product (reverse): {item.get('name')}")
                return item
    
    print(f"[SUBJECT_NODE] No product found in user input")
    return None

def _render_subject_context(item: dict) -> str:
    if not item: return ""
    lines = []
    lines.append(f"제품명: {item.get('name','')}")
    lines.append(f"카테고리: {item.get('category','')}")
    lines.append(f"제조사: {item.get('manufacturer','')}")
    lines.append(f"원산지: {item.get('origin_country','')}")
    if v:=item.get("volume"): lines.append(f"용량: {v}")
    if nut:=item.get("nutrition"): lines.append(f"영양성분: " + ", ".join([f"{k}:{v}" for k,v in nut.items()]))
    if ing:=item.get("ingredients"): lines.append(f"성분: {', '.join(ing)}")
    if feat:=item.get("key_features"): lines.append("특징: " + "; ".join(feat))
    if pv:=item.get("popular_variants"): lines.append("대표 버전: " + ", ".join(pv))
    return "\n".join(lines)

def subject_info_node(state):
    try:
        user_q = state["user_input"]
        subjects = _load_subjects()
        
        if not subjects:
            state["response"] = "제품 정보를 불러올 수 없습니다."
            return state
            
        # user_input에서 제품 찾기 시도
        item = _pick_subject(user_q, subjects)
        
        # user_input에서 못 찾았으면 last_product 사용
        if not item:
            last_product = state.get("last_product")
            if last_product:
                print(f"[SUBJECT_NODE] Using last_product: {last_product}")
                # last_product로 제품 찾기
                for subject_item in subjects:
                    if (subject_item.get("name", "").lower() == last_product.lower() or 
                        last_product.lower() in subject_item.get("name", "").lower()):
                        item = subject_item
                        break
        
        if not item:
            print(f"[SUBJECT_NODE] No product found for: '{user_q}' or last_product: '{state.get('last_product')}'")
            # 제품을 찾지 못했을 때 맥락을 고려한 응답
            last_product = state.get("last_product")
            if last_product:
                state["response"] = f"'{last_product}'에 대한 건강 정보를 찾을 수 없습니다. 구체적인 제품명을 말씀해 주시거나, 다른 제품에 대해 질문해 주세요."
            else:
                state["response"] = "어떤 제품에 대한 정보를 원하시나요? 구체적인 제품명을 말씀해 주시면 자세한 정보를 알려드릴 수 있습니다."
            return state
            
        print(f"[SUBJECT_NODE] Using product: {item.get('name', 'Unknown')}")
        subject_ctx = _render_subject_context(item)

        # 대화 맥락을 고려한 프롬프트
        last_intent = state.get("last_intent", "chat")
        last_product = state.get("last_product")
        
        context_info = ""
        if last_product and last_product != item.get('name'):
            context_info += f"\n사용자가 이전에 언급한 제품: {last_product}"
        if last_intent != "subject":
            context_info += f"\n직전 대화 의도: {last_intent}"

        system = f"""당신은 제품 정보를 알려주는 도우미입니다.

**답변 방식:**
1. 제공된 제품 정보만 사용해주세요 - 외부 지식은 사용하지 마세요
2. 한국어로 자연스럽게 대화하듯 답변해주세요
3. 정보가 풍부하고 도움이 되도록 답변해주세요
4. 건강/안전에 대한 질문이 있으면 데이터에서 상세한 사실 정보를 제공해주세요
5. 적절할 때는 성분, 영양 정보, 주요 특징 등을 포함해주세요
6. 4-6문장 정도로 충분한 정보를 제공해주세요
7. 너무 형식적이지 말고 자연스러운 대화체로 답변해주세요
8. 사용자의 질문 맥락을 고려해서 관련 정보를 제공해주세요

**현재 맥락:**{context_info}

**주의사항:** 정보를 이해하기 쉽게, 사용자 질문과 관련성 있게, 그리고 정말 도움이 될 수 있도록 충분히 상세하게 답변해주세요. 자연스러운 대화를 나누는 것처럼 답변해주세요."""
        
        user = f"[Product Basic Information]\n{subject_ctx}\n\n[User Question]\n{user_q}"
        ans = chat(system=system, user=user, temperature=0.3, max_tokens=800)
        state["response"] = ans
        
    except Exception as e:
        state["response"] = f"제품 정보 조회 중 오류가 발생했습니다: {str(e)}"
    
    return state
