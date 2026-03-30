#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List


ZH_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
JA_RE = re.compile(r"[\u3040-\u30ff]")
KO_RE = re.compile(r"[\uac00-\ud7af]")
LATIN_RE = re.compile(r"[A-Za-z]")


def read_inputs(files: Iterable[str], texts: Iterable[str]) -> str:
    chunks: List[str] = list(texts)
    for file_path in files:
        chunks.append(Path(file_path).read_text(encoding="utf-8"))
    if not chunks and not sys.stdin.isatty():
        chunks.append(sys.stdin.read())
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def detect_language(text: str, override: str = "") -> Dict[str, object]:
    if override:
        return {
            "suggested_language": override,
            "language_source": "explicit_override",
            "confidence": "high",
            "reason": "Explicit override provided by the caller.",
            "stats": {},
        }

    if not text:
        return {
            "suggested_language": "zh-CN",
            "language_source": "default_zh_cn",
            "confidence": "low",
            "reason": "No usable language signal was found, so the default fallback is zh-CN.",
            "stats": {},
        }

    stats = {
        "zh_chars": len(ZH_RE.findall(text)),
        "ja_chars": len(JA_RE.findall(text)),
        "ko_chars": len(KO_RE.findall(text)),
        "latin_chars": len(LATIN_RE.findall(text)),
    }

    if stats["ja_chars"] >= 6 and stats["ja_chars"] >= stats["latin_chars"] / 4:
        return {
            "suggested_language": "ja",
            "language_source": "intake_inference",
            "confidence": "medium",
            "reason": "Kana characters dominate the materials, so Japanese is the best-fit report language.",
            "stats": stats,
        }

    if stats["ko_chars"] >= 6 and stats["ko_chars"] >= stats["latin_chars"] / 4:
        return {
            "suggested_language": "ko",
            "language_source": "intake_inference",
            "confidence": "medium",
            "reason": "Hangul characters dominate the materials, so Korean is the best-fit report language.",
            "stats": stats,
        }

    if stats["zh_chars"] >= max(12, stats["latin_chars"] // 2):
        return {
            "suggested_language": "zh-CN",
            "language_source": "intake_inference",
            "confidence": "high" if stats["zh_chars"] >= stats["latin_chars"] else "medium",
            "reason": "Chinese text is the dominant signal across the supplied materials.",
            "stats": stats,
        }

    if stats["latin_chars"] > 0:
        return {
            "suggested_language": "en",
            "language_source": "intake_inference",
            "confidence": "medium",
            "reason": "Latin-script text dominates the supplied materials, so English is the best-fit report language.",
            "stats": stats,
        }

    return {
        "suggested_language": "zh-CN",
        "language_source": "default_zh_cn",
        "confidence": "low",
        "reason": "The signal was mixed or too weak, so the default fallback is zh-CN.",
        "stats": stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suggest a report language from conversation or document text, with zh-CN as the default fallback."
    )
    parser.add_argument("--file", action="append", default=[], help="UTF-8 text file to inspect. May be repeated.")
    parser.add_argument("--text", action="append", default=[], help="Inline text sample to inspect. May be repeated.")
    parser.add_argument("--override", default="", help="Explicit language override such as zh-CN or en.")
    args = parser.parse_args()

    text = read_inputs(args.file, args.text)
    print(json.dumps(detect_language(text, args.override), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
