#!/usr/bin/env python3

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_review_contract.py"
RENDERER = REPO_ROOT / "scripts" / "render_report.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures"
VALID_GOLD = FIXTURE_ROOT / "valid-gold-yitongbai"
VALID_RENDER = FIXTURE_ROOT / "valid-render-self-check"
VALID_RENDER_STATE = (
    VALID_RENDER / "design-buff-reviews" / "self-check-render-sample" / "review-state.json"
)
VALID_RENDER_SLOTS = (
    VALID_RENDER / ".design-buff" / "self-check-render-sample" / "report-slots.json"
)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def require(result: subprocess.CompletedProcess[str], expect_success: bool, label: str) -> None:
    ok = result.returncode == 0
    if ok != expect_success:
        print(f"[FAIL] {label}")
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        raise SystemExit(1)
    status = "PASS" if expect_success else "PASS(expected failure)"
    print(f"[{status}] {label}")


def render_valid_fixture() -> None:
    report_path = VALID_RENDER_STATE.with_name("report.html")
    if report_path.exists():
        report_path.unlink()
    result = run(
        [
            sys.executable,
            str(RENDERER),
            str(VALID_RENDER_STATE),
            "--slots",
            str(VALID_RENDER_SLOTS),
        ],
        REPO_ROOT,
    )
    require(result, True, "render valid self-check fixture")


def validate_fixture(root: Path, expect_success: bool, label: str) -> None:
    result = run([sys.executable, str(VALIDATOR), str(root)], REPO_ROOT)
    require(result, expect_success, label)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def mutate_h1_verdict(root: Path) -> None:
    report_path = root / "design-buff-reviews" / "self-check-render-sample" / "report.html"
    html = report_path.read_text(encoding="utf-8")
    original = '<h1 data-slot="project-name">会员互通开通与绑定流程</h1>'
    replacement = '<h1 data-slot="project-name">这条互通流程最大的问题不是页面不够全，而是系统把最早那道最难判断的题仍然留给了用户自己做。</h1>'
    write_text(report_path, html.replace(original, replacement, 1))


def mutate_stacked_timeline(root: Path) -> None:
    report_path = root / "design-buff-reviews" / "self-check-render-sample" / "report.html"
    html = report_path.read_text(encoding="utf-8")
    html = html.replace('class="timeline-node"', 'class="timeline-card"')
    html = html.replace('class="timeline-stage"', 'class="timeline-head"')
    html = html.replace('class="timeline-stage-text"', 'class="timeline-meta"')
    html = html.replace('class="timeline-dot"', 'class="tag"')
    html = html.replace('class="timeline-stage-title"', 'class="timeline-title"')
    html = html.replace('class="timeline-stage-summary"', 'class="timeline-subtitle"')
    html = html.replace('class="timeline-summary"', 'class="muted"')
    write_text(report_path, html)


def mutate_resolution_path_cards(root: Path) -> None:
    report_path = root / "design-buff-reviews" / "self-check-render-sample" / "report.html"
    html = report_path.read_text(encoding="utf-8")
    old = """<section class="section" id="resolution-tracks" data-structure="resolution-summary">
      <div class="section-header">
        <h2>结构摘要</h2>
      </div>
      <div class="three-col">
        <div class="panel">
          <h3>问题分布</h3>
          <p>这轮最重的问题不是平均散落在每个页面上，而是集中成三组结构风险：首步判路错位、关键节点层级混乱、站外回流承接不足。</p>
        </div>
        <div class="panel">
          <h3>分三批推进</h3>
          <p>建议分三批推进。第一批先修首步判路与失败恢复；第二批拆开协议层级；第三批补齐站外回流与安全承接。</p>
        </div>
        <div class="panel">
          <h3>关键风险</h3>
          <p>如果继续按当前结构推进，用户会在最关键的几个节点连续补猜：先猜自己该走哪条路，再猜失败后的按钮会把自己带去哪里，最后再猜站外登录后能不能顺利回来。</p>
        </div>
      </div>
    </section>"""
    new = """<section class="section" id="resolution-tracks" data-structure="resolution-summary">
      <div class="section-header">
        <h2>修正路径</h2>
      </div>
      <div class="tracks">
        <article class="track-card">
          <h3>路径一：先修首步判路</h3>
          <p>把授权后的状态识别前移，尽量减少用户首步自诊断。</p>
        </article>
        <article class="track-card">
          <h3>路径二：再拆协议层级</h3>
          <p>把必选协议与营销偏好拆开，减少关键节点里的额外判断。</p>
        </article>
        <article class="track-card">
          <h3>路径三：最后补站外承接</h3>
          <p>把外跳前后的安全感、回流方式和失败兜底讲实。</p>
        </article>
      </div>
    </section>"""
    write_text(report_path, html.replace(old, new, 1))


