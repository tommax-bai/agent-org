# 模块边界纪律(v2.3)

> agent-org 是 **modular monolith**(物理单体,逻辑严格模块化)。
> 严格的模块边界是它跟"耦合腐烂的单体"的根本区别。
>
> 详细见 `docs/autonomous-agent-system-design.md` Part IV 末尾"模块边界保护"段。

---

## 核心规则

### 1. 跨模块 import 必须只用 top-level namespace

```python
# ✅ 允许
from orchestrator.memory import get_relevant_memory
from orchestrator.event_log import write_event

# ❌ 禁止
from orchestrator.memory._internal.store import query
from orchestrator.memory.store import _internal_helper
from orchestrator.event_log._internal.writer import _fast_path
```

`_internal/` 子目录视为模块私有,跨模块禁止访问。

### 2. 需要其他模块的内部细节时,不要直接拿

错误做法:

```python
# dispatcher 想读 memory 的某个 internal table → 直接 SQL 读
from orchestrator.memory._internal.store import _query_recent
```

正确做法:
1. 检查目标模块的 public API 够不够(看它的 `__init__.py`)
2. 不够 → **先改目标模块的 `__init__.py`,export 新方法**
3. 再 import 那个 public API
4. **这一步不能跳过**

### 3. 优先依赖 Protocol,不依赖具体类

```python
# protocols.py 里定义 Protocol
class MemoryStore(Protocol):
    def get_relevant_memory(self, task_id: str) -> list[MemoryItem]: ...

# ✅
def schedule(state, memory: MemoryStore): ...

# ❌
def schedule(state, memory: PostgresMemoryStore): ...
```

V1 阶段不强求 Protocol(避免过度抽象),但**新加跨模块依赖时,考虑能否用 Protocol**。

### 4. 跨模块"快捷方式"是腐烂的开始

- ❌ 不要直接读其他模块的 Postgres 表(走它的 API)
- ❌ 不要直接写其他模块的私有文件(走它的 API)
- ❌ 任何"绕过接口"的设计,先 stop,考虑改 public API

### 5. 改 `__init__.py` / `importlinter.cfg` 必须走 PR

- 这是架构变更,不能在普通代码 PR 里夹带
- PR 描述必须说明"为什么 export 这个 / 为什么改边界"

---

## 模块清单(Phase 0A 骨架)

```
orchestrator/
├── _runtime/          入口层(__main__.py + run loop)
├── state_machine/     状态机模块
├── dispatcher/        DISPATCH 节点逻辑
├── roles/             角色调用框架(不是 role 配置)
├── llm/               LLM 抽象(Anthropic SDK 包装)
├── memory/            记忆访问
├── event_log/         事件存储(0B jsonl,0C+ Postgres)
├── artifact/          产物存储
├── budget/            成本管理
├── escalation/        升级通知
└── _shared/           跨模块基础设施(共享类型)
```

每个模块都有 `__init__.py`(显式 export public API)+ `_internal/`(私有实现)。

## 分层架构

```
_runtime          ← 最上层
   ↓
state_machine
   ↓
dispatcher
   ↓
roles
   ↓
llm
   ↓
memory / event_log / artifact / budget / escalation  (并列,互不依赖)
   ↓
_shared           ← 最下层
```

上层可以调下层,下层不能调上层。`import-linter` 强制。

---

## CI 强制

`importlinter.cfg` 在仓库根目录。CI 跑:

```bash
lint-imports
```

违规 → CI 失败 → PR 被拒。

---

## 遵守规则的好处

- CI 自动拦截违规 import
- V1.5+ 真要拆 service 时,模块可以平滑提取
- 改一处不影响其他模块
- 测试时 mock Protocol,不用起 Postgres

## 违反时会发生什么

- `lint-imports` CI 失败 → PR 被拒
- pre-commit hook 拦截(如有)→ commit 失败
- 即使蒙混过关,后期 review / refactor 时会暴露

---

## v2.3 的最小集

只做三件事:

1. **`_internal/` + `__init__.py`(基础,最重要)** — 是其他保护手段的前提
2. **`coding-subagent-prompt` 加"模块边界纪律"段** — 让 AI 主动遵守
3. **`importlinter.cfg` CI 强制** — 兜底

V1 不做:完整 Protocol/ABC 体系、架构测试、pre-commit hook、模块版本号 / 独立打包。
真出现腐烂模式再加新工具。
