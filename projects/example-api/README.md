# projects/example-api/

示例项目配置,展示方案 Y(framework 不预设角色,Owner 自己配)。

## 结构

```
project.yaml          # 项目元数据 + roles 列表 + role_groups
dispatch_policy.yaml  # mandatory_role_rules + retry_limits + pm_deviation_policy
roles/                # 该项目用的角色(从 examples/role_templates/ 拷过来改)
  pm/
  developer/
  reviewer/
```

## 起新项目怎么做

1. `cp -r projects/example-api projects/my-project/`
2. 改 `project.yaml`:project_id / name / repo_url / role_groups / protected_paths
3. 改 `roles/` 下角色 prompt(根据项目特点)
4. 改 `dispatch_policy.yaml`(根据项目敏感度)
5. 校验:`check-jsonschema --schemafile schemas/project.schema.json projects/my-project/project.yaml`
