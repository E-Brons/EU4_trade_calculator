#!/usr/bin/env python3
"""Decide what the research agent has to do, from the files in docs/research.

Convention (docs/research/README.md): Rxx_<topic>_{goal,draft,request_<i>,response_<i>,final}.md
Sequence per topic: goal(0) -> draft(1) -> request_1(2) -> response_1(3) -> request_2(4) ...
The agent only acts when the newest file is a `goal` (write the draft) or a `request_<i>`
(write the response). After a draft/response the next step is a human/Claude review, after
`final` there is nothing to do. A target file that already exists is never regenerated.

  plan                  print the JSON list of pending items (for a GitHub matrix)
  prompt <target>       print the prompt for one target file
  strip <file>          remove an outer ```markdown wrapper (allowed formatting repair)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "docs" / "research"
NAME = re.compile(r"^(R\d+)_(.+?)_(goal|draft|final|request_(\d+)|response_(\d+))\.md$")
MAX_ROUNDS = 4


def scan():
    topics = {}
    for p in sorted(ROOT.glob("R*.md")):
        m = NAME.match(p.name)
        if not m:
            continue
        rid, topic, kind, req, resp = m.groups()
        order = {"goal": 0, "draft": 1, "final": 10**6}.get(kind)
        if order is None:
            order = 2 * int(req) if req else 2 * int(resp) + 1
        topics.setdefault((rid, topic), {})[order] = (kind, p)
    return topics


def plan(only=None):
    out = []
    for (rid, topic), files in sorted(scan().items()):
        if only and only not in (rid, f"{rid}_{topic}"):
            continue
        newest = max(files)
        kind, path = files[newest]
        base = f"{rid}_{topic}"
        if kind == "goal":
            target, needs = f"{base}_draft.md", [path.name]
        elif kind.startswith("request_"):
            i = int(kind.split("_")[1])
            if i > MAX_ROUNDS:
                continue
            target = f"{base}_response_{i}.md"
            needs = [f"{base}_goal.md", f"{base}_draft.md"]
            for j in range(1, i):
                needs += [f"{base}_request_{j}.md", f"{base}_response_{j}.md"]
            needs.append(path.name)
        else:
            continue
        if (ROOT / target).exists() or not all((ROOT / n).exists() for n in needs):
            continue
        out.append({"topic": base, "target": target, "needs": needs, "kind": kind})
    return out


def prompt(target):
    item = next((x for x in plan() if x["target"] == target), None)
    if item is None:
        sys.exit(f"nothing pending for {target}")
    parts = [
        "You are the research agent for an EU4 (1.37.5) trade calculator. Follow the rules and the required "
        "answer format in the files below exactly. Use only sources you actually opened; give verbatim quotes; "
        "write UNKNOWN instead of guessing; never invent quotes, URLs, defines or data rows. "
        f"Your answer will be saved as docs/research/{target}. "
        "Output ONLY the markdown content of that file: no preface, no closing remarks, no outer code fence.",
        "",
        "The repository README that defines the convention:",
        f"=== docs/research/README.md ===\n{(ROOT / 'README.md').read_text()}",
    ]
    for n in item["needs"]:
        parts.append(f"=== docs/research/{n} ===\n{(ROOT / n).read_text()}")
    if item["kind"].startswith("request_"):
        parts.append("Answer only the numbered points of the last request, keeping their numbers.")
    return "\n".join(parts)


def strip(path):
    p = Path(path)
    lines = p.read_text().strip().split("\n")
    if lines and lines[0].strip() == "```markdown":
        lines = lines[1:]
        while lines and not lines[-1].strip():
            lines.pop()
        if lines and lines[-1].strip() == "```":
            lines.pop()
    text = "\n".join(lines).strip() + "\n"
    if len(text) < 500 or not text.lstrip().startswith("#"):
        sys.exit(f"{path}: output is empty or not a markdown document; refusing to keep it")
    p.write_text(text)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "plan":
        print(json.dumps(plan(sys.argv[2] if len(sys.argv) > 2 else None)))
    elif cmd == "prompt":
        print(prompt(sys.argv[2]))
    elif cmd == "strip":
        strip(sys.argv[2])
    else:
        sys.exit(__doc__)
