"""Build demo/index.html from demo/template.html.

Injects the triage prompt (facts block filled from test_facts.json), the six
failure emails with the old prompt's output and the recorded Haiku result from
the last run_eval.py run, and the repository URL.
"""
import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_eval import SIX, fill_prompt, HERE

REPO_URL = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/wolfwdavid/riverbend-donate-triage"
LABELS = {"kevin": "Kevin (22 pallets)", "sarah": "Sarah (drop-off)", "pastor_dan": "Pastor Dan (allocation)",
          "spam": "GrantStation (spam)", "jen": "Jen (NHS + food drive)", "ana": "Ana Lucía (ayuda)"}
ORDER = ["kevin", "pastor_dan", "sarah", "jen", "ana", "spam"]

prompt = fill_prompt((HERE / "triage_prompt.md").read_text(encoding="utf-8"),
                     json.load(open(HERE / "test_facts.json", encoding="utf-8")))

# old outputs, parsed from failure_examples.md in document order
fe = (HERE / "failure_examples.md").read_text(encoding="utf-8")
blocks = re.split(r"^## Email \d+\s*$", fe, flags=re.M)[1:]
old = {}
for key, block in zip(["kevin", "sarah", "pastor_dan", "spam", "jen", "ana"], blocks):
    m = re.search(r"\*\*Current output:\*\*\s*(.*)$", block, re.S)
    text = m.group(1).strip() if m else ""
    text = text.replace("Draft reply: *\"", "Draft reply:\n").rstrip("*\" \n").rstrip('"*')
    old[key] = re.sub(r"^\s*-\s*", "", text, flags=re.M).strip()

recorded = {}
p = HERE / "build" / "eval_results.json"
if p.exists():
    for r in json.load(open(p, encoding="utf-8")):
        if r["id"] in SIX and r["fmt_ok"]:
            recorded[r["id"]] = {"category": r["got_cat"], "urgent": r["got_urg"], "route_to": r["got_route"], "draft": r["draft"]}

examples = []
for k in ORDER:
    frm, sub, body = SIX[k]
    examples.append({"id": k, "label": LABELS[k], "from": frm, "subject": sub, "body": body,
                     "old": old.get(k, ""), "recorded": recorded.get(k)})

html = (HERE / "demo" / "template.html").read_text(encoding="utf-8")
assert "</script" not in prompt
html = html.replace("__PROMPT__", prompt)
html = html.replace("__EXAMPLES__", json.dumps(examples, ensure_ascii=False).replace("</", "<\\/"))
html = html.replace("__REPO_URL__", REPO_URL)
out = HERE / "demo" / "index.html"          # body only: the Artifact tool adds the document skeleton
out.write_text(html, encoding="utf-8")

# GitHub Pages copy: standalone document with its own skeleton; <title> and the font <link> move into <head>
title = re.search(r"<title>.*?</title>", html).group(0)
link = re.search(r'<link rel="stylesheet"[^>]*>', html).group(0)
body_html = html.replace(title, "", 1).replace(link, "", 1)
pages = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
         '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
         + title + "\n" + link + "\n"
         '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
         "</head>\n<body>\n" + body_html + "\n</body>\n</html>\n")
docs = HERE / "docs"; docs.mkdir(exist_ok=True)
(docs / "index.html").write_text(pages, encoding="utf-8")
(docs / ".nojekyll").write_text("", encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes) and docs/index.html ({(docs / 'index.html').stat().st_size} bytes); "
      f"recorded results for {sorted(recorded)}")
