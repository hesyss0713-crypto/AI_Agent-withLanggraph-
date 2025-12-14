from app.graph import build_app
from app.state import AgentState
from app.visualize import visualize_graph


if __name__ == "__main__":
    try:
        app = build_app()
        try:
            png_path = visualize_graph(app, path="graph_output.png")
            if png_path:
                print(f"그래프가 저장되었습니다: {png_path}")
        except Exception as viz_error:
            print(f"그래프 시각화를 건너뜁니다: {viz_error}")
        user_input = input("무엇을 도와드릴까요?")

        init_state: AgentState = {"user_input": user_input}
        result = app.invoke(init_state)
        print(f"Final Intent: {result.get('final_intent')}")
        print(f"Web Data: {result.get('web_data')}")
        print(f"LLM Output: {result.get('llm_output')}")


    except FileNotFoundError as e:
        print(f"\n오류: {e}")
        print("코드 실행 전에 app/config/prompts.yaml 파일을 생성해야 합니다.")
    except Exception as e:
        print(f"\n실행 중 오류 발생: {e}")
