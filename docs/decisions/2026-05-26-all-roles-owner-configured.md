# ADR: 所有角色都是 Owner 配置(方案 Y)

- **日期**:2026-05-26
- **状态**:已接受
- **关联修订**:v2.4(主文档 B 域 + spec A.2 / A.3 / A.4)
- **触发问题**:Owner 提问"会预设 reviewer 角色的原因是什么?角色应该是用户运行时配置定义的么?"

---

## 决策

**所有角色(包括 PM)都是 Owner 配置,framework 不预设任何角色**。

framework 唯一硬约束:`project.yaml` 里恰好一个角色标 `is_orchestrator: true`(担任 PM 职责,状态机入口指向它)。

删除原 spec 里 `required: true/false` 标记(本质是 framework 半固定角色,跟第 5 条宪法"Owner 配置不固定数量"自相矛盾)。

---

## 上下文

v2.0 把固定 4 角色范式改成动态角色,宪法第 5 条原话:
> 角色由 Owner 配置,不固定数量
> role.yaml + system_prompt.md 即可注册新角色

但 v2.0-v2.3 没改干净:
- spec A.2 目录把 `roles/pm/`、`roles/developer/`、`roles/reviewer/`、`roles/architect/` 预建
- spec A.3.5 project.yaml 里 PM/Developer/Reviewer 标 `required: true`
- 主文档 D 域出现"V1 内置的"措辞

Owner 在 v2.4 讨论时发现这个不一致。

---

## 论据

### 为什么不能半固定

- 半固定违反"系统不懂业务"原则。PM 跟 Developer/Reviewer 一样是"做事的角色",系统不该预设
- 加新角色(SecurityReviewer / DBA / Tester)的体验跟"必需角色"不一致(必需的特权配置 vs 可选的从模板拷贝)
- 长期看,Owner 想完全自定义角色组(比如"评审型项目":只配 Architect + Reviewer + Editor,完全没 Developer),半固定挡住这条路

### 为什么需要 `is_orchestrator`

虽然角色全 Owner 配,但**状态机有入口**——必须有一个角色出 dispatch_plan,否则 DISPATCH 循环跑不起来。`is_orchestrator: true` 标记的就是这个入口角色。

不叫"PM",叫 `is_orchestrator`,因为:
- 强调**职责**(出 dispatch_plan),不强调**名字**
- Owner 可以叫它"Coordinator"、"Planner"、"Project Lead",任何名字都行,只要标 is_orchestrator

### 为什么是"恰好一个"

- 0 个 → 状态机没入口,系统不知道从哪开始 → 拒绝启动
- 多个 → 调用顺序歧义 → 拒绝启动

恰好一个是结构性约束,不是"业界标配"。

---

## 实施

### 目录改动

**之前(v2.3)**:
```
agent-org/roles/
  ├── _template/      # 通用模板
  ├── pm/             # 预建,必需
  ├── developer/      # 预建,必需
  ├── reviewer/       # 预建,必需
  └── architect/      # 预建,可选
```

**之后(v2.4 方案 Y)**:
```
agent-org/examples/role_templates/    # framework 参考模板(不是内置)
  ├── _template/                       # 通用模板
  ├── pm/                              # 参考实现(可拷贝改)
  ├── developer/                       # 参考实现
  ├── reviewer/                        # 参考实现
  └── architect/                       # 参考实现

agent-org/projects/<project>/         # 用户项目实例
  ├── project.yaml                     # 含 is_orchestrator: true 的角色
  ├── dispatch_policy.yaml
  └── roles/                           # 该项目实际用的角色(Owner 配)
      ├── pm/                          # 从 examples/role_templates/pm/ 拷过来
      ├── developer/
      └── reviewer/
```

### project.yaml 改动

**之前**:
```yaml
roles:
  - role_id: pm
    required: true
  - role_id: developer
    required: true
  - role_id: reviewer
    required: true
  - role_id: architect
    required: false
```

**之后**:
```yaml
roles:
  - role_id: pm
    is_orchestrator: true              # 恰好一个
  - role_id: developer
  - role_id: reviewer
  - role_id: architect
```

### schemas 改动

- `role.schema.json`:加 `is_orchestrator: boolean`
- `project.schema.json`:加约束"恰好一个 role 标 is_orchestrator: true"

### 同步删除

- 主文档 D 域"V1 内置的还是 Owner 后加的"措辞(v2.0 没改干净的残留)

---

## 不做什么

- 不为了"开箱即用"保留 `required: true`(违反第 5 条宪法)
- 不把 PM 提升到 framework(主文档原意不是这样,PM 是"特殊职责的角色")
- 不引入"角色继承"机制(过度抽象,V1 不需要)

---

## 修订风险

- Owner 第一次配项目可能不知道怎么开始 → 用 `examples/role_templates/` 兜底,Owner 拷贝就行
- 配错 is_orchestrator 数量 → schema 校验失败,系统拒绝启动,error message 提示

---

## 关联文档

- `constitution.md` 第 5 条
- `docs/autonomous-agent-system-design.md` B 域"角色配置"
- `docs/phase-0-1-execution-spec.md` A.2 目录 + A.3.5 project.yaml + A.4 完成标准
- `docs/design-history.md` v2.4 修订日志 + Part IV 已否决清单(`required: true/false 标记角色"必需"`)
