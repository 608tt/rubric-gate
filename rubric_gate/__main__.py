import argparse
import html
import json
from pathlib import Path
from .core import evaluate


def render_html(reports):
    cards = []
    for report in reports:
        rows = "".join(f'<tr><td>{html.escape(row["id"])}</td><td>{"hard" if row["hard"] else "soft"}</td>'
                       f'<td>{"PASS" if row["passed"] else "FAIL"}</td><td><code>{html.escape(json.dumps(row["detail"], ensure_ascii=False))}</code></td></tr>'
                       for row in report["rules"])
        cards.append(f'<section><h2>{html.escape(report["name"])}</h2><p class="result">'
                     f'{"ACCEPTED" if report["accepted"] else "BLOCKED"} · {report["score"]}% rule satisfaction</p>'
                     f'<p class="hash">SHA-256: {report["sha256"]}</p><table><thead><tr><th>Rule</th><th>Gate</th><th>Result</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Rubric Gate · Acceptance report</title><style>body{background:#141826;color:#e9edfc;font:15px/1.6 system-ui;margin:0}main{max-width:1100px;margin:50px auto;padding:0 24px}h1{font-size:56px;letter-spacing:-.04em;line-height:1.1}h2{font-size:24px}.eyebrow{color:#a9a9ff;text-transform:uppercase;letter-spacing:.18em;font-size:12px}section{background:#1d2336;border:1px solid #343d56;border-radius:16px;margin-top:25px;padding:28px;overflow:auto}.result{color:#c5d697;font-weight:700}.hash{font-size:11px;overflow-wrap:anywhere;color:#a2aec7}table{width:100%;border-collapse:collapse;text-align:left}td,th{padding:12px;border-bottom:1px solid #343d56}code{white-space:pre-wrap;color:#b4bfe8}@media(max-width:600px){h1{font-size:36px}section{padding:16px}}</style><main><p class="eyebrow">Offline · Deterministic · CI-ready</p><h1>Hard rules.<br>Clear acceptance.</h1><p>A failed hard rule blocks acceptance, even when the overall score is high.<br>These checks do not measure semantic quality or factual accuracy.</p>''' + "".join(cards) + "</main></html>"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic text checks with hard acceptance gates")
    parser.add_argument("documents", type=Path, nargs="+")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--format", choices=["json", "html"], default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        reports = [evaluate(path.read_text(encoding="utf-8-sig"), spec, path.name) for path in args.documents]
        result = json.dumps({"reports": reports}, ensure_ascii=False, indent=2) if args.format == "json" else render_html(reports)
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result)
        return 0 if all(report["accepted"] for report in reports) else 1
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
