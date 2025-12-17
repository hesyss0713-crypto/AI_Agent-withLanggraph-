from typing import Dict
from app.state import AgentState, extract_json


def make_source_router(prompt_getter, run_llm):
    def source_router(state: AgentState) -> AgentState:
        system_prompt = prompt_getter("source_router")
        raw_json_data = run_llm(system_prompt, state["user_input"])

        data = extract_json(raw_json_data)
        return {
            "source": data.get("source", "general"),
            "source_conf": float(data.get("confidence", 0.0)),
        }

    return source_router


def make_agg_router(keyword_rules: Dict[str, Dict[str, list]]):
    CONFIDENCE_GATE = 0.35

    def agg_router(state: AgentState) -> AgentState:
        source_conf = float(state.get("source_conf") or 0.0)
        source = state.get("source") or "general"

        if source_conf < CONFIDENCE_GATE:
            return {
                "final_intent": "general_lookup",
                "final_source": "general",
            }

        text = state["user_input"].lower()
        # When the Source Router is confident about the source, we should still route
        # into that source even if no keyword rule matches. Start with a source-level
        # default intent, then optionally refine via keyword matches.
        default_by_source = {
            "web": "fetch_news",
            "code": "explain_code",
            "policy": "summarize_policy",
            "general": "general_lookup",
        }
        determined_intent = default_by_source.get(source, "general_lookup")

        category_rules = keyword_rules.get(source, {})
        for intent, keywords in category_rules.items():
            for kw in keywords:
                if kw.lower() in text:
                    determined_intent = intent
                    break
            if determined_intent != "general_lookup":
                break

        return {
            "final_intent": determined_intent,
            "final_source": source,
        }

    return agg_router
