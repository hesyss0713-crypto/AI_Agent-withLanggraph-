import json
from app.state import AgentState


def web_agent(state: AgentState) -> AgentState:
    if state["final_intent"] == "fetch_news":
        web_data = "[Web API] 오늘의 주요 뉴스를 가져왔습니다."
    elif state["final_intent"] == "fetch_stocks":
        web_data = "[Web API] 현재 시장 주식 정보를 가져왔습니다."
    elif state["final_intent"] == "fetch_jobs":
        web_data = "[Web API] 최신 채용 공고를 가져왔습니다."
    else:
        web_data = "[Web API] 웹 검색 결과가 없습니다."
    return {"web_data": web_data}


def code_agent(state: AgentState) -> AgentState:
    if state["final_intent"] == "review_code":
        code_data = "[Code Tool] 사내 표준에 따라 코드를 검토했습니다."
    elif state["final_intent"] == "explain_code":
        code_data = "[Code Tool] 요청하신 함수 구조를 분석 및 설명했습니다."
    elif state["final_intent"] == "refactor_code":
        code_data = "[Code Tool] 요청에 따라 코드를 수정했습니다."
    else:
        code_data = "[Code Tool] 코드 분석에 실패했습니다."
    return {"code_data": code_data}


def policy_agent(state: AgentState) -> AgentState:
    if state["final_intent"] == "check_violation":
        policy_data = "[RAG Tool] 규정 위반 여부를 확인했습니다."
    elif state["final_intent"] == "summarize_policy":
        policy_data = "[RAG Tool] 요청하신 문서 내용을 요약했습니다."
    else:
        policy_data = "[RAG Tool] 규정 문서 검색에 실패했습니다."
    return {"policy_data": policy_data}


def make_supervisor(prompt_getter, run_llm):
    def supervisor(state: AgentState) -> AgentState:
        system_prompt = prompt_getter("supervisor")

        context_data = {
            "web_data": state.get("web_data"),
            "code_data": state.get("code_data"),
            "policy_data": state.get("policy_data"),
            "original_query": state["user_input"],
            "final_intent": state.get("final_intent"),
        }

        user_prompt = f"Original Query: {state['user_input']}\nContext Data: {json.dumps(context_data, ensure_ascii=False)}"

        out = run_llm(system_prompt, user_prompt, max_tokens=512)
        return {"llm_output": out}

    return supervisor
