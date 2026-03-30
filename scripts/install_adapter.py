#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path


BEGIN_MARKER = "<!-- design-buff:begin -->"
END_MARKER = "<!-- design-buff:end -->"
CODEX_ALLOWLIST = [
    "SKILL.md",
    "agents",
    "references",
    "scripts",
    "templates",
    "LICENSE",
    ".gitignore",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_portable_instructions(root: Path) -> str:
    path = root / "adapters" / "shared" / "portable-instructions.md"
    return path.read_text(encoding="utf-8").strip()


def wrap_managed_block(title: str, body: str) -> str:
    return f"{BEGIN_MARKER}\n## {title}\n\n{body.rstrip()}\n{END_MARKER}\n"


def upsert_markdown_block(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        original = path.read_text(encoding="utf-8")
        if BEGIN_MARKER in original and END_MARKER in original:
            before, remainder = original.split(BEGIN_MARKER, 1)
            _, after = remainder.split(END_MARKER, 1)
            updated = before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip("\n")
        else:
            updated = original.rstrip() + "\n\n" + block.rstrip() + "\n"
    else:
        updated = block
    path.write_text(updated, encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_claude_block(portable: str) -> str:
    intro = (
        "Use this installed Design Buff block when the user asks for design review, "
        "design self-check, flow diagnosis, Figma review, screenshot review, or product-minded UX critique.\n\n"
    )
    return wrap_managed_block("Design Buff", intro + portable)


def render_claude_command(root: Path) -> str:
    return (root / "adapters" / "claude-code" / "design-buff-review.md").read_text(encoding="utf-8").strip()


def render_cursor_rule(portable: str) -> str:
    return (
        "---\n"
        "description: Use Design Buff for product-minded design review from Figma, screenshots, or flow docs\n"
        "alwaysApply: false\n"
        "---\n\n"
        "Use this rule when the user asks for design review, self-check, flow diagnosis, or UX critique from Figma, screenshots, exports, or product documents.\n\n"
        f"{portable.rstrip()}\n"
    )


def render_agents_block(portable: str) -> str:
    intro = (
        "Use this installed Design Buff block when the user asks for design review, "
        "Figma review, screenshot critique, journey diagnosis, or product-minded UX feedback.\n\n"
    )
    return wrap_managed_block("Design Buff", intro + portable)


def render_codex_runtime_readme() -> str:
    return """# Design Buff

这是给 `Codex` 直接安装使用的最小运行仓库，不是维护源码仓库。

`Design Buff` 是一个面向业务与体验的设计审核 skill，不是审美打分器。它会根据 Figma、截图、页面结构和补充材料，还原这条设计到底服务谁、要完成什么任务、处在链路的哪一步，再判断真正的问题是不是出在结构、认知成本、信任建立或连续性上。

## 这个 Skill 用来做什么

- 设计师自查和方案复盘
- 关键转化流程的体验诊断
- Figma、截图、PRD 混合输入下的设计审核
- 发现页面局部没错、但整条链路不顺的结构问题

## 在 Codex 里怎么触发

- 如果你是让 AI 直接按 GitHub URL 安装，这个仓库本身就可以直接安装
- 直接在对话里写明你的设计审核需求，并附上 Figma、截图或相关材料
- 想明确点名时，直接写 `$design-buff`
- 如果已经有同一条方案的旧评审，继续沿用同一个 `review-slug`

## 会生成什么

- 人看的报告：`design-buff-reviews/<review-slug>/report.html`
- 机器状态：`design-buff-reviews/<review-slug>/review-state.json`
- 临时技术状态：`.design-buff/<review-slug>/`

`report.html` 是正式的人类评审报告；`review-state.json` 只用于结构化追踪、复跑和对比，不是第二份报告。
"""


def copy_allowed_entries(source: Path, destination: Path, allowlist: list[str]) -> None:
    for entry in allowlist:
        src = source / entry
        dst = destination / entry
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def default_codex_skill_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return base / "skills" / "design-buff"


def install_codex(root: Path, target: Path | None) -> list[Path]:
    destination = (target if target is not None else default_codex_skill_dir()).resolve()
    root = root.resolve()
    if destination == root:
        raise SystemExit("Codex 默认安装位当前正指向这个仓库本身。无需覆盖仓库；如需验证或生成精简运行包，请改用 --target 指到别的目录。")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="design-buff-codex-", dir=destination.parent) as tmpdir:
        staging = Path(tmpdir) / "design-buff"
        staging.mkdir(parents=True, exist_ok=True)
        copy_allowed_entries(root, staging, CODEX_ALLOWLIST)
        write_text(staging / "README.md", render_codex_runtime_readme())

        if destination.exists():
            if destination.is_file():
                raise SystemExit(f"目标路径已存在且不是目录：{destination}")
            shutil.rmtree(destination)
        shutil.move(str(staging), str(destination))
    return [destination]


def install_claude(root: Path, scope: str, target: Path | None) -> list[Path]:
    portable = read_portable_instructions(root)
    if scope == "user":
        base = Path.home() / ".claude"
    else:
        if target is None:
            raise SystemExit("--target is required for project scope")
        base = target / ".claude"
    claude_md = base / "CLAUDE.md"
    command_md = base / "commands" / "design-buff-review.md"
    upsert_markdown_block(claude_md, render_claude_block(portable))
    write_text(command_md, render_claude_command(root))
    return [claude_md, command_md]


def install_cursor(root: Path, target: Path | None) -> list[Path]:
    if target is None:
        raise SystemExit("--target is required for cursor adapter")
    portable = read_portable_instructions(root)
    rule_path = target / ".cursor" / "rules" / "design-buff-review.mdc"
    write_text(rule_path, render_cursor_rule(portable))
    return [rule_path]


def install_generic(root: Path, target: Path | None) -> list[Path]:
    if target is None:
        raise SystemExit("--target is required for generic-agents adapter")
    portable = read_portable_instructions(root)
    agents_md = target / "AGENTS.md"
    upsert_markdown_block(agents_md, render_agents_block(portable))
    return [agents_md]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Design Buff adapters into another project or user config.")
    parser.add_argument(
        "platform",
        choices=["codex", "claude-code", "cursor", "generic-agents"],
        help="Target runtime adapter to install.",
    )
    parser.add_argument(
        "--scope",
        choices=["project", "user"],
        default="project",
        help="Install scope. Only Claude Code supports user scope.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Target project path. Required for project-scope installs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root()

    if args.platform != "claude-code" and args.scope != "project":
        raise SystemExit("Only claude-code supports --scope user.")

    if args.platform == "codex":
        written = install_codex(root, args.target.resolve() if args.target else None)
    elif args.platform == "claude-code":
        written = install_claude(root, args.scope, args.target.resolve() if args.target else None)
    elif args.platform == "cursor":
        written = install_cursor(root, args.target.resolve() if args.target else None)
    else:
        written = install_generic(root, args.target.resolve() if args.target else None)

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
