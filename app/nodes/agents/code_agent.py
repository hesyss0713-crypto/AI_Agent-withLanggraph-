from app.state import AgentState


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
