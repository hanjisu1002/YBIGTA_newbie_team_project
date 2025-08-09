# st_app/rag/llm.py
import os
from typing import Optional
from langchain_upstage import ChatUpstage

DEFAULT_MODEL = "solar-pro"

def get_chat_model(model: Optional[str] = None, api_key: Optional[str] = None) -> ChatUpstage:
    if api_key:
        os.environ["UPSTAGE_API_KEY"] = api_key
    if not (api_key or os.getenv("UPSTAGE_API_KEY")):
        raise RuntimeError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    return ChatUpstage(model=model or DEFAULT_MODEL)

def chat(
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 512,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    llm = get_chat_model(model=model, api_key=api_key).bind(
        temperature=temperature,
        max_tokens=max_tokens,
    )
    msgs = [("system", system), ("human", user)]
    resp = llm.invoke(msgs)
    return resp.content

