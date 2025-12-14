from app.state import AgentState


def policy_agent(state: AgentState) -> AgentState:
    if state["final_intent"] == "check_violation":
        policy_data = "[RAG Tool] 규정 위반 여부를 확인했습니다."
    elif state["final_intent"] == "summarize_policy":
        policy_data = "[RAG Tool] 요청하신 문서 내용을 요약했습니다."
    else:
        policy_data = "[RAG Tool] 규정 문서 검색에 실패했습니다."
    return {"policy_data": policy_data}
