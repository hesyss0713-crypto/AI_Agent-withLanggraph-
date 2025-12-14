import json
from app.state import AgentState


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
