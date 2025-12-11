from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END

import re
import yaml
from pathlib import Path
import json

#Utility & Prompt Management

# prompt loader
class PromptLoader:
    def __init__(self, path: str = "./prompts.yaml"):
        self.path = Path(path)

    def get(self, key: str) -> str:
        with open(self.path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get(key, {}).get("system", "")
    
# State Definition

@dataclass
class State:
    """LangGraph의 상태를 정의합니다."""
    model: Optional[AutoModelForCausalLM] = field(default=None, repr=False)
    tokenizer: Optional[AutoTokenizer] = field(default=None, repr=False)
    user_input: Optional[str] = None

    # Routing Fields (Source Router 결과)
    source: Optional[str] = None
    source_conf: Optional[float] = 0.0
    
    # Aggregator / Final Decision
    final_source: Optional[str] = None
    final_intent: Optional[str] = None 
    
    # Data Fields (Agent 실행 결과)
    web_data: Optional[str] = None
    code_data: Optional[str] = None
    policy_data: Optional[str] = None
    
    # Final Output
    llm_output: Optional[str] = None

    def extract_json(self, text: str):
        """LLM 출력에서 가장 마지막 JSON 블록만 안전하게 추출"""
        matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)

        if not matches:
            raise ValueError(f"JSON not found in output:\n{text}")

        json_candidate = matches[-1]  # 가장 마지막 JSON 선택

        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON Decode Failed: {e}\nCandidate JSON:\n{json_candidate}\nFull Output:\n{text}"
            )


    def run_llm(self, system_prompt: str, user_prompt: str, max_tokens=512) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        tok = self.tokenizer
        model = self.model

        chat_text = tok.apply_chat_template(
            messages,
            tokenize=False,           
            add_generation_prompt=True
        )

        inputs = tok(
            chat_text,
            return_tensors="pt"
        ).to(model.device)

        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )

        output_text = tok.decode(output_ids[0], skip_special_tokens=True)

        return output_text



# Nodes (Agents)

# Node: Load main llm (초기 LLM 로드)
def load_llm_node(state: State) -> State:
    model_id = "meta-llama/Llama-3.2-3B-Instruct" 
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    state.model = model
    state.tokenizer = tokenizer
    return state

# Node Factory: Source Router
def make_source_router(prompt_loader):
    def source_router(state: State) -> State:
        system_prompt = prompt_loader.get("source_router")
        raw_json_data = state.run_llm(system_prompt, state.user_input)
        
        # JSON 추출 및 상태 업데이트
        data = state.extract_json(raw_json_data)
        state.source = data.get("source", "general")
        state.source_conf = float(data.get("confidence", 0.0))
        return state
    return source_router

# Node Factory: Aggregator Router (규칙 기반 Intent 확정 및 Fallback)
def make_agg_router():
    CONFIDENCE_GATE = 0.35
    
    # 8가지 세부 Intent 결정을 위한 키워드 맵
    INTENT_KEYWORDS = {
        # Web Intents 
        "fetch_news": ["뉴스", "headline", "기사"],
        "fetch_stocks": ["주식", "market", "종목"],
        "fetch_jobs": ["채용", "공고", "일자리"],
        # Code Intents 
        "review_code": ["review", "검토", "버그", "보안"],
        "explain_code": ["설명", "구조", "함수"],
        "refactor_code": ["수정", "리팩터", "변경"],
        # Policy Intents 
        "check_violation": ["규정", "위반", "정책"],
        "summarize_policy": ["요약", "문서", "RAG"],
    }
    
    def agg_router(state: State) -> str: 
        source_conf = state.source_conf or 0.0
        
        # Low conf => Source LLM 신뢰도 검증 (Fallback 트리거)
        if source_conf < CONFIDENCE_GATE:
            state.final_intent = "general_lookup"
            state.final_source = "general"
            return state.final_intent
        
        # High conf => LLM의 Source 결정 채택 및 규칙 기반 Intent 확정
        state.final_source = state.source
        text = state.user_input.lower()
        
        determined_intent = "general_lookup"
        
        # 3. 규칙 기반 Intent
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(k in text for k in keywords):
                if state.final_source == "web" and intent.startswith("fetch"):
                    determined_intent = intent
                    break
                elif state.final_source == "code" and intent.endswith("code"):
                    determined_intent = intent
                    break
                elif state.final_source == "policy" and intent.endswith("policy"):
                    determined_intent = intent
                    break
        
        state.final_intent = determined_intent
        return state

    return agg_router

