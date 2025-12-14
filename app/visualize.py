import random
from dataclasses import dataclass
from typing import Optional
from langgraph.graph.state import CompiledStateGraph


@dataclass
class NodeStyles:
    default: str = (
        "fill:#45C4B0, fill-opacity:0.3, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:bold, line-height:1.2"
    )
    first: str = (
        "fill:#45C4B0, fill-opacity:0.1, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"
    )
    last: str = (
        "fill:#45C4B0, fill-opacity:1, color:#000000, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"
    )


def _random_hex() -> str:
    return f"{random.randint(0, 0xFFFFFF):06x}"


def visualize_graph(
    graph: CompiledStateGraph,
    path: Optional[str] = "graph_output.png",
    xray: bool = False,
    ascii_fallback: bool = True,
) -> Optional[str]:
    """
    CompiledStateGraph를 PNG로 시각화하고 파일 경로를 반환합니다.
    PNG 생성에 실패하면 선택적으로 ASCII를 출력합니다.
    """

    if not isinstance(graph, CompiledStateGraph):
        raise TypeError("visualize_graph expects a CompiledStateGraph.")

    target_path = path or f"graph_output_{_random_hex()}.png"
    g = graph.get_graph(xray=xray)

    try:
        png_bytes = g.draw_mermaid_png(
            background_color="white",
            node_colors=NodeStyles(),
        )
        with open(target_path, "wb") as f:
            f.write(png_bytes)
        return target_path
    except Exception as e:
        print(f"그래프 PNG 생성 실패: {e}")
        if ascii_fallback:
            try:
                print(g.draw_ascii())
            except Exception as ascii_error:
                print(f"ASCII 표시도 실패: {ascii_error}")
    return None
