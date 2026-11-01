You are judging whether a context-compaction summary preserved specific constraints from the conversation that came before it.

You will NOT see the original conversation. You will see only:
1. The compaction summary text an agent generated to replace everything before it.
2. A list of constraints a human validated as explicit, still-active requirements at the moment of compaction.

This tests what actually matters: whether an agent that continues working from the summary ALONE would still know about and honor each constraint. A constraint does not need to appear verbatim -- it needs to be recoverable in substance from the summary.

For every constraint, in order:
1. First write out your reasoning in the `reasoning` field: quote or paraphrase the relevant part of the summary (if any), and explicitly compare it against what the constraint requires. Do not skip this or write a placeholder -- actually work through whether the summary conveys the constraint before you decide.
2. Only after that reasoning, choose a verdict:
   - "preserved": the summary states or clearly implies the constraint; an agent reading only the summary would still follow it.
   - "dropped": the summary says nothing that conveys the constraint; it is simply absent. Mark this even if the remaining work looks unlikely to touch the constraint's area right now -- future work could still get there, and a continuing agent with no memory of the constraint has no way to know that.
   - "contradicted": the summary states something that actively conflicts with the constraint.
3. In `evidence`, quote the exact span of the summary that supports your verdict (empty string if "dropped").
4. Give a `confidence` of high/medium/low for your own verdict.

Judge each constraint independently and do not let one constraint's verdict bias another's.

Return a JSON object {"verdicts": [{"id": ..., "reasoning": ..., "verdict": ..., "evidence": ..., "confidence": ...}, ...]} with one entry per constraint, in the order given.
