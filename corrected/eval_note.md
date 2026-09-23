# donate@ triage prompt — what changed and how to evaluate it

## Why the six replies were wrong (root cause, not symptoms)

The old prompt told the model what to promise: "bring it to our warehouse anytime", "we'll add it to their next delivery", "never turn anyone away". Both board-agenda incidents are that text doing exactly what it was told. The six flagged replies fail in four ways:

1. Invented facts. Ana got a walk-in process, an ID requirement, and an address placeholder. Jen got a fake "attached" needs list.
2. Invented commitments and timelines. Kevin was promised an answer "within the next few hours". Pastor Dan was told "we absolutely want to make sure Crossroads is fully stocked". Jen was told "we'd love to have your 18 students".
3. Wrong output shape. The spam email produced a prose triage summary instead of an empty draft. Sarah's draft had markdown bold that pastes badly into Gmail.
4. One category miss. Jen's email is a food drive plus a volunteer ask; only volunteering was tagged. Nothing was routed to anyone, so nothing could be caught.

## What the new prompt does differently

- Section 1 is a closed list of facts. The model may only state what is written there. Anything else becomes "a member of our team will confirm that with you" and the email cannot go out as auto_ok. Fill Section 1 before pasting; anything left blank is safe by design, just less helpful.
- Every category has one fixed route. auto_ok is allowed only for individual drop-off questions fully answered from Section 1.
- Drafts for anything routed to a person are holding replies: restate the ask, say the right person will follow up, stop. No "when", no "who", no "we forwarded it".
- Urgent has a checklist definition (deadline within 3 business days, perishable offer, partner shortage, immediate need, press or board). Food assistance seekers are not urgent by default because intake_line is already the fastest path; flip that one line if you disagree.
- JSON only, four keys, with six worked examples so Haiku has the shape in front of it.

Routing assumptions to confirm: corporate and partner agency go to marcus, volunteers and food drives to priya, media to diane. The old prompt sent press to Marcus; I moved it to Diane since press and reputational items belong with the executive. Each is a one-word edit in the Section 4 table.

## How to evaluate it (about 30 minutes, then 5 minutes a week)

1. Golden set. inbox_sample.csv has 40 emails and is already a decent test set: it contains near-duplicate bodies from different senders (S25/S27), subject lines that disagree with bodies (S01 to S04), non-food items mixed into drop-off questions, and a vendor pitch titled "Partnership opportunity". eval_labels.csv is my expected label for each of the 40 plus a reason. Disagree with any label, change the file, that is the point.
2. Run. Paste each email into the Project and record the four JSON fields. On Haiku this is cheap enough to run the full 40 each time the prompt changes.
3. Score four things, in this order of importance:
   - Route accuracy: correct route_to on all 40. This is the number the board cares about. Any auto_ok that should have been a person is a hard fail.
   - Commitment check on drafts: search every draft for promise words: "we'll", "we will", "anytime", "add to", "attached", "forwarded", "within", "right away", "we'd love to have". Target is zero hits on routed emails.
   - Category and urgent accuracy: target 38 of 40 or better on category. Urgent misses on volunteer deadlines are tolerable; urgent misses on corporate offers are not.
   - Format: 40 of 40 parse as JSON with exactly four keys, urgent is a boolean, spam drafts are empty, no markdown in any draft. One bad parse and the volunteer is back to copying by hand.
4. Consistency: identical bodies (S25 and S27, S21 and S23) must produce identical category, urgent, and route. If they do not, the prompt is under-specified for that case.
5. Weekly after launch: every reply that a human edited before sending goes into failure_examples.md with the fix. Once a month, re-run the 40 plus the new failures. Add a worked example to Section 7 only when a failure repeats.

Pass bar for tomorrow: 40 of 40 routes, zero promise words in routed drafts, 40 of 40 valid JSON. If it misses, the fix is almost always one more line in Section 3 or 4, not a rewrite.

## Result of my own run (Haiku, all 46 emails)

I ran the six failures plus the 40-email sample through Haiku 4.5 with a test copy of the prompt whose facts block held placeholder values. Full output is in eval_results.csv.

| check | result |
|---|---|
| valid JSON, four keys, boolean urgent | 46 / 46 |
| category | 46 / 46 |
| urgent | 46 / 46 |
| route_to | 45 / 46 |
| promise words in routed drafts | 0 |
| markdown in drafts, non-empty spam drafts | 0 |

The one route miss was S11 (sparkling water plus baby formula). My placeholder facts said nothing about formula, so the model deferred that question and sent it to priya instead of auto_ok. That is the missing-fact rule working as intended, not a bug. Note for the promise-word search: "within" also matches "within its best-by date", so read hits before counting them.
