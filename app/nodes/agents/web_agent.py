from typing import Callable, Dict
from app.state import AgentState, extract_json
from app.services.stocks import format_stock_result
from app.services.news import format_news_result


def make_serpapi_handler(
    *,
    run_llm: Callable,
    get_prompt: Callable,
    prompt_key: str,
    api_client: Callable,
    formatter: Callable,
    failure_prefix: str,
):
    def handle(state: AgentState) -> AgentState:
        system_prompt = get_prompt(prompt_key)
        raw = run_llm(system_prompt, state["user_input"])
        params = extract_json(raw)
        print(f"[PARAMS] : {params}")

        try:
            api_result = api_client(params)
            formatted = formatter(api_result)
            return {"web_data": formatted}
        except Exception as e:
            return {"web_data": f"{failure_prefix} 호출 실패: {e}"}

    return handle


def make_stock_handler(run_llm: Callable, get_prompt: Callable, stock_client: Callable):
    return make_serpapi_handler(
        run_llm=run_llm,
        get_prompt=get_prompt,
        prompt_key="stock_api",
        api_client=stock_client,
        formatter=format_stock_result,
        failure_prefix="[Stock API]",
    )


def make_news_handler(run_llm: Callable, get_prompt: Callable, news_client: Callable):
    return make_serpapi_handler(
        run_llm=run_llm,
        get_prompt=get_prompt,
        prompt_key="news_api",
        api_client=news_client,
        formatter=format_news_result,
        failure_prefix="[News API]",
    )


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
