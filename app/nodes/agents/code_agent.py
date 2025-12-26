from app.state import AgentState
from typing import Callable, Optional, Dict
import re
import json
import subprocess
from pathlib import Path
import ast

ALLOWED = {"excution_code", "refactor_code"}

# ============================================================
# Normalization
# ============================================================
def _normalize_command(cmd: Optional[str]) -> str:
    cmd = (cmd or "").strip().lower()

    # 실행 계열
    if cmd in {"run", "execute", "execution", "excute", "exec"}:
        return "excution_code"

    # 리팩토링/수정 계열
    if cmd in {"refactor", "rewrite", "revise", "modify", "edit", "patch", "fix"}:
        return "refactor_code"

    return cmd


# ============================================================
# Robust parsing helpers
# ============================================================
def _strip_python_repr_if_needed(text: str) -> str:
    """
    입력이 "'...'" 처럼 파이썬 repr 문자열(이스케이프 포함)로 들어오는 케이스 복원.
    예: raw = "'system\\n...{...}'"
    """
    t = (text or "").strip()
    if len(t) >= 2 and t[0] in ("'", '"') and t[-1] == t[0]:
        try:
            return ast.literal_eval(t)
        except Exception:
            return text
    return text


def _after_last_assistant(text: str) -> str:
    """
    프롬프트 내부 예제 JSON을 피하기 위해 마지막 'assistant' 이후만 파싱 대상으로.
    """
    if not text:
        return ""
    idx = text.rfind("\nassistant")
    if idx == -1:
        idx = text.rfind("assistant")
    return text[idx:] if idx != -1 else text


def _salvage_json_object_fragment(tail: str) -> Optional[dict]:
    """
    tail에서 마지막 '{'부터 끝까지를 JSON 후보로 보고,
    - 코드펜스/꼬리 쓰레기 제거
    - 부족한 '}' 채우기
    - trailing comma 제거
    후 json.loads 시도.
    """
    if not tail:
        return None

    i = tail.rfind("{")
    if i == -1:
        return None

    frag = tail[i:].strip()

    # 코드펜스 제거(있을 수 있는 케이스 방어)
    frag = frag.replace("```json", "").replace("```", "").strip()

    # 흔한 꼬리 쓰레기 제거 (예: 마지막에 "'" 또는 '"'가 붙는 케이스)
    frag = frag.rstrip(" \t\r\n'\"")

    # 닫는 중괄호 부족분 채우기
    diff = frag.count("{") - frag.count("}")
    if diff > 0:
        frag += "}" * diff

    # trailing comma 제거: { "a": 1, } 같은 케이스
    frag = re.sub(r",\s*([}\]])", r"\1", frag)

    try:
        obj = json.loads(frag)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _regex_fallback_extract(tail: str) -> Optional[Dict[str, str]]:
    """
    JSON 파싱이 실패할 때의 최후 수단:
    "path", "command", "content" 값만 정규식으로 추출.
    """
    def pick(key: str) -> Optional[str]:
        m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', tail)
        return m.group(1) if m else None

    path = pick("path")
    command = pick("command")
    content = pick("content") or ""

    if path and command:
        return {"path": path, "command": command, "content": content}
    return None


def extract_last_path_command(text: str) -> dict:
    """
    1) 입력이 파이썬 repr 문자열이면 복원
    2) 마지막 assistant 이후만 대상
    3) 미완성 JSON 복구 파싱 시도
    4) 실패 시 필드 regex fallback
    """
    text = _strip_python_repr_if_needed(text)
    tail = _after_last_assistant(text)

    # 1차: JSON 복구 파싱
    obj = _salvage_json_object_fragment(tail)
    if obj:
        path = obj.get("path")
        cmd  = _normalize_command(obj.get("command"))
        content = obj.get("content", "")

        if isinstance(path, str) and cmd in ALLOWED:
            return {"path": path, "command": cmd, "content": content}

    # 2차: regex fallback
    fb = _regex_fallback_extract(tail)
    if fb:
        fb_cmd = _normalize_command(fb.get("command"))
        if fb_cmd in ALLOWED and isinstance(fb.get("path"), str):
            fb["command"] = fb_cmd
            return fb

    raise ValueError("No valid {path, command} found in last assistant output.")


# ============================================================
# File operations
# ============================================================
def execute_file(path: str) -> str:
    try:
        p = Path(path)
        if not p.is_file():
            return f"파일 실행 중 오류 발생: File not found: {path}"

        result = subprocess.run(
            ["python3", str(p)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"파일 실행 중 오류 발생: returncode={result.returncode}\n{result.stderr}"
        return result.stdout
    except Exception as e:
        return f"파일 실행 중 오류 발생: {e}"


def refactor_file(path: str, content: str) -> str:
    try:
        p = Path(path)
        if not p.is_file():
            return f"파일 리팩토링 중 오류 발생: File not found: {path}"

        p.write_text(content, encoding="utf-8")
        return "파일이 성공적으로 리팩토링되었습니다."
    except Exception as e:
        return f"파일 리팩토링 중 오류 발생: {e}"


# 기존 함수명 호환 (오타 그대로 쓰는 곳이 있으면 유지)
def refact_file(path: str, content: str) -> str:
    return refactor_file(path, content)


# ============================================================
# Agent handler (AgentState에 맞춤)
# ============================================================
def code_handler(*, run_llm: Callable, get_prompt: Callable, prompt_key: str):
    def handle(state: AgentState) -> AgentState:
        system_prompt = get_prompt(prompt_key)

        # user_input이 없을 가능성도 있으니 방어
        user_input = state.get("user_input", "")
        raw = run_llm(system_prompt, user_input)

        try:
            json_value = extract_last_path_command(raw)
        except Exception as e:
            # Code Agent 결과는 code_data에 기록
            state["code_data"] = f"파싱 실패: {e}\nraw={raw}"
            return state

        cmd = json_value["command"]
        path = json_value["path"]

        if cmd == "excution_code":
            result = execute_file(path)
        elif cmd == "refactor_code":
            result = refact_file(path, json_value.get("content", ""))
        else:
            result = f"지원하지 않는 command: {cmd}"

        # Code Agent 결과는 code_data에 기록
        state["code_data"] = "code result is: "+result
        return state

    return handle


def code_agent(run_llm: Callable, get_prompt: Callable):
    return code_handler(run_llm=run_llm, get_prompt=get_prompt, prompt_key="code")
