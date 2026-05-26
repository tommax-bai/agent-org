# V1 部署决策

> **文档定位**:V1 阶段在哪里跑、怎么跑的关键决策
>
> **不是**:详细部署手册(那是 Phase 0C 才写)
>
> **配套文档**:autonomous-agent-system-design.md v2.2

---

## 1. V1 部署目标

```text
预期负载:每天 3 个任务,单人使用
运行时长:24/7(任务可能在你不在时跑完)
数据持久化:Postgres(state + memory + events)
观察工具:Langfuse 自托管
代码隔离:Git worktree(per task)
LLM 调用:走外网到 api.anthropic.com
```

## 2. 部署模式对比

| 方案 | 月成本 | 上手难度 | 优势 | 劣势 |
|---|---|---|---|---|
| **本地机器** (Mac mini / 旧台式机) | 0(只算电费) | 低 | 完全控制、上手快 | 必须 24/7 开着,关机任务停 |
| **家里 NAS** (群辉 / unRAID) | 0(已有) | 中 | 24/7 已经在跑 | 部分 NAS 资源紧张 |
| **VPS** (Hetzner CX22 / DigitalOcean) | $5-10 | 中 | 稳定、专业 | 数据在外、需要管 SSH |
| **阿里云国内 + 自有代理** | ¥80-150 + 代理 | 中 | 合规、可走公司流程 | 必须维护代理可用性 |
| **阿里云海外 Region** (香港/新加坡) | ¥150-300 | 中 | 可直连 Claude API | 价格高、合规需评估 |
| **国内云裸用(无代理)** | 不可行 | - | - | **api.anthropic.com 不通** |
| **完全云原生** (k8s / managed services) | $50+ | 高 | 企业级 | **严重过度工程**,单人不需要 |

## 3. 推荐方案

**Phase 0A / 0B**:**自己电脑** ← 无需任何服务器

- 这两个 phase 都是文件 + 简单 Python,本地跑就行
- 不需要 24/7,不需要 docker

**Phase 0C 之后**:**按约束分情况**

```text
情况 1:个人项目,无云厂商约束
  优先级:
  1. 24/7 本地机器(Mac mini)→ 用它
  2. 支持 docker 的 NAS → 用它
  3. 都没有 → Hetzner CX22(欧美延迟可接受)
  永远不推荐:k8s / 完全云原生

情况 2:公司约束必须用某家国内云(本项目实际)
  必备:有可用的代理服务(自有 VPS / 公司代理 / bandwagon)
  推荐:阿里云国内 Region + 自有代理
       - ECS 共享型 s6 (2 vCPU + 4 GB) ≈ ¥100-150/月
       - 走代理访问 api.anthropic.com
       - 不推荐 RDS(用自托管 Postgres)
       - 不推荐云监控告警(用 Langfuse + 飞书)
  备选:阿里云海外 Region(可直连,但价格更贵)

情况 3:商业项目对外提供服务
  → 这是另一个项目,不在 V1 范围
```

## 3.5 本项目实际方案(2026-05-25 决定)

```text
约束:
  - 公司要求用阿里云
  - 数据不敏感
  - 自己 root + SSH 维护
  - 使用 bandwagon VPS 作为代理

架构:
  ┌─────────────────────────────────┐
  │ 阿里云 ECS 国内 Region            │
  │  - docker-compose                │
  │  - postgres 14                   │
  │  - langfuse (self-hosted)        │
  │  - orchestrator (Python)         │
  └────────────────┬────────────────┘
                   │ HTTPS_PROXY
                   ↓
  ┌─────────────────────────────────┐
  │ bandwagon VPS(代理服务)          │
  │  - 反向代理 / HTTP 转发           │
  └────────────────┬────────────────┘
                   │
                   ↓
  ┌─────────────────────────────────┐
  │ api.anthropic.com                │
  └─────────────────────────────────┘

ECS 规格:
  - 阶段 0C-1:s6 共享型 (2 vCPU + 4 GB) ≈ ¥100/月
  - 阶段 5(多任务并行):升 g6 (4 vCPU + 8 GB) ≈ ¥250/月

代理配置:
  - bandwagon 已有 VPS(沉没成本,不额外计费)
  - 在 orchestrator 配 HTTPS_PROXY=http://<bandwagon_ip>:<port>
  - 走 HTTPS,Claude 不要看 IP 是 ECS

备份策略:
  - pg_dump 每天 cron → 阿里云 OSS(同 Region,免费流量)
  - 周一次全量,日间增量
  - 阿里云 ECS 快照(月级容灾)

不做的事:
  - 不上阿里云 RDS(自托管 Postgres 够)
  - 不上 ACK / 容器服务(docker-compose 够)
  - 不上 SLB / WAF(单人不暴露公网)
  - 不上云监控告警(用 Langfuse + 飞书)
```