def mutate_split_tail_sections(root: Path) -> None:
    report_path = root / "design-buff-reviews" / "self-check-render-sample" / "report.html"
    html = report_path.read_text(encoding="utf-8")
    old = """<section class="section">
      <div class="section-header">
        <h2>待确认与下一步</h2>
      </div>
      <div class="actions-grid" data-structure="closing-actions-grid">
        <div class="panel" id="open-questions">
          <h3>待确认</h3>
          <ol class="ordered-actions"><li>系统能否在授权后直接判断用户该走开通还是绑定？</li><li>营销授权能否后置到主任务完成后再补充？</li><li>站外登录完成后能否自动返回并刷新结果？</li></ol>
        </div>
        <div class="panel" id="next-actions">
          <h3>下一步</h3>
          <ol class="ordered-actions"><li>先重做首步分流，把第一道题改成用户答得出来的事实题。</li><li>把协议页里的必选协议与营销偏好彻底拆开。</li><li>补齐失败恢复与站外回流的结果型动作和反馈说明。</li></ol>
        </div>
      </div>
      <p class="footer-note">产物路径：design-buff-reviews/self-check-render-sample/report.html · run_id: run_fixture_render_sample_001 · 评审节点: 36:587</p>
    </section>"""
    new = """<section class="section" id="open-questions">
      <div class="section-header">
        <h2>待确认</h2>
      </div>
      <ol class="ordered-actions"><li>系统能否在授权后直接判断用户该走开通还是绑定？</li><li>营销授权能否后置到主任务完成后再补充？</li><li>站外登录完成后能否自动返回并刷新结果？</li></ol>
    </section>

    <section class="section" id="next-actions">
      <div class="section-header">
        <h2>下一步</h2>
      </div>
      <ol class="ordered-actions"><li>先重做首步分流，把第一道题改成用户答得出来的事实题。</li><li>把协议页里的必选协议与营销偏好彻底拆开。</li><li>补齐失败恢复与站外回流的结果型动作和反馈说明。</li></ol>
      <p class="footer-note">产物路径：design-buff-reviews/self-check-render-sample/report.html · run_id: run_fixture_render_sample_001 · 评审节点: 36:587</p>
    </section>"""
    write_text(report_path, html.replace(old, new, 1))


def mutate_precise_intake_drift(root: Path) -> None:
    state_path = root / "design-buff-reviews" / "self-check-render-sample" / "review-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["meta"]["requested_input_node"] = None
    state["meta"]["reviewed_node"] = "0:1"
    state["meta"]["reviewed_node_reason"] = None
    write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def build_standalone_case(tmp_root: Path) -> Path:
    standalone = tmp_root / "invalid-standalone-desktop"
    standalone.mkdir(parents=True, exist_ok=True)
    report_src = VALID_RENDER / "design-buff-reviews" / "self-check-render-sample" / "report.html"
    shutil.copy2(report_src, standalone / "report.html")
    return standalone


def copy_valid_fixture(tmp_root: Path, case_name: str) -> Path:
    case_root = tmp_root / case_name
    shutil.copytree(VALID_RENDER, case_root)
    return case_root


def main() -> int:
    render_valid_fixture()

    validate_fixture(VALID_GOLD, True, "gold fixture passes")
    validate_fixture(VALID_RENDER, True, "renderer fixture passes")

    with tempfile.TemporaryDirectory(prefix="design-buff-contract-") as tmpdir:
        tmp_root = Path(tmpdir)

        invalid_h1 = copy_valid_fixture(tmp_root, "invalid-h1-verdict")
        mutate_h1_verdict(invalid_h1)
        validate_fixture(invalid_h1, False, "invalid h1 verdict fails")

        invalid_timeline = copy_valid_fixture(tmp_root, "invalid-stacked-timeline")
        mutate_stacked_timeline(invalid_timeline)
        validate_fixture(invalid_timeline, False, "stacked timeline drift fails")

        invalid_resolution = copy_valid_fixture(tmp_root, "invalid-resolution-path-cards")
        mutate_resolution_path_cards(invalid_resolution)
        validate_fixture(invalid_resolution, False, "resolution path cards fail")

        invalid_tail = copy_valid_fixture(tmp_root, "invalid-split-tail-sections")
        mutate_split_tail_sections(invalid_tail)
        validate_fixture(invalid_tail, False, "split tail sections fail")

        invalid_precise_intake = copy_valid_fixture(tmp_root, "invalid-precise-intake-drift")
        mutate_precise_intake_drift(invalid_precise_intake)
        validate_fixture(invalid_precise_intake, False, "precise intake drift fails")

        standalone = build_standalone_case(tmp_root)
        validate_fixture(standalone, False, "standalone desktop report fails")

    print("All contract regressions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
