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
    for item in subjects:
        keys = [item.get("id",""), item.get("name",""), *(item.get("popular_variants",[]) or [])]
        if any(k and str(k).lower() in text for k in keys):
            return item
    return subjects[0] if subjects else None

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
            
        item = _pick_subject(user_q, subjects)
        subject_ctx = _render_subject_context(item)

        system = "You are a fact-based product review assistant. Answer ONLY from the provided product basic information. No external knowledge. Always respond in Korean."
        user = f"[Product Basic Information]\n{subject_ctx}\n\n[User Question]\n{user_q}"
        ans = chat(system=system, user=user, temperature=0.2, max_tokens=600)
        state["response"] = ans
        
    except Exception as e:
        state["response"] = f"제품 정보 조회 중 오류가 발생했습니다: {str(e)}"
    
    return state
