"""角色调用框架(role_invocation_protocol 的执行)。

不是 role 配置(那是 examples/role_templates/ + projects/<x>/roles/)。
这里是"调用 role 的代码"。

Phase 0B 阶段:
- PMRunner: 真实 Claude API(只有 PM)
- MockRunner: 返回符合 schema 的 mock 数据(其他角色)
Phase 1 起全切真实 LLM。
"""

from orchestrator.roles._internal.factory import make_runner
from orchestrator.roles._internal.protocol import RoleExecutionError, RoleRunner

__all__ = ["RoleRunner", "RoleExecutionError", "make_runner"]
