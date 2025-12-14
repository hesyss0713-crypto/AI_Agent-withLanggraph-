from typing import Annotated, Optional, TypedDict
import re
import json


class AgentState(TypedDict, total=False):
    user_input: str
    source: Annotated[Optional[str], "Source Router 결정"]
    source_conf: Annotated[float, "Source Router 신뢰도 (0~1)"]
    final_source: Annotated[Optional[str], "확정된 데이터 소스"]
    final_intent: Annotated[Optional[str], "규칙 기반 최종 Intent"]
    web_data: Annotated[Optional[str], "Web Agent 결과"]
    code_data: Annotated[Optional[str], "Code Agent 결과"]
    policy_data: Annotated[Optional[str], "Policy Agent 결과"]
    llm_output: Annotated[Optional[str], "Supervisor 최종 답변"]


def extract_json(text: str) -> dict:
    """LLM 출력에서 가장 마지막 JSON 블록만 안전하게 추출"""
    matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)

    if not matches:
        raise ValueError(f"JSON not found in output:\n{text}")

    json_candidate = matches[-1]

    try:
        return json.loads(json_candidate)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON Decode Failed: {e}\nCandidate JSON:\n{json_candidate}\nFull Output:\n{text}"
        )
