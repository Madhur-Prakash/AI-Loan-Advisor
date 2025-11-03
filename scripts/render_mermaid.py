#!/usr/bin/env python3
"""
Render Mermaid code blocks from a Markdown file to SVG/PNG.

Usage:
  python3 scripts/render_mermaid.py <input_md> [output_dir] [formats] [--local]

Defaults:
  output_dir = docs/images
  formats    = svg,png

This script scans for fenced code blocks that start with ```mermaid and
produces image files named after the nearest preceding markdown heading.
It renders via Kroki by default. Use --local to render with mermaid-cli (mmdc).
"""

import os
import sys
import re
import subprocess
import urllib.request
import urllib.error
import base64


def sanitize_filename(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\-\_\s]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name or "diagram"


def kroki_render(mermaid_source: str, fmt: str) -> bytes:
    url = f"https://kroki.io/mermaid/{fmt}"
    data = mermaid_source.encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Kroki HTTP error {e.code}: {e.read().decode('utf-8', 'ignore')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Kroki URL error: {e.reason}")


def ink_render(mermaid_source: str, fmt: str) -> bytes:
    # Mermaid Ink supports svg/png via base64-urlsafe encoding in path
    if fmt not in ("svg", "png"):
        raise ValueError("ink_render supports only svg and png")
    encoded = base64.urlsafe_b64encode(mermaid_source.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/{fmt}/{encoded}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Mermaid Ink HTTP error {e.code}: {e.read().decode('utf-8', 'ignore')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Mermaid Ink URL error: {e.reason}")


def parse_mermaid_blocks(md_text: str):
    blocks = []
    current_heading = ""
    in_block = False
    buf = []
    for line in md_text.splitlines():
        # Track headings for naming
        if re.match(r"^#{2,}\s+", line):
            current_heading = re.sub(r"^#{2,}\s+", "", line).strip()
        # Start of mermaid block
        if not in_block and line.strip() == "```mermaid":
            in_block = True
            buf = []
            continue
        # End of mermaid block
        if in_block and line.strip() == "```":
            blocks.append({
                "heading": current_heading,
                "source": "\n".join(buf)
            })
            in_block = False
            buf = []
            continue
        # Inside block
        if in_block:
            buf.append(line)
    return blocks


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/render_mermaid.py <input_md> [output_dir] [formats]", file=sys.stderr)
        sys.exit(2)

    input_md = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else os.path.join("docs", "images")
    formats_arg = sys.argv[3] if len(sys.argv) >= 4 else "svg,png"
    use_local = "--local" in sys.argv[4:] or os.getenv("LOCAL_MERMAID") == "1"
    formats = [f.strip() for f in formats_arg.split(",") if f.strip()]

    if not os.path.isfile(input_md):
        print(f"Input markdown not found: {input_md}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    sources_dir = os.path.join(os.path.dirname(output_dir), "diagrams")
    os.makedirs(sources_dir, exist_ok=True)

    with open(input_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = parse_mermaid_blocks(md_text)
    if not blocks:
        print("No mermaid blocks found.")
        return

    for idx, blk in enumerate(blocks, start=1):
        base_name = sanitize_filename(blk["heading"]) or f"diagram-{idx}"
        # Always write source .mmd for reproducibility
        src_path = os.path.join(sources_dir, f"{base_name}.mmd")
        with open(src_path, "w", encoding="utf-8") as sf:
            sf.write(blk["source"])

        if use_local:
            # Render using local mermaid-cli (mmdc)
            mmdc = os.path.join("node_modules", ".bin", "mmdc")
            if not os.path.isfile(mmdc):
                print("mermaid-cli not found (node_modules/.bin/mmdc). Install with: npm i -D @mermaid-js/mermaid-cli", file=sys.stderr)
                continue
            for fmt in formats:
                out_path = os.path.join(output_dir, f"{base_name}.{fmt}")
                cmd = [mmdc, "-i", src_path, "-o", out_path]
                if fmt == "png":
                    cmd += ["-b", "transparent"]
                try:
                    subprocess.run(cmd, check=True)
                    print(f"Rendered: {out_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to render '{base_name}' as {fmt} locally: {e}", file=sys.stderr)
        else:
            # Render via Kroki service
            for fmt in formats:
                try:
                    content = kroki_render(blk["source"], fmt)
                except Exception as e:
                    print(f"Kroki failed for '{base_name}' as {fmt}: {e}", file=sys.stderr)
                    # Fallback to Mermaid Ink
                    try:
                        content = ink_render(blk["source"], fmt)
                        print(f"Mermaid Ink fallback succeeded for '{base_name}' as {fmt}")
                    except Exception as e2:
                        print(f"Failed to render '{base_name}' as {fmt}: {e2}", file=sys.stderr)
                        continue
                out_path = os.path.join(output_dir, f"{base_name}.{fmt}")
                with open(out_path, "wb") as out:
                    out.write(content)
                print(f"Rendered: {out_path}")


if __name__ == "__main__":
    main()