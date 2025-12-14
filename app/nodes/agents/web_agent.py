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