# Node: Web agent 
def web_agent(state: State) -> State:
    # final_intent를 사용하여 세부 동작 수행 (fetch_news, fetch_stocks 등)
    if state.final_intent == "fetch_news":
        state.web_data = "[Web API] 오늘의 주요 뉴스를 가져왔습니다."
    elif state.final_intent == "fetch_stocks":
        state.web_data = "[Web API] 현재 시장 주식 정보를 가져왔습니다."
    elif state.final_intent == "fetch_jobs":
        state.web_data = "[Web API] 최신 채용 공고를 가져왔습니다."
    else:
        state.web_data = "[Web API] 웹 검색 결과가 없습니다."
    return state

# Node: Code agent 
def code_agent(state: State) -> State:
    if state.final_intent == "review_code":
        state.code_data = "[Code Tool] 사내 표준에 따라 코드를 검토했습니다."
    elif state.final_intent == "explain_code":
        state.code_data = "[Code Tool] 요청하신 함수 구조를 분석 및 설명했습니다."
    elif state.final_intent == "refactor_code":
        state.code_data = "[Code Tool] 요청에 따라 코드를 수정했습니다."
    else:
        state.code_data = "[Code Tool] 코드 분석에 실패했습니다."
    return state

# Node: Policy agent
def policy_agent(state: State) -> State:
    if state.final_intent == "check_violation":
        state.policy_data = "[RAG Tool] 규정 위반 여부를 확인했습니다."
    elif state.final_intent == "summarize_policy":
        state.policy_data = "[RAG Tool] 요청하신 문서 내용을 요약했습니다."
    else:
        state.policy_data = "[RAG Tool] 규정 문서 검색에 실패했습니다."
    return state

# Node Factory: Supervisor Agent
def make_supervisor(prompt_loader):
    def supervisor(state: State) -> State:
        system_prompt = prompt_loader.get("supervisor")
        
        # 이전 Agent의 실행 결과 데이터를 user_prompt에 포함
        context_data = {
            "web_data": state.web_data,
            "code_data": state.code_data,
            "policy_data": state.policy_data,
            "original_query": state.user_input,
            "final_intent": state.final_intent
        }
        
        user_prompt = f"Original Query: {state.user_input}\nContext Data: {json.dumps(context_data, ensure_ascii=False)}"
        
        out = state.run_llm(system_prompt, user_prompt, max_tokens=512)
        state.llm_output = out
        return state
    return supervisor


# Graph Definition
def build_app():
    graph = StateGraph(State)
    prompt_loader = PromptLoader("./prompts.yaml")
    
    # 노드 정의
    graph.add_node("load_llm", load_llm_node)
    graph.add_node("source_router", make_source_router(prompt_loader))
    graph.add_node("agg_router", make_agg_router())
    graph.add_node("supervisor", make_supervisor(prompt_loader))
    graph.add_node("web_agent", web_agent)
    graph.add_node("policy_agent", policy_agent)
    graph.add_node("code_agent", code_agent)

    # 간선
    graph.add_edge("load_llm", "source_router")
    graph.add_edge("source_router", "agg_router") 

    # 조건부 라우팅
    graph.add_conditional_edges(
        "agg_router",
        lambda state: state.final_intent,
        {
            "fetch_news": "web_agent", 
            "fetch_stocks": "web_agent",
            "fetch_jobs": "web_agent",
            
            "review_code": "code_agent", 
            "explain_code": "code_agent",
            "refactor_code": "code_agent",

            "check_violation": "policy_agent", 
            "summarize_policy": "policy_agent",
            
            "general_lookup": "supervisor", # Fallback 경로
        }
    )
    
    # 3. 실행 노드 -> Supervisor (결과 합성)
    graph.add_edge("web_agent", "supervisor")
    graph.add_edge("code_agent", "supervisor")
    graph.add_edge("policy_agent", "supervisor")
    
    # 4. Supervisor -> END
    graph.add_edge("supervisor", END)

    graph.set_entry_point("load_llm")
    
    return graph.compile()

# TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE #  
# TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # 
# TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # # TEST CODE # 

if __name__ == "__main__":
    # 테스트 코드 실행 전, prompts.yaml 파일을 생성해야 합니다.
    try:
        app = build_app()
        
        print("--- 테스트: 오늘 주식 정보를 알려줘 ---")
        init_state_1 = State(user_input="오늘의 주요 주식 시장 상황을 알려줘.")
        result_1 = app.invoke(init_state_1) 
        print(f"Final Intent: {result_1['final_intent']}")
        print(f"Web Data: {result_1['web_data']}")
        print(f"LLM Output: {result_1['llm_output']}")
        
    except FileNotFoundError as e:
        print(f"\n오류: {e}")
        print("코드 실행 전에 prompts.yaml 파일을 생성해야 합니다.")
    except Exception as e:
        print(f"\n실행 중 오류 발생: {e}")