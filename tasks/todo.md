# Donate@ triage rewrite — plan

- [x] Read current_prompt.md, failure_examples.md, inbox_sample.csv, corrections.csv
- [x] Diagnose each of the six failures (category / urgent / route / draft)
- [x] Write triage_prompt.md (Haiku-friendly, JSON-only, facts block, routing table, examples)
- [x] Fill corrections.csv (header + email column untouched)
- [x] Write eval_note.md (one page) + eval_labels.csv golden set from inbox_sample.csv
- [x] Run the six failures through Haiku with the new prompt and check the JSON
- [x] Review section below

## Review

- triage_prompt.md: rewritten as a closed facts block, eight fixed categories, checklist urgency, fixed routing table, holding-reply draft rules, six worked examples, JSON-only output.
- corrections.csv: six rows filled; header and email column untouched.
- eval_note.md + eval_labels.csv: one-page evaluation method plus a 40-email golden set.
- Verification: ran all 46 emails through Haiku 4.5 via the Claude CLI (native exe + --system-prompt-file) with placeholder facts filled in. 46/46 valid JSON, 46/46 category, 46/46 urgent, 45/46 route (the miss is the safe-side downgrade from auto_ok to priya on an item the facts did not cover). Zero promise words, zero markdown, spam drafts empty. Results in eval_results.csv.
- Open decision for Marcus: press is routed to diane; the old prompt sent it to marcus. One-word edit in Section 4.
- Before pasting: fill the [FILL IN] lines in Section 1. Until then every individual drop-off reply routes to priya instead of going out automatically, which is safe but slower.

## Follow-up (2026-09-23)

- [x] corrected/ folder with the deliverables as sent
- [x] Live demo page published (artifact TS466GwxdbTvx6DuCVGYnZ, sample capability, quick tier)
- [x] GitHub repo wolfwdavid/donate-13 (private)
- [ ] Live run on the demo page not yet exercised by a viewer click