## 4. 各 Phase 部署演进

```text
Phase 0A: 纯文件 + Git
  - 任何能写代码的机器
  - 不需要服务

Phase 0B: 本地 Python 进程
  - Python 3.11+
  - 不需要 Postgres / Langfuse / Git worktree
  - events.jsonl 写本地文件

Phase 0C: docker-compose 起 Postgres + Langfuse
  - 选定的部署目标(本地/NAS/VPS)
  - docker-compose.yml(Postgres + Langfuse)
  - 备份策略生效

Phase 1: 真实 LLM 调用
  - api.anthropic.com 可访问
  - $ANTHROPIC_API_KEY 配置好
  - 不需要新增基础设施

Phase 2: Git worktree
  - 部署目标必须能跑 Git worktree
  - 需要 Node.js (pnpm/yarn) 等项目依赖
  - 磁盘:per task 100MB-500MB worktree

Phase 3: CI 工具
  - gitleaks 安装
  - 项目本身的 CI 命令(test / lint / build)能本地跑
  - GitHub CLI (gh) 配置 SSH key

Phase 4A: 还是 Postgres + Langfuse,不增加新组件
Phase 5: 多任务并行,资源需求略涨
```

## 5. 硬件资源粗估(V1 稳态)

```text
CPU:     2 核(平均 1 核闲置,任务执行时短时 2 核)
内存:    4-8 GB
  - Postgres: ~500 MB
  - Langfuse: ~1 GB
  - orchestrator (Python): ~300 MB
  - worktree 进程 (Claude Code subprocess): 2-3 GB peak
磁盘:    50-100 GB SSD
  - Postgres data: 5-10 GB(events 表是大头)
  - worktree: 10-30 GB(per project 大小 × 并行任务数)
  - Langfuse data: 5-10 GB
  - 日志: 5-10 GB
网络:    任意,但要能连 api.anthropic.com 和 github.com
        国内机器需要代理
```

**Hetzner CX22** (€4.5/月,2 vCPU + 4 GB RAM + 40 GB SSD) 基本够用,Phase 5 多任务并行时可能要升级到 CX32。

## 6. 数据备份策略

```text
真相源:
  - Postgres (task state + memory + events) ← 必备份
  - Git repo (代码 + roles config) ← 必备份
  - runs/ artifacts ← 可选(可从 events 重建)

V1 备份方案(轻量):
  1. Postgres: pg_dump 每天一次 → 本地另一磁盘 / S3 / Backblaze B2
  2. agent-org Git repo: push 到 GitHub (private)
  3. 项目 Git repos: 本来就在 GitHub
  4. runs/ artifacts: 选择性保留最近 30 天

不做的事:
  ❌ 高可用 Postgres replication(单点故障可接受)
  ❌ 实时备份(每天一次够了)
  ❌ 跨区域备份(项目不重要)
```

## 7. 监控告警(V1 极简)

