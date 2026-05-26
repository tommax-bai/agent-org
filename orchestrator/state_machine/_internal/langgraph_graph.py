"""LangGraph 实现状态机(Phase 0C PoC)。

跟自写版 graph.py 等价的状态机,复用所有底层逻辑(dispatcher / roles / artifact / ...)。
唯一不同:节点用 LangGraph StateGraph + conditional_edges,
checkpointer 可选(MemorySaver / SqliteSaver / PostgresSaver)。

通过环境变量 STATE_MACHINE=langgraph 切换。默认 self_written(0B 自写)。

PoC 验证目标:
  ✓ checkpoint 在 long-running 任务能持久化(MemorySaver 即可)
  ✓ 中途 kill 后从 checkpoint 恢复(需 SqliteSaver / PostgresSaver)
  ✓ 节点 timeout(LangGraph 节点天然支持)
  ✓ budget exceeded 硬中断(走条件边到 ESCALATED)
  ✓ event 可以回放(LangGraph 自带 stream replay)
"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from orchestrator._shared import TaskState
from orchestrator.state_machine._internal.graph import (  # 复用底层节点逻辑
    _dispatch_loop,
    _escalate,
    _pm_planning,
)
from orchestrator.event_log import write_event


# ---------- 节点实现(复用 0B graph.py 的内部函数) ----------


def _node_pm_planning(state: TaskState) -> dict[str, Any]:
    ok = _pm_planning(state)
    if not ok:
        # _pm_planning 内部已经 escalate 了 state.status
        pass
    return {"_full_state": state}


def _node_dispatch_loop(state: TaskState) -> dict[str, Any]:
    """LangGraph 版的 DISPATCH 节点。

    设计选择:不把 DISPATCH 拆成多个 LangGraph 节点(role_executing 等),
    因为 0B 的 _dispatch_loop 已经是个完整循环,LangGraph 拆成多节点反而
    破坏现有逻辑。这里把整个 DISPATCH 当作一个节点(里面是循环 + 多次 LLM 调用)。

    Trade-off:checkpoint 颗粒度变粗(只能在 PM_PLANNING / DISPATCH 节点边界
    checkpoint,中途 kill 不能恢复到某个 role 调用之后)。Phase 1 真有需要
    再拆细。
    """
    if state.status != "ESCALATED_TO_OWNER" and state.status != "DONE":
        _dispatch_loop(state)
    return {"_full_state": state}


# ---------- 路由 ----------


def _route_after_pm(state: TaskState) -> Literal["dispatch", "end"]:
    if state.status in ("ESCALATED_TO_OWNER", "BUDGET_EXCEEDED"):
        return "end"
    return "dispatch"


def _route_after_dispatch(state: TaskState) -> Literal["end"]:
    # DISPATCH 循环内部已经走完了,无论哪个终态都直接 END
    return "end"


# ---------- LangGraph 状态:用 dict wrapper 包装 TaskState ----------


class _GraphState(dict):
    """LangGraph 要求 state 是 dict-like 的。把 TaskState 包在 _full_state key 下。

    LangGraph 1.x 接受 TypedDict / Pydantic model 作为 state schema,但跟我们
    现有的 TaskState 直接用更省事 — 用 dict[str, TaskState] 透传。
    """


def build_graph(use_checkpoint: bool = True):
    """构造 LangGraph 图。返回 compiled graph。

    use_checkpoint=True 时用 MemorySaver(进程内持久化,验证 PoC 用)。
    Phase 0C+ 接 PostgresSaver 实现跨进程恢复(需 docker compose up)。
    """
    graph: StateGraph = StateGraph(_GraphState)

    graph.add_node("pm_planning", _node_pm_planning)
    graph.add_node("dispatch", _node_dispatch_loop)

    graph.set_entry_point("pm_planning")
    graph.add_conditional_edges(
        "pm_planning",
        lambda s: _route_after_pm(s["_full_state"]),
        {"dispatch": "dispatch", "end": END},
    )
    graph.add_edge("dispatch", END)

    if use_checkpoint:
        return graph.compile(checkpointer=MemorySaver())
    return graph.compile()


def run_task_langgraph(state: TaskState, thread_id: str | None = None) -> TaskState:
    """LangGraph 版 run_task。等价于自写版 graph.run_task。"""
    write_event(
        state.task.task_id,
        "TASK_CREATED",
        actor="owner",
        payload={"title": state.task.title, "project_id": state.task.project_id},
    )

    app = build_graph(use_checkpoint=True)
    config = {"configurable": {"thread_id": thread_id or state.task.task_id}}
    initial: _GraphState = _GraphState(_full_state=state)
    final: _GraphState = app.invoke(initial, config=config)  # type: ignore[assignment]

    final_state: TaskState = final["_full_state"]

    if final_state.status == "DONE":
        write_event(
            final_state.task.task_id,
            "TASK_COMPLETED",
            actor="orchestrator",
            payload={"total_cost_usd": final_state.cost_used_usd},
        )
    else:
        write_event(
            final_state.task.task_id,
            "TASK_FAILED",
            actor="orchestrator",
            payload={
                "status": final_state.status,
                "reason": final_state.escalation_reason,
                "total_cost_usd": final_state.cost_used_usd,
            },
        )
    return final_state
