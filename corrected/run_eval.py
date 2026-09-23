import csv, json, os, re, subprocess, sys, pathlib, concurrent.futures as cf
SP = pathlib.Path(sys.argv[1]); PROJ = pathlib.Path(sys.argv[2])
prompt = (SP / "triage_prompt_filled.md").read_text(encoding="utf-8")
MODEL = "claude-haiku-4-5-20251001"

# --- the six failure emails ---
six = {
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
cases = []
with open(PROJ / "corrections.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        fr, sub, body = six[r["email"]]
        cases.append(dict(id=r["email"], set="six", frm=fr, subject=sub, body=body,
                          exp_cat=r["correct_category"], exp_urg=r["urgent"]=="yes", exp_route=r["route_to"]))
labels = {}
with open(PROJ / "eval_labels.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f): labels[r["id"]] = r
with open(PROJ / "inbox_sample.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        L = labels[r["id"]]
        cases.append(dict(id=r["id"], set="inbox", frm=r["from"], subject=r["subject"], body=r["body"],
                          exp_cat=L["expected_category"], exp_urg=L["expected_urgent"]=="yes", exp_route=L["expected_route_to"]))

env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
def run(c):
    msg = f"From: {c['frm']}\nSubject: {c['subject']}\n\n{c['body']}"
    p = subprocess.run(["C:/Users/Mkaru/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe", "-p", msg, "--model", MODEL, "--system-prompt-file", str(SP / "triage_prompt_filled.md"), "--tools", "",
                        "--no-session-persistence"], capture_output=True, text=True, encoding="utf-8",
                       stdin=subprocess.DEVNULL, env=env, timeout=180)
    return c, p.stdout, p.stderr

PROMISE = re.compile(r"\b(we'll|we will|anytime|add (it )?to|attached|attaching|forwarded|forwarding|within|right away|we'd love to have|absolutely)\b", re.I)
results = []
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for c, out, err in ex.map(run, cases):
        raw = out.strip()
        m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.S)
        ok = False; obj = None; fmt_err = ""
        try:
            obj = json.loads(m.group(1) if m else raw)
            keys = list(obj.keys())
            if keys != ["category","urgent","route_to","draft"]: fmt_err = f"keys={keys}"
            elif not isinstance(obj["urgent"], bool): fmt_err = "urgent not bool"
            elif not m: fmt_err = "no ```json fence"
            else: ok = True
        except Exception as e:
            fmt_err = f"parse: {e}; raw={raw[:120]!r}; err={err.strip()[-200:]!r}"
        d = (obj or {}).get("draft", "") or ""
        md = bool(re.search(r"(\*\*|^#|^- |^\* |^Subject:)", d, re.M))
        r = dict(id=c["id"], set=c["set"], fmt_ok=ok, fmt_err=fmt_err,
                 exp_cat=c["exp_cat"], got_cat=(obj or {}).get("category"),
                 exp_urg=c["exp_urg"], got_urg=(obj or {}).get("urgent"),
                 exp_route=c["exp_route"], got_route=(obj or {}).get("route_to"),
                 promise=";".join(sorted(set(x.group(0).lower() for x in PROMISE.finditer(d)))),
                 markdown=md, spam_empty=(c["exp_cat"]!="spam_no_reply" or d==""), draft=d)
        results.append(r)
        print(f"{c['id']:<11} {'OK ' if ok else 'BAD'} cat={'ok' if r['got_cat']==c['exp_cat'] else 'MISS:'+str(r['got_cat'])} "
              f"urg={'ok' if r['got_urg']==c['exp_urg'] else 'MISS:'+str(r['got_urg'])} "
              f"route={'ok' if r['got_route']==c['exp_route'] else 'MISS:'+str(r['got_route'])} "
              f"promise={r['promise'] or '-'} md={md}", flush=True)
results.sort(key=lambda r: (r["set"]!="six", r["id"]))
with open(SP / "eval_results.json", "w", encoding="utf-8") as f: json.dump(results, f, ensure_ascii=False, indent=1)
n = len(results)
print("\n=== SUMMARY ===")
print("format ok      :", sum(r["fmt_ok"] for r in results), "/", n)
print("category ok    :", sum(r["got_cat"]==r["exp_cat"] for r in results), "/", n)
print("urgent ok      :", sum(r["got_urg"]==r["exp_urg"] for r in results), "/", n)
print("route ok       :", sum(r["got_route"]==r["exp_route"] for r in results), "/", n)
print("promise hits   :", sum(bool(r["promise"]) for r in results))
print("markdown drafts:", sum(r["markdown"] for r in results))
print("spam non-empty :", sum(not r["spam_empty"] for r in results))
bad_auto = [r["id"] for r in results if r["got_route"]=="auto_ok" and r["exp_route"]!="auto_ok"]
print("auto_ok that should be a person:", bad_auto or "none")
