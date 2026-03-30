#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from typing import Dict, Optional


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "issue"


def make_issue_id(title: str, semantic: Optional[str], category: Optional[str]) -> Dict[str, str]:
    semantic_part = slugify(semantic or category or title)
    seed = "\n".join(part.strip() for part in [title, category or "", semantic or ""])
    suffix = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6]
    stable_id = f"{semantic_part}__{suffix}"
    return {
        "stable_id": stable_id,
        "semantic_part": semantic_part,
        "suffix": suffix,
        "seed": seed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a mixed-format stable issue ID.")
    parser.add_argument("title", help="Human-readable issue title")
    parser.add_argument("--semantic", help="Preferred semantic fragment for the readable prefix")
    parser.add_argument("--category", help="Issue category used as fallback semantic context")
    args = parser.parse_args()

    print(json.dumps(make_issue_id(args.title, args.semantic, args.category), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
