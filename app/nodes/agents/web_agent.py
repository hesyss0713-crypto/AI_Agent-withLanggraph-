from typing import Callable, Dict
from app.state import AgentState, extract_json


def make_stock_handler(run_llm: Callable, get_prompt: Callable, stock_client: Callable):
    def handle(state: AgentState) -> AgentState:
        system_prompt = get_prompt("stock_api")
        raw = run_llm(system_prompt, state["user_input"])
        print(f"[RAW] : {raw}")
        params = extract_json(raw)
        print(f"[params] : {params}")

        try:
            api_result = stock_client(params)
            print(f"[API_RESULT] : {api_result}")
            return {"web_data": f"[Stock API] {params.get('q')}: {api_result}"}
        except Exception as e:
            return {"web_data": f"[Stock API] 호출 실패: {e}"}

    return handle


def make_simple_handler(message: str):
    def handle(state: AgentState) -> AgentState:
        return {"web_data": message}

    return handle


def make_web_agent(
    run_llm: Callable,
    prompt_getter: Callable,
    handlers: Dict[str, Callable[[AgentState], AgentState]],
):
    def web_agent(state: AgentState) -> AgentState:
        intent = state.get("final_intent")
        handler = handlers.get(intent)
        if handler:
            return handler(state)
        return {"web_data": "[Web API] 웹 검색 결과가 없습니다."}

    return web_agent
