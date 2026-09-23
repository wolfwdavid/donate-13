"""Run the donate@ triage prompt on Haiku against the six failure emails and the
40-email inbox sample, then score the output against the expected labels.

Usage:
    python run_eval.py                 # uses triage_prompt.md with test_facts.json filled in
    python run_eval.py --no-fill       # run the prompt exactly as written (blank facts block)
    python run_eval.py --workers 4

Needs either ANTHROPIC_API_KEY (uses the anthropic SDK) or a logged-in Claude
Code CLI on PATH (falls back to `claude -p`). Writes eval_results.csv.
"""
import argparse, concurrent.futures as cf, csv, json, os, re, shutil, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
MODEL = "claude-haiku-4-5-20251001"

SIX = {
    "kevin": ("Kevin Walsh <kwalsh@midstatebev.com>", "Short-dated product — 22 pallets sparkling water, need answer by Wed",
              "Hi — we have 22 pallets of flavored sparkling water (best-by 6 weeks out) at our Linden DC. We can deliver to you Thursday AM if you can take it, otherwise it's getting dumped Wednesday night. Can you confirm dock space + whether you accept short-dated beverage? Need a yes/no by EOD Wednesday. — Kevin, Midstate Beverage"),
    "sarah": ("Sarah M <sarahm1987@gmail.com>", "cleaning out pantry",
              "hi, I have some canned goods and pasta I'd like to donate, where can I drop them off? thanks!"),
    "pastor_dan": ("Pastor Daniel Reyes <office@crossroadsmission.org>", "URGENT — Crossroads pantry allocation",
                   "Marcus — our Thursday distribution served 112 families last week, up from ~70. We ran out by 10:30am. Can we get an extra half-pallet of produce and 4 more cases of protein on this week's delivery? I know it's late to ask. — Pastor Dan"),
    "spam": ("noreply@grantstation.com", "🎯 Kevin, 47 New Grants Match Your Profile This Week!",
             "[marketing email body: GrantStation weekly digest — 47 new grants match your profile, click to view, upgrade to Premium for full access, unsubscribe link]"),
    "jen": ("Jen Park <jpark@lincolnhs.edu>", "NHS volunteer hours + food drive question",
            "Hi! I'm the National Honor Society advisor at Lincoln HS. Two things — (1) we have 18 students who need volunteer hours before May 15, can we set up a warehouse shift? (2) we also want to run a food drive the first week of May — is there a list of items you actually need? Last year we got a lot of stuff you apparently couldn't use."),
    "ana": ("Ana Lucía Torres <atorres.community@gmail.com>", "ayuda con comida",
            "Hola, una amiga me dijo que ustedes ayudan con comida. Tengo tres niños y este mes está difícil. ¿Cómo funciona? ¿Tengo que llenar algo? Gracias."),
}

PROMISE = re.compile(r"\b(we'll|we will|anytime|add (it )?to|attached|attaching|forwarded|forwarding|right away|we'd love to have|absolutely|within (the next|a few|an hour|24))\b", re.I)


def fill_prompt(text: str, facts: dict) -> str:
    """Replace each `- KEY: [FILL IN ...]` line in Section 1 with the test value."""
    for key, value in facts.items():
        if key.startswith("_"):
            continue
        text, n = re.subn(r"(- " + re.escape(key) + r": )\[FILL IN[^\]]*\]", lambda m: m.group(1) + value, text)
        if n != 1:
            raise SystemExit(f"fact line not found exactly once in prompt: {key}")
    return text


