#!/usr/bin/env python3

import argparse
import json
import re
from urllib.parse import parse_qs, urlparse


def normalize_node_id(value):
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    return value.replace("-", ":")


def parse_figma_url(url):
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    result = {
        "url": url,
        "editor": None,
        "file_key": None,
        "node_id": normalize_node_id(parse_qs(parsed.query).get("node-id", [None])[0]),
    }

    if len(path_parts) >= 4 and path_parts[0] == "design" and path_parts[2] == "branch":
        result["editor"] = "design-branch"
        result["file_key"] = path_parts[3]
    elif len(path_parts) >= 2 and path_parts[0] in {"design", "board", "make"}:
        result["editor"] = path_parts[0]
        result["file_key"] = path_parts[1]

    if result["file_key"] is None:
        match = re.search(r"figma\.com/(design|board|make)/([^/]+)", url)
        if match:
            result["editor"] = match.group(1)
            result["file_key"] = match.group(2)

    result["is_precise_intake"] = bool(result["file_key"] and result["node_id"])
    result["recommended_next_step"] = (
        "use_as_intake_root" if result["is_precise_intake"] else "locate_board_or_frame_before_review"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description="Parse a Figma URL into fileKey and normalized node-id.")
    parser.add_argument("url", help="Figma design, board, or make URL")
    args = parser.parse_args()
    print(json.dumps(parse_figma_url(args.url), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
