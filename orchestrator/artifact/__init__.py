"""产物存储(role 输出的 artifact)。

artifact 不可变,attempt N+1 是新 artifact_id(v2.4)。
本模块对 artifact.content 类型无知,只存 dict。
content schema 校验在 roles 模块出口做。

public API(Phase 0B 待填):
    write_artifact(artifact) -> artifact_id
    get_artifact(artifact_id) -> Artifact
    get_current_artifact(task_id, subtask_id, role_id) -> Artifact | None
"""
