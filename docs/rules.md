# Rule reference

All specifications are JSON objects with `version: 1` and 1–500 rules.
Every rule has a unique non-empty `id`, an `op`, optional boolean `hard`
(default true) and positive integer `weight` (default 1).

| Operator | Configuration | Pass condition |
|---|---|---|
| `contains_all` | `values`: non-empty strings | Every string occurs |
| `contains_any` | `values`: non-empty strings | At least one string occurs |
| `excludes` | `values`: non-empty strings | None occurs |
| `regex` | `pattern`: valid Python regex | At least one multiline match |
| `length` | `min`, `max`, `unit` | Count is within inclusive bounds |
| `footnotes` | None | No missing, unused or duplicate definitions |
| `sha256` | `value`: 64 lowercase hex characters | Exact UTF-8 hash matches |

String checks are case-sensitive and apply to the whole document, including
footnotes. A required string occurring in a negated sentence still matches.
Regex uses Python `re` with MULTILINE, without IGNORECASE or DOTALL.

Length units: `characters` counts Unicode code points; `words` splits on
whitespace; `chinese` counts U+4E00–U+9FFF characters. This is not a linguistic
word counter. Default bounds are 0 to 200,000, the maximum input length.

Footnotes use line-start definitions such as `[^source]: Example source`.
All references must have exactly one definition, and every definition must be
used. Markdown code blocks and multiline nested definitions are not parsed.

Input is decoded as UTF-8 (optional BOM removed). SHA-256 is calculated from the
decoded text encoded as UTF-8, with Python's normal newline translation. A hash
is therefore a content check, not a byte-for-byte original-file checksum.

For JSON and HTML, `--output` writes a report; without it the report prints to
stdout. A batch exits `1` if any document fails a hard rule.