```text
做的:
  ✅ Langfuse dashboard(LLM 调用 + cost)
  ✅ 飞书 webhook 推送(escalation)
  ✅ Postgres 简单查询(失败任务、卡住任务)

不做的:
  ❌ Prometheus / Grafana(过度工程)
  ❌ Alertmanager
  ❌ APM 工具
  ❌ SLI / SLO 跟踪
```

如果系统挂了,Owner 手动看 Langfuse + Postgres 排查。这是单人维护下的正确权衡。

## 8. 运维方式 — Claude subagent 分工

> **关键洞察**:Owner 用 Claude 开发 agent-org 系统,**也用 Claude 运维这套系统**。
> 不做独立的 "ops agent" 软件——开发负担 + 维护负担都太大。
> 用 Claude 的 subagent 功能,把开发上下文和运维上下文**隔离开**。

### 为什么不做独立 ops agent

```text
独立 ops agent 软件:
  ❌ 需要单独开发(1-2 周)
  ❌ 需要单独部署、维护
  ❌ Phase 0C 都还没跑通,做 ops agent 没数据训练 prompt
  ❌ 跟 agent-org 系统循环依赖(系统挂了,运维 agent 也挂)

Claude subagent 方式:
  ✅ 零开发成本
  ✅ 零维护成本
  ✅ 上下文隔离(开发 prompt vs 运维 prompt)
  ✅ Owner in loop(所有实质操作 Owner 自己执行)
  ✅ 系统挂了反而最能用(在 Claude.ai / Desktop)
```

### 两个 subagent 的分工

```text
┌─────────────────────────────────────────┐
│  Coding Subagent (开发 agent-org)        │
│  - 系统设计 / 代码 / schema 修改         │
│  - 12 次修订的设计教训上下文            │
│  - 主文档 v2.2 / spec / history 文件    │
│  - 用于 Phase 0A-1 开发期               │
└─────────────────────────────────────────┘
            (跟主系统开发并行)
┌─────────────────────────────────────────┐
│  Ops Subagent (运维 agent-org)           │
│  - 部署 / 排查 / 监控 / 备份             │
│  - 部署 runbook / 系统架构上下文        │
│  - deployment-decision.md / 配置示例    │
│  - 用于 Phase 0C 部署后日常运维         │
└─────────────────────────────────────────┘
```

两份完整的 system prompt 草稿见 `docs/operations/`:

- `docs/operations/coding-subagent-prompt.md`
- `docs/operations/ops-subagent-prompt.md`

### Owner 使用方式

```text
形态选项:
1. Claude.ai Project(网页 / Desktop / 移动)
   - 每个 subagent = 一个 Project
   - 把对应的 system prompt 贴到 Custom Instructions
   - 把对应的上下文文件传到 Project Files

2. Claude Code subagent(CLI / IDE)
   - 用 Claude Code 的 subagent 功能
   - 各自配置 system prompt + tools

3. 移动场景
   - 紧急时,Claude 移动 App 也能用 Ops subagent
   - 你 SSH 上去,subagent 告诉你跑什么命令
```

### Ops subagent 能做的 / 不能做的

```text
能做:
  ✅ 帮 Owner 诊断系统问题(分析日志 / events / Langfuse 数据)
  ✅ 给出具体的排查步骤(SSH 命令、SQL 查询、log 位置)
  ✅ 解释错误信息
  ✅ 生成运维报告(周报、月报、故障模式总结)
  ✅ 提供升级方案 + rollback 计划
  ✅ 帮写 cron 脚本(备份、清理)

绝不做(V1):
  ❌ 自动 SSH / 自动 kill 任务(Owner 必须 in loop)
  ❌ 自动改 prompt(必须走 B5 角色质量门)
  ❌ 自动改 dispatch_policy(必须走 PR)
  ❌ 自动备份/恢复(这是 cron 的事,不是 agent)
```

### 主动告警(不靠 subagent)

```text
subagent 是被动的(Owner 问它才回答)。主动告警需要别的:

简单 cron + 飞书 webhook:
  - Postgres 连不上 → 告警
  - 磁盘 > 80% → 告警
  - 24h 内任务 0 个完成 → 告警
  - 代理(bandwagon)挂了 → 告警

收到告警 → Owner 打开 Ops subagent → 贴上告警内容 → 诊断
```