def load_cases():
    cases = []
    with open(HERE / "corrections.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            frm, sub, body = SIX[r["email"]]
            cases.append(dict(id=r["email"], frm=frm, subject=sub, body=body,
                              exp_cat=r["correct_category"], exp_urg=r["urgent"] == "yes", exp_route=r["route_to"]))
    labels = {}
    with open(HERE / "eval_labels.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            labels[r["id"]] = r
    with open(HERE / "inbox_sample.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            L = labels[r["id"]]
            cases.append(dict(id=r["id"], frm=r["from"], subject=r["subject"], body=r["body"],
                              exp_cat=L["expected_category"], exp_urg=L["expected_urgent"] == "yes", exp_route=L["expected_route_to"]))
    return cases


def make_runner(system_prompt: str):
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()

        def run(msg):
            r = client.messages.create(model=MODEL, max_tokens=800, system=system_prompt,
                                       messages=[{"role": "user", "content": msg}])
            return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return run

    exe = None
    npm_exe = pathlib.Path.home() / "AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
    if sys.platform == "win32" and npm_exe.exists():
        exe = str(npm_exe)  # the npm .cmd shim goes through cmd.exe, whose 8K arg limit breaks long prompts
    else:
        exe = shutil.which("claude")
    if not exe:
        raise SystemExit("Set ANTHROPIC_API_KEY or install the Claude Code CLI.")
    prompt_file = HERE / "build" / "triage_prompt_test.md"
    prompt_file.parent.mkdir(exist_ok=True)
    prompt_file.write_text(system_prompt, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    def run(msg):
        p = subprocess.run([exe, "-p", msg, "--model", MODEL, "--system-prompt-file", str(prompt_file),
                            "--tools", "", "--no-session-persistence"],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL, env=env, timeout=180)
        return p.stdout
    return run


def score(case, raw):
    m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.S)
    obj, ok, err = None, False, ""
    try:
        obj = json.loads(m.group(1) if m else raw.strip())
        if list(obj.keys()) != ["category", "urgent", "route_to", "draft"]:
            err = f"keys={list(obj.keys())}"
        elif not isinstance(obj["urgent"], bool):
            err = "urgent not bool"
        else:
            ok = True
    except Exception as e:
        err = f"parse: {e}"
    obj = obj or {}
    d = obj.get("draft") or ""
    return dict(id=case["id"], fmt_ok=ok, fmt_err=err,
                exp_cat=case["exp_cat"], got_cat=obj.get("category"),
                exp_urg=case["exp_urg"], got_urg=obj.get("urgent"),
                exp_route=case["exp_route"], got_route=obj.get("route_to"),
                promise=";".join(sorted({x.group(0).lower() for x in PROMISE.finditer(d)})),
                markdown=bool(re.search(r"(\*\*|^#|^- |^\* |^Subject:)", d, re.M)),
                spam_empty=(case["exp_cat"] != "spam_no_reply" or d == ""), draft=d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fill", action="store_true", help="run the prompt as written, facts block blank")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    prompt = (HERE / "triage_prompt.md").read_text(encoding="utf-8")
    if not args.no_fill:
        prompt = fill_prompt(prompt, json.load(open(HERE / "test_facts.json", encoding="utf-8")))
    run = make_runner(prompt)
    cases = load_cases()

    def one(c):
        msg = f"From: {c['frm']}\nSubject: {c['subject']}\n\n{c['body']}"
        return score(c, run(msg))

    results = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(one, cases):
            results.append(r)
            print(f"{r['id']:<11} {'OK ' if r['fmt_ok'] else 'BAD'} "
                  f"cat={'ok' if r['got_cat'] == r['exp_cat'] else 'MISS:' + str(r['got_cat'])} "
                  f"urg={'ok' if r['got_urg'] == r['exp_urg'] else 'MISS:' + str(r['got_urg'])} "
                  f"route={'ok' if r['got_route'] == r['exp_route'] else 'MISS:' + str(r['got_route'])} "
                  f"promise={r['promise'] or '-'} md={r['markdown']}", flush=True)

    order = {c["id"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: order[r["id"]])
    with open(HERE / "eval_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "expected_category", "got_category", "expected_urgent", "got_urgent",
                    "expected_route_to", "got_route_to", "match", "draft"])
        for r in results:
            match = r["got_cat"] == r["exp_cat"] and r["got_urg"] == r["exp_urg"] and r["got_route"] == r["exp_route"]
            w.writerow([r["id"], r["exp_cat"], r["got_cat"], "yes" if r["exp_urg"] else "no", "yes" if r["got_urg"] else "no",
                        r["exp_route"], r["got_route"], "yes" if match else "no", r["draft"]])
    (HERE / "build").mkdir(exist_ok=True)
    json.dump(results, open(HERE / "build" / "eval_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    n = len(results)
    print("\n=== SUMMARY ===")
    print("format ok      :", sum(r["fmt_ok"] for r in results), "/", n)
    print("category ok    :", sum(r["got_cat"] == r["exp_cat"] for r in results), "/", n)
    print("urgent ok      :", sum(r["got_urg"] == r["exp_urg"] for r in results), "/", n)
    print("route ok       :", sum(r["got_route"] == r["exp_route"] for r in results), "/", n)
    print("promise hits   :", sum(bool(r["promise"]) for r in results))
    print("markdown drafts:", sum(r["markdown"] for r in results))
    print("spam non-empty :", sum(not r["spam_empty"] for r in results))
    bad_auto = [r["id"] for r in results if r["got_route"] == "auto_ok" and r["exp_route"] != "auto_ok"]
    print("auto_ok that should be a person:", bad_auto or "none")


if __name__ == "__main__":
    main()
