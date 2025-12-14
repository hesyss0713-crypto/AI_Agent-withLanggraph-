from app.graph import build_app
from app.state import AgentState


if __name__ == "__main__":
    try:
        app = build_app()

        init_state: AgentState = {"user_input": "오늘 테슬라 주가 확인해봐"}
        result = app.invoke(init_state)
        print(f"Final Intent: {result.get('final_intent')}")
        print(f"Web Data: {result.get('web_data')}")
        print(f"LLM Output: {result.get('llm_output')}")

    except FileNotFoundError as e:
        print(f"\n오류: {e}")
        print("코드 실행 전에 app/config/prompts.yaml 파일을 생성해야 합니다.")
    except Exception as e:
        print(f"\n실행 중 오류 발생: {e}")
