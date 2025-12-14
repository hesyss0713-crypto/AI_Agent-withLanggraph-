from langgraph.graph import StateGraph, END

from app.state import AgentState
from app.nodes.llm import load_llm, make_llm_runner
from app.nodes.routing import make_source_router, make_agg_router
from app.nodes.agents import web_agent, code_agent, policy_agent, make_supervisor
from app.config import get_prompt, load_routing_rules


def build_app(model_id: str = "meta-llama/Llama-3.2-3B-Instruct"):
    tokenizer, model = load_llm(model_id)
    run_llm = make_llm_runner(tokenizer, model)
    keyword_rules = load_routing_rules()

    graph = StateGraph(AgentState)

    # 노드 정의
    graph.add_node("source_router", make_source_router(get_prompt, run_llm))
    graph.add_node("agg_router", make_agg_router(keyword_rules))
    graph.add_node("supervisor", make_supervisor(get_prompt, run_llm))
    graph.add_node("web_agent", web_agent)
    graph.add_node("policy_agent", policy_agent)
    graph.add_node("code_agent", code_agent)

    # 간선
    graph.add_edge("source_router", "agg_router")

    # 조건부 라우팅
    graph.add_conditional_edges(
        "agg_router",
        lambda state: state["final_intent"],
        {
            "fetch_news": "web_agent",
            "fetch_stocks": "web_agent",
            "fetch_jobs": "web_agent",
            "review_code": "code_agent",
            "explain_code": "code_agent",
            "refactor_code": "code_agent",
            "check_violation": "policy_agent",
            "summarize_policy": "policy_agent",
            "general_lookup": "supervisor",
        },
    )

    # 실행 노드 -> Supervisor (결과 합성)
    graph.add_edge("web_agent", "supervisor")
    graph.add_edge("code_agent", "supervisor")
    graph.add_edge("policy_agent", "supervisor")

    # Supervisor -> END
    graph.add_edge("supervisor", END)

    graph.set_entry_point("source_router")

    return graph.compile()
