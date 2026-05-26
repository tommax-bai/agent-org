# tasks/

任务文件目录。状态机驱动的流转:

```
inbox/         Owner 写好 task.yaml 丢这里(进 git)
   ↓ orchestrator 拉一个开始跑
active/        正在跑的任务(不进 git)
   ↓ 成功 / 失败
done/          成功完成(不进 git)
failed/        失败或 escalate(不进 git)
```

只有 `inbox/` 进 git。`active/done/failed/` 在 .gitignore 里(`.gitkeep` 保留目录)。

## task.yaml schema

见 `schemas/task.schema.json`。

校验示例:

```bash
check-jsonschema --schemafile schemas/task.schema.json tasks/inbox/*.yaml
```
