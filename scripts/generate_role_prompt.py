#!/usr/bin/env python3
"""scripts/generate_role_prompt.py

CLI 包装:用 Anthropic Claude API 跑 meta_prompts/generate_role_prompt.md。

用法:
    python scripts/generate_role_prompt.py \\
        --role-id security_reviewer \\
        --artifact-type security_review \\
        --description "审查 OAuth / 加密 / 密钥相关改动" \\
        --output examples/role_templates/security_reviewer/system_prompt.md

需要环境变量:
    ANTHROPIC_API_KEY

这是"启动门槛工具",不是自动化。Owner 必须 review 生成的草稿再提交。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


META_PROMPT_PATH = Path(__file__).parent.parent / "meta_prompts" / "generate_role_prompt.md"


def build_user_message(
    role_id: str,
    artifact_type: str,
    description: str,
    capabilities: list[str],
    constraints: list[str],
) -> str:
    return f"""
请按 meta_prompts/generate_role_prompt.md 的要求,给我生成下面这个角色的 system_prompt.md。

role_id: {role_id}
artifact_type: {artifact_type}
职责描述: |
  {description}
特殊能力:
{chr(10).join(f"  - {c}" for c in capabilities) if capabilities else "  (无特殊能力,基础角色)"}
特别约束:
{chr(10).join(f"  - {c}" for c in constraints) if constraints else "  (无)"}

请直接输出完整 markdown 文件内容(不要 wrap 在 code fence 里)。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role-id", required=True, help="role_id(snake_case)")
    parser.add_argument(
        "--artifact-type",
        required=True,
        help="对应 schemas/artifact_content/<type>.schema.json",
    )
    parser.add_argument("--description", required=True, help="1-3 句话职责描述")
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="重复使用:--capability X --capability Y",
    )
    parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help="重复使用",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5",
        help="模型 ID(默认 claude-sonnet-4-5)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="输出文件路径(通常 examples/role_templates/<role>/system_prompt.md)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印请求内容,不调 API(用来 review 输入)",
    )

    args = parser.parse_args()

    if not META_PROMPT_PATH.exists():
        print(f"ERROR: meta-prompt 不存在:{META_PROMPT_PATH}", file=sys.stderr)
        return 1

    system_prompt = META_PROMPT_PATH.read_text()
    user_message = build_user_message(
        role_id=args.role_id,
        artifact_type=args.artifact_type,
        description=args.description,
        capabilities=args.capability,
        constraints=args.constraint,
    )

    if args.dry_run:
        print("===== System Prompt(meta_prompt) =====")
        print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
        print()
        print("===== User Message =====")
        print(user_message)
        print()
        print(f"===== Model: {args.model} =====")
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: 缺少环境变量 ANTHROPIC_API_KEY", file=sys.stderr)
        return 2

    try:
        from anthropic import Anthropic
    except ImportError:
        print("ERROR: 请先 `uv pip install anthropic` 或在 pyproject 已经声明", file=sys.stderr)
        return 3

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=args.model,
        max_tokens=args.max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    content = response.content[0].text  # type: ignore[union-attr]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content)

    cost_info = (
        f"\ninput_tokens={response.usage.input_tokens}, "
        f"output_tokens={response.usage.output_tokens}"
    )
    print(f"✅ 已生成 {args.output}{cost_info}")
    print("⚠️  这是草稿,Owner 必须 review 再提交。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
