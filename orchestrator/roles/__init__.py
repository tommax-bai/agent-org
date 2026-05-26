"""角色调用框架(role_invocation_protocol 的执行)。

不是 role 配置(那是 examples/role_templates/ + projects/<x>/roles/)。
这里是"调用 role 的代码"。

public API(待填):
    RoleRunner: 抽象类,实现 role_invocation_protocol
    invoke_role(role_id, context_pack) -> RoleInvocationOutput
"""