### 演化路径

```text
V1 阶段:
  - Claude subagent + Owner SSH 操作
  
V1.5 阶段(V1 跑稳 1-2 个月后):
  - 评估是否需要"专门的 ops agent 服务"
  - 触发条件:运维占用 Owner > 10 小时/月
  - 不到这个数,继续用 subagent
  
V2 阶段:
  - 考虑"半自治运维"(只读诊断 + 给出建议给 Owner 决策)
  - 不做"自动操作生产"(永远不做)
```

### 写 prompt 草稿的时机

```text
v2.2 现在:
  - 写概念性草稿(docs/operations/*.md)
  - 描述定位、能力边界、context 清单
  - 不写具体的 system prompt 内容(没真实场景)
  
Phase 0C 部署后:
  - 在真实环境跑过几周
  - 用 meta_prompts 思路生成 system prompt
  - Owner review 后落地到 Claude.ai Project
```

## 9. 网络与凭据

```text
必需凭据:
  - ANTHROPIC_API_KEY (Claude API)
  - GITHUB_TOKEN 或 SSH key (Git push + gh CLI)
  - 飞书 webhook URL (escalation 通知)

存储方式:
  V1:  .env 文件 + dotenv 加载,.gitignore 忽略
  V2:  考虑 vault / 1Password CLI
  
  V1 不做:
  ❌ 完整 secret manager
  ❌ 凭据轮换
```

## 10. 决策记录

```text
[2026-05-25] 决定:V1 用 docker-compose + 自托管 Postgres + Langfuse
  理由:
  - Phase 0A / 0B 不需要服务,本地跑
  - Phase 0C 起 docker-compose 简单可控
  - Owner 单人维护,no SRE budget
  - 内部使用、低敏感度,接受单点故障风险

[2026-05-25] 决定:用阿里云国内 Region + bandwagon VPS 代理
  理由:
  - 公司约束必须用阿里云
  - 数据不敏感,合规风险低
  - 已有 bandwagon VPS 可做代理(沉没成本)
  - 国内 Region 比海外便宜,延迟更友好

[2026-05-25] 决定:运维方式 = Claude subagent 分工 + Owner SSH
  理由:
  - 不做独立 ops agent 软件(过度工程)
  - Claude subagent 零成本,上下文隔离
  - V1.5 才评估是否需要"专门 ops 服务"

[2026-05-25] 决定:不上 k8s / 不上阿里云 RDS / 不上 ACK
  理由:单人项目,这些都是过度工程
```

## 11. 你需要决定的(开工前)

打 ✓ 表示已决定:

```text
[✓] 部署目标:阿里云国内 ECS
[ ] 阿里云 Region:杭州 / 上海 / 北京 / 深圳(看延迟)
[ ] ECS 规格:s6 (2c4g) 起步,Phase 5 升 g6 (4c8g)
[✓] 代理:bandwagon VPS
[ ] bandwagon 节点位置(影响延迟)
[✓] 操作系统:Linux(Ubuntu 22.04 LTS 推荐)
[ ] 备份目标:阿里云 OSS 同 Region(免费内网流量)
[✓] 通知渠道:飞书
[✓] 运维方式:Claude subagent 分工(coding + ops)
```

这些不决定也不阻塞 Phase 0A 开工,Phase 0C 之前定下来即可。

---

## 元数据

- 版本:v1.1
- 创建:2026-05-25
- v1.1 增量:加阿里云实际方案 + Claude subagent 运维分工(新第 8 节)
- 配套主文档:autonomous-agent-system-design.md v2.2
- 配套 subagent prompt:docs/operations/coding-subagent-prompt.md, docs/operations/ops-subagent-prompt.md
- 维护:Phase 0C 部署后,把"决策记录"和"硬件资源粗估"用真实数据更新
