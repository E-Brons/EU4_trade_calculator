---
name: research-loop
description: Run the EU4 trade research loop end to end - take a trade-mechanics question from the user, formalise it into a research goal, get a draft from a research agent, iterate request/response rounds until every point is clear and evidence-based, then write the final document. Use when the user asks a new question about how EU4 trade works, or asks to continue/finish a topic under docs/research.
---

# Research loop (docs/research)

Follow the file convention in `docs/research/README.md` (goal -> draft -> request_i/response_i -> final; flat folder; append-only). Read that README first every time: it holds the rules and the status table you must keep current.

Arguments: a question in free text, or an existing topic id (`R15`, `R10`) to continue. With no argument, ask for the question.

## 0. Orient
- Read `docs/research/README.md`. List `docs/research` to find the topic's newest file (status = newest file) or the next free `Rxx`.
- New question: continue at step 1. Existing topic: jump to the step matching its newest file (goal -> step 3, draft/response -> step 4, request -> step 5, final -> report, nothing to do).

## 1. Ask the user (only what you cannot infer)
Use AskUserQuestion, at most one round of 1-4 questions. Settle:
- the question in the user's words, and what decision in the calculator depends on it (which stage of `backend/app/trade/calc.py` or which failing stage in `docs/trade_testing.md`);
- which save fields are involved and whether a data table from the saves helps (ask only if not obvious);
- who runs the research: `agent` (you spawn a research subagent with web tools) or `manual` (the user gives files to another assistant such as GitLab Duo and saves the replies; you then wait for them). Default `agent`.
Do not ask about things the repo answers.

## 2. Formalise the goal
Write `docs/research/Rxx_<topic>_goal.md` (`<topic>` = snake_case, 2-5 words) by copying the structure of an existing goal (e.g. `R11_ships_and_trade_power_goal.md`):
1. Title `# Rxx - <topic sentence>`; the "How to use this file" line (self-contained, give it unchanged to an internet-enabled assistant, save the answer as `Rxx_<topic>_draft.md`).
2. "Project context (same in every task)": copy verbatim from an existing goal; append any newly verified facts from the README integration log that bear on this question.
3. "Rules for your answer": copy verbatim (source + verbatim quote + confidence; `UNKNOWN` instead of guesses; test against the data tables; prefer primary sources; state game version).
4. "Required format of `Rxx_<topic>_draft.md`": copy the template with the new title.
5. "Question": the user's question made precise and exhaustive: named save fields, named defines/constants, what exactly must be computed, and what counts as an answer. Split it into numbered sub-questions.
6. Data tables: build from the repo's real saves/fixtures when the question is about numbers (small, 5-25 rows, chosen to include the hard cases and the edge cases). Never invent rows. State how each table was produced (script path or query).
Show the goal to the user (summary + path) and get a go-ahead before spending research effort. Add the topic to the README status table (status `goal`).

## 3. Draft
- `agent` mode: spawn a research subagent (general-purpose; it needs WebSearch/WebFetch) with the full text of the goal file as its prompt plus: "write your answer in the required format; use only sources you actually opened; quote verbatim; write UNKNOWN rather than guessing; return the complete markdown". Save the returned text as `Rxx_<topic>_draft.md`, applying only the formatting repairs listed in the README (no wording or number changes).
- `manual` mode: tell the user which file to give to the assistant and the exact filename to save the reply under, then stop. Resume when the file exists.
Update the README status to `draft`.

## 4. Review (every draft and every response)
Review as a skeptical reviewer. Record findings as you go.
1. Format: all required sections present; each claim has source, verbatim quote, confidence.
2. Sources: open at least the key URLs with WebFetch and check the quote exists; a quote copied from our own goal, with no URL/file:line, or not found at its URL is a defect.
3. Data: recompute every validation row with real arithmetic; validation rows must come from the goal's tables; no circular validation (a definition re-derived by itself); every failure listed.
4. Contradictions with: the goal's verified facts, the goal's data tables, the README integration log (integrated and verified rules are ground truth), and other drafts/finals (grep the research folder for the same field names). Data beats claims.
5. Coverage: each numbered sub-question answered, or `UNKNOWN` with what would settle it.
6. Precision: invented defines/constants/formulas presented as confirmed.
Where cheap, check claims yourself against repo data (fixtures, `backend/app/trade`) rather than trusting the draft.

Decide:
- **No open defects** -> step 6.
- **Defects remain** -> step 5.
- **Not answerable by research** (needs an in-game experiment or data we do not have) -> do not loop again on it; record it as `UNKNOWN` with the experiment that would settle it (feed it into the R14 intervention-pair design).

## 5. Request / response round `i`
- Write `Rxx_<topic>_request_<i>.md` in the format of `R10_embargo_privateers_transfers_misc_request_1.md`: files to read (by path), the rules repeated, a short summary of what was wrong, numbered points `Q1..` each stating what is wrong or missing, the evidence from the files, and the form of answer wanted. Only real gaps, no padding; frame uncertain game facts as things to verify, never as assertions.
- `agent` mode: send it to the research agent (SendMessage to keep its context if it is still alive, otherwise a fresh agent given the goal, draft, prior requests/responses and the new request). Save the reply as `Rxx_<topic>_response_<i>.md` (formatting repairs only). `manual` mode: hand over the file names and wait.
- Review the response (step 4), against the numbered points. Repeat.
- **Stop rules:** at most 4 rounds per topic; also stop when a round resolves nothing new (same point still unanswered or still contradicted). Then finalise with the remainder marked `UNKNOWN`, and tell the user what is left and why.
- Keep the README status column current (`request_<i> open`, `response_<i> received`).

## 6. Final
Write `Rxx_<topic>_final.md`: the goal's sections 1-6 (Answer with exact formula/pseudo-code, Variables JSON, Claims, Validation, Unknowns, Sources) merged from the draft and all responses, keeping only what survived review, plus:
- `## 7. Provenance` table: each claim/variable -> source file and point number (`response_2.md Q3`, `draft.md`).
- `## 8. Rejected claims`: claim, where it came from, the data or source that contradicts it.
Every number in the final must be traceable to a quote or to a data row. Update the README status to `final` (ready to integrate). Do not change `calc.py`, the spec, or tests as part of the loop; integration is a separate step, and only then is an entry added to the README integration log.

## Guardrails
- Never fabricate a source, quote, define, file line or data row, in requests as well as in finals.
- Never edit a saved draft/response except formatting repairs; never delete or renumber files.
- Do not pass the user's approval of one step to the next; the goal needs the user's go-ahead (step 2), later rounds may run on their own within the stop rules.
- Report to the user after each round in 3-5 lines: what was found, what was requested, what is open.
