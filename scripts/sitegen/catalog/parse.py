# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read the strict YAML subset that sites.yaml is written in.

The standard library has no YAML parser, and the build must run on a stock
runner image without PyYAML. So sites.yaml keeps to a small subset that this
module reads exactly, and refuses anything outside it with the line number,
instead of guessing. Every file it accepts is also valid YAML with the same
meaning, so PyYAML (used by the private completeness check) reads it the same
way; tests/test_catalog.py compares the two when PyYAML is installed.

The subset:
  - comments (a line whose first non-space character is #) and blank lines;
  - block mappings ("key: value", keys are lower-case words);
  - block sequences ("- ..."), whose items are mappings or scalars;
  - a key with no value opens a nested mapping or sequence, indented further
    (a sequence may also sit at the key's own indent, as YAML allows);
  - scalars: plain text, "double-quoted" text, integers, and flow lists of
    those ([a, b, "c"]).

Refused: tabs, anchors, tags, block scalars (| >), single quotes, flow
mappings, trailing comments, duplicate keys, and plain text that YAML would
read as something other than a string (true, null, 1.5, "a: b", "x #y").
Quote such text with double quotes.
"""
import re

KEY = re.compile(r"^([a-z][a-z0-9_-]*):(?: (.*))?$")
INT = re.compile(r"^-?(0|[1-9][0-9]*)$")
NUMBERISH = re.compile(r"^[-+.]?[0-9]")
SPECIAL_START = tuple("-?:,[]{}#&*!|>'\"%@`")
RESERVED = {"true", "false", "yes", "no", "on", "off", "null", "~", "y", "n"}


class CatalogError(ValueError):
    """A problem in the catalog text, with its line number."""

    def __init__(self, line, msg):
        super().__init__(f"line {line}: {msg}")
        self.line = line


def _plain(text, line):
    """Return the value of a plain scalar, or raise when YAML would read it differently."""
    if text != text.strip():
        raise CatalogError(line, f"stray spaces around {text!r}")
    if not text:
        raise CatalogError(line, "empty value (write \"\" for an empty string)")
    if INT.match(text):
        return int(text)
    if text.lower() in RESERVED:
        raise CatalogError(line, f"{text!r} is not a plain string in YAML; quote it")
    if text in ("=", "<<") or re.match(r"^[-+]?0[xXoObB]", text):
        raise CatalogError(line, f"{text!r} is not a plain string in YAML; quote it")
    if NUMBERISH.match(text) and not re.match(r"^[0-9]+[a-zA-Z]", text):
        raise CatalogError(line, f"{text!r} may read as a number in YAML; quote it")
    if text.startswith(SPECIAL_START):
        raise CatalogError(line, f"{text!r} starts with a YAML special character; quote it")
    if ": " in text or text.endswith(":") or " #" in text:
        raise CatalogError(line, f"{text!r} contains ': ' or ' #'; quote it")
    return text


def _quoted(text, line):
    """Return the value of a "double-quoted" scalar; only \\\" and \\\\ escapes."""
    if len(text) < 2 or not text.endswith('"'):
        raise CatalogError(line, f"unterminated quoted string {text!r}")
    body, out, i = text[1:-1], [], 0
    while i < len(body):
        c = body[i]
        if c == "\\":
            if i + 1 >= len(body) or body[i + 1] not in '"\\':
                raise CatalogError(line, "only \\\" and \\\\ escapes are allowed")
            out.append(body[i + 1])
            i += 2
            continue
        if c == '"':
            raise CatalogError(line, "unescaped \" inside a quoted string")
        out.append(c)
        i += 1
    return "".join(out)


def _scalar(text, line, in_flow=False):
    """Return the value of one scalar (plain, quoted or integer)."""
    if text.startswith('"'):
        return _quoted(text, line)
    if in_flow and ("," in text or "[" in text or "]" in text):
        raise CatalogError(line, f"{text!r}: quote list items that contain , [ or ]")
    return _plain(text, line)


def _value(text, line):
    """Return the value after "key: ": a scalar or a flow list."""
    if text.startswith("["):
        if not text.endswith("]"):
            raise CatalogError(line, "a flow list must end with ] on the same line")
        inner = text[1:-1].strip()
        if not inner:
            return []
        items, cur, quoted = [], "", False
        for i, c in enumerate(inner):
            if c == '"' and (i == 0 or inner[i - 1] != "\\"):
                quoted = not quoted
            if c == "," and not quoted:
                items.append(cur.strip())
                cur = ""
            else:
                cur += c
        items.append(cur.strip())
        return [_scalar(x, line, in_flow=True) for x in items]
    return _scalar(text, line)


def _lines(text):
    """Return [(line number, indent, content)] for the meaningful lines."""
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise CatalogError(n, "tab character (indent with spaces)")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw != raw.rstrip():
            raise CatalogError(n, "trailing spaces")
        if stripped == "---" or stripped.startswith(("%", "&", "*", "!", "|", ">", "{", "'")):
            raise CatalogError(n, f"unsupported YAML syntax: {stripped[:20]!r}")
        out.append([n, len(raw) - len(raw.lstrip(" ")), stripped])
    return out


def _block(lines, i, indent):
    """Parse the block starting at lines[i] (which sits at INDENT); return (node, next index)."""
    if lines[i][2] == "-" or lines[i][2].startswith("- "):
        return _sequence(lines, i, indent)
    return _mapping(lines, i, indent)


def _child(lines, i, indent, n):
    """Parse the nested block under a valueless key at INDENT, on line N."""
    if i >= len(lines):
        raise CatalogError(n, "key has no value and nothing nested under it")
    ci = lines[i][1]
    is_seq = lines[i][2] == "-" or lines[i][2].startswith("- ")
    if ci > indent or (ci == indent and is_seq):
        return _block(lines, i, ci)
    raise CatalogError(n, "key has no value and nothing nested under it")


def _mapping(lines, i, indent):
    """Parse a block mapping at INDENT."""
    out = {}
    while i < len(lines) and lines[i][1] == indent and not lines[i][2].startswith("- ") and lines[i][2] != "-":
        n, _, text = lines[i]
        m = KEY.match(text)
        if not m:
            raise CatalogError(n, f"expected 'key: value', got {text[:40]!r}")
        key, rest = m.group(1), m.group(2)
        if key in out:
            raise CatalogError(n, f"duplicate key {key!r}")
        i += 1
        if rest is None or rest == "":
            out[key], i = _child(lines, i, indent, n)
        else:
            out[key] = _value(rest, n)
    if i < len(lines) and lines[i][1] > indent:
        raise CatalogError(lines[i][0], "unexpected indentation")
    return out, i


def _sequence(lines, i, indent):
    """Parse a block sequence at INDENT; '- key: v' items become mappings."""
    out = []
    while i < len(lines) and lines[i][1] == indent and (lines[i][2] == "-" or lines[i][2].startswith("- ")):
        n, _, text = lines[i]
        rest = text[1:].lstrip(" ")
        if not rest:
            i += 1
            if i >= len(lines) or lines[i][1] <= indent:
                raise CatalogError(n, "empty list item")
            item, i = _block(lines, i, lines[i][1])
        elif KEY.match(rest):
            inner = indent + (len(text) - len(rest))
            lines[i] = [n, inner, rest]
            item, i = _mapping(lines, i, inner)
        else:
            item = _value(rest, n)
            i += 1
        out.append(item)
    if i < len(lines) and lines[i][1] > indent:
        raise CatalogError(lines[i][0], "unexpected indentation")
    return out, i


def parse(text):
    """
    SYNOPSIS
        parse(text) -> dict | list
    DESCRIPTION
        Parse TEXT, written in the subset described in this module's docstring,
        into dicts, lists, strings and ints. Raises CatalogError (with the line
        number) for anything outside the subset.
    EXAMPLE
        parse("sites:\\n  - label: icons\\n    order: 10\\n")
    """
    lines = _lines(text)
    if not lines:
        return {}
    if lines[0][1] != 0:
        raise CatalogError(lines[0][0], "the document must start at column 0")
    node, i = _block(lines, 0, 0)
    if i < len(lines):
        raise CatalogError(lines[i][0], "unexpected line (check the indentation)")
    return node
