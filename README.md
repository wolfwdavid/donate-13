# Riverbend donate@ inbox triage

A rewritten Claude Project prompt for triaging a food bank's shared donation inbox, plus the evaluation set and harness that show it works on Claude Haiku.

The previous prompt told the model what to promise ("bring it anytime", "we'll add it to your next delivery"). The replies it produced committed the organisation to allocations and drop-offs it could not honour. The new prompt turns the model into a sorting and drafting tool that may only state facts from a closed list, routes every email to a fixed owner, and writes holding replies that promise nothing.

Live demo, two hosts:

- GitHub Pages: https://wolfwdavid.github.io/donate-13/ (bring your own Anthropic API key to run live; recorded results show without one)
- Claude artifact: https://claude.ai/artifact/TS466GwxdbTvx6DuCVGYnZ (runs on the viewer's own Claude account, invite-only)

> Note: this repository is public until the owner is cued in to make it private. It contains only a fictional exercise; no real organisation, people, keys or addresses.

## Files

| file | what it is |
|---|---|
| `triage_prompt.md` | The Project system prompt. Fill the `[FILL IN]` lines in Section 1 before use. |
| `eval_note.md` | One page on why the old replies failed, what changed, and how to evaluate the prompt. |
| `corrections.csv` | The six flagged emails re-triaged by hand. |
| `eval_labels.csv` | Expected category, urgency and route for the 40-email `inbox_sample.csv`. |
| `eval_results.csv` | Output of the last Haiku run against all 46 emails. |
| `run_eval.py` | Harness: runs every email through Haiku and scores it against the labels. |
| `test_facts.json` | Placeholder values for the facts block, used only when testing. |
| `demo/` | A single-page live demo that runs the prompt on Claude's quick tier from the browser. |
| `current_prompt.md`, `failure_examples.md`, `inbox_sample.csv` | The original inputs. |
| `corrected/` | The deliverables as sent, frozen. |

## Output contract

For each email the prompt returns exactly one JSON object:

```json
{"category": "...", "urgent": true, "route_to": "...", "draft": "..."}
```

Categories: `corporate_food_donation`, `individual_food_donation`, `partner_agency_request`, `food_assistance_seeker`, `volunteer_inquiry`, `food_drive`, `media_or_general_inquiry`, `spam_no_reply`.

Routes: `marcus`, `diane`, `priya`, `intake_line`, `auto_ok`, `no_reply`.

## Last run

Haiku 4.5, all 46 emails, facts block filled with the placeholder values in `test_facts.json`.

| check | result |
|---|---|
| valid JSON, four keys, boolean urgent | 46 / 46 |
| category | 46 / 46 |
| urgent | 46 / 46 |
| route_to | 45 / 46 |
| promise words in routed drafts | 0 |
| markdown in drafts, non-empty spam drafts | 0 |

The one route difference is S11 (sparkling water plus baby formula). The placeholder facts say nothing about formula, so the model deferred the question and routed to a person instead of auto-replying. That is the missing-fact rule working as designed.

## Reproduce

```
python run_eval.py            # facts block filled from test_facts.json
python run_eval.py --no-fill  # prompt exactly as written
```

Needs `ANTHROPIC_API_KEY` (uses the `anthropic` SDK) or a logged-in Claude Code CLI on PATH. Writes `eval_results.csv` and `build/eval_results.json`.

To rebuild the demo page after changing the prompt or rerunning the eval:

```
python build_demo.py
```
