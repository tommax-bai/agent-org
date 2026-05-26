# 通用角色模板

复制这个目录到 `projects/<project>/roles/<your_role>/`,改:
1. `role.yaml`:role_id / name / description / model / capabilities / inputs / outputs / budget
2. `system_prompt.md`:按 6 段标准结构填(见 `docs/role_prompt_structure.md`)
3. `golden_dataset/`:5-30 个 case(见 `docs/golden_dataset_format.md`)

`is_orchestrator: true` 的角色(出 dispatch_plan)只能有一个,通常是 PM。
