Subject: Re: Triage prompt for donate@ inbox

Hi Marcus,

Thanks for the welcome. Attached are the rewritten prompt (triage_prompt.md), the evaluation note (eval_note.md), and the six re-triaged replies (corrections.csv, header and email column untouched). I also attached eval_results.csv, which is the output of a test run you can show the board.

What went wrong: the old prompt told the model what to promise. "Bring it anytime," "we'll add it to their next delivery," and "never turn anyone away" are instructions, and the six flagged replies are those instructions being followed. Both of the incidents on tomorrow's agenda come from the same line of text.

What the new prompt does differently:

- It can only state facts from a short list at the top of the prompt. Anything not on the list becomes "a member of our team will confirm that with you."
- Every category has one fixed route. Only individual drop-off questions that are fully answered from the fact list can go out without a human reading them.
- Replies to anything routed to a person are holding replies. They restate what was asked and say someone will follow up. No timelines, no commitments, no "we've forwarded this."
- Output is one JSON block with the four fields you specified. No prose.

I tested it on Haiku against your six emails plus the 40-email inbox sample. All 46 produced valid JSON. Category and urgency matched my expected labels on all 46, and routing matched on 45. The one difference was the prompt sending a baby formula question to Priya instead of auto-replying, because formula wasn't in the fact list. That is the safety rule doing its job.

Two things I need from you before this goes live:

1. Fill in the fact list at the top of the prompt: warehouse address, drop-off hours, what you accept and don't accept from individuals, the intake line number, and the volunteer sign-up contact. The old prompt said 8am to 6pm every day, but I didn't want to assume that was right. Until these are filled in, every individual drop-off reply routes to Priya instead of going out automatically. Safe, but slower.

2. Confirm the routing: corporate offers and partner agencies to you, volunteers and food drives to Priya, press to Diane. The old prompt sent press to you, so change that back if you prefer. Each is a one-word edit in the routing table.

The eval note has a 30-minute test you can run once the facts are filled in, and a five-minute weekly check after launch. Happy to rerun my test against the finished version as soon as you send it back.

Thanks,
[Your name]
