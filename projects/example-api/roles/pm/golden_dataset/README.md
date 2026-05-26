# PM Golden Dataset

5 个 case 覆盖:
- `case_001_simple_bugfix.yaml` — bug_fix 任务(最简单)
- `case_002_complex_feature.yaml` — 多 subtask + 有依赖
- `case_003_security_sensitive.yaml` — 触发 mandatory rule(security_reviewer)
- `case_004_refactor_with_tester.yaml` — refactor + 偏离默认模板
- `case_005_ambiguous_request.yaml` — Owner 需求模糊(测 confidence + signal 行为)

跑 dataset:`scripts/eval_golden.py pm`(Phase 1 才实现)。

通过线:单 case ≥ 70 分,平均 ≥ 80 分。
