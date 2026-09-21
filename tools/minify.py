#!/usr/bin/env python3
"""Safe Python script minifier for NumWorks MicroPython.

Strips comments, docstrings, and blank lines while strictly preserving
indentation and semantic correctness.

Usage:
    python3 tools/minify.py input.py [output.py]
    python3 tools/minify.py --in-place script.py
"""

import sys
import io
import tokenize


def minify_python(source: str) -> str:
    """Safely minify Python code by removing comments, docstrings, and empty lines.

    Preserves exact indentation and token structure.
    """
    io_obj = io.BytesIO(source.encode("utf-8"))
    comments = []
    docstrings = []
    prev_tok_type = None

    try:
        for tok in tokenize.tokenize(io_obj.readline):
            tok_type = tok.type
            if tok_type == tokenize.COMMENT:
                comments.append((tok.start, tok.end))
            elif tok_type == tokenize.STRING:
                # Standalone string right after INDENT or at line start is a docstring
                if prev_tok_type in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.ENCODING) or prev_tok_type is None:
                    docstrings.append((tok.start, tok.end))
            if tok_type not in (tokenize.NL, tokenize.COMMENT):
                prev_tok_type = tok_type
    except tokenize.TokenError:
        pass

    lines = source.splitlines()

    # Blank out docstring ranges
    for (sline, scol), (eline, ecol) in docstrings:
        if sline == eline:
            lines[sline - 1] = lines[sline - 1][:scol] + lines[sline - 1][ecol:]
        else:
            lines[sline - 1] = lines[sline - 1][:scol]
            for l in range(sline, eline - 1):
                lines[l] = ""
            lines[eline - 1] = lines[eline - 1][ecol:]

    # Strip comments from end of lines
    for (sline, scol), (eline, ecol) in reversed(comments):
        idx = sline - 1
        if idx < len(lines):
            lines[idx] = lines[idx][:scol]

    # Filter out empty or whitespace-only lines
    res = [l.rstrip() for l in lines if l.strip()]
    return "\n".join(res) + "\n"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [--in-place] <input.py> [output.py]")
        sys.exit(1)

    in_place = False
    args = sys.argv[1:]
    if args[0] == "--in-place":
        in_place = True
        args = args[1:]

    input_path = args[0]
    output_path = args[1] if len(args) > 1 else (input_path if in_place else None)

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    minified = minify_python(source)

    # Validate syntax of minified output
    try:
        compile(minified, output_path or "<minified>", "exec")
    except SyntaxError as e:
        print(f"Error: Minification produced invalid syntax on line {e.lineno}: {e.msg}", file=sys.stderr)
        sys.exit(1)

    orig_size = len(source.encode("utf-8"))
    min_size = len(minified.encode("utf-8"))
    saved = orig_size - min_size
    pct = (saved / orig_size) * 100 if orig_size else 0

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(minified)
        print(f"Minified {input_path} -> {output_path}")
        print(f"  {orig_size:,} B -> {min_size:,} B (saved {saved:,} B, {pct:.1f}%)")
    else:
        sys.stdout.write(minified)


if __name__ == "__main__":
    main()
