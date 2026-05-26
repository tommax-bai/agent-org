# meta_prompts/ — LLM 辅助生成 prompt / dataset 的工具

不是自动化。Owner 用这些 prompt 让 Claude 生成草稿,**Owner review 后再提交**(不直接进 git)。

## 文件

- `generate_role_prompt.md` — 让 LLM 帮你写 role 的 system_prompt.md 草稿
- `generate_golden_dataset.md` — 让 LLM 帮你生成 golden case 草稿

## 用法

```bash
# 准备输入(role_id / 职责描述 / 输入输出约定)
# 把 generate_role_prompt.md 内容贴给 Claude(或用 scripts/generate_role_prompt.py)
# 拿到草稿,review,改,提交
```

详细见 `docs/autonomous-agent-system-design.md` B 域"角色创建的工程实践"。
