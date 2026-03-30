#!/usr/bin/env python3

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple


FRAME_RE = re.compile(
    r'^(?P<indent>\s*)<(?P<tag>frame|section)\s+id="(?P<id>[^"]+)"\s+name="(?P<name>[^"]*)"\s+'
    r'x="(?P<x>[^"]+)"\s+y="(?P<y>[^"]+)"\s+width="(?P<width>[^"]+)"\s+height="(?P<height>[^"]+)"'
)

IGNORE_NAME_RE = re.compile(r"(vector|slice|group|路径|光效|image\s+\d+|img_|rectangle)", re.IGNORECASE)
SCREEN_HINT_RE = re.compile(r"(frame|开通|绑定|协议|失败|成功|说明|信息|登录|实名|会员)", re.IGNORECASE)


@dataclass
class Candidate:
    id: str
    name: str
    tag: str
    depth: int
    x: float
    y: float
    width: float
    height: float
    score: int
    reasons: List[str]


def read_source(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def score_frame(name: str, width: float, height: float, depth: int) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    aspect = width / height if height else 0

    if 280 <= width <= 1800:
        score += 3
        reasons.append("screen_like_width")
    elif width > 3000:
        score -= 4
        reasons.append("too_wide_for_single_screen")

    if 480 <= height <= 4000:
        score += 3
        reasons.append("screen_like_height")
    elif height > 5000:
        score -= 4
        reasons.append("too_tall_for_single_screen")

    if 0.2 <= aspect <= 1.6:
        score += 2
        reasons.append("reasonable_aspect_ratio")

    if SCREEN_HINT_RE.search(name):
        score += 2
        reasons.append("name_looks_like_flow_step")

    if IGNORE_NAME_RE.search(name):
        score -= 5
        reasons.append("name_looks_decorative")

    if depth <= 1:
        score += 1
        reasons.append("near_root")

    return score, reasons


def parse_candidates(source: str, min_score: int) -> List[Candidate]:
    candidates: List[Candidate] = []
    for line in source.splitlines():
        match = FRAME_RE.match(line)
        if not match:
            continue
        indent = match.group("indent")
        depth = len(indent) // 2
        width = float(match.group("width"))
        height = float(match.group("height"))
        score, reasons = score_frame(match.group("name"), width, height, depth)
        if score < min_score:
            continue
        candidates.append(
            Candidate(
                id=match.group("id"),
                name=match.group("name"),
                tag=match.group("tag"),
                depth=depth,
                x=float(match.group("x")),
                y=float(match.group("y")),
                width=width,
                height=height,
                score=score,
                reasons=reasons,
            )
        )
    candidates.sort(key=lambda item: (-item.score, item.y, item.x, item.depth))
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest screen-like Figma review units from get_metadata output.")
    parser.add_argument("source", nargs="?", help="Path to saved metadata output. Reads stdin when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    parser.add_argument("--min-score", type=int, default=4, help="Minimum score to keep a candidate.")
    args = parser.parse_args()

    candidates = parse_candidates(read_source(args.source), args.min_score)

    if args.json:
        print(json.dumps([asdict(candidate) for candidate in candidates], ensure_ascii=False, indent=2))
        return

    if not candidates:
        print("No review units matched the configured heuristics.")
        return

    for index, candidate in enumerate(candidates, start=1):
        print(
            f"{index}. {candidate.id} | {candidate.name} | {int(candidate.width)}x{int(candidate.height)} | "
            f"score={candidate.score} | reasons={','.join(candidate.reasons)}"
        )


if __name__ == "__main__":
    main()
