# Defect Log — Verdeza

Defects are filed as GitHub Issues using the Bug report template. This file is
the milestone-facing summary, regenerated before each submission.

## Life cycle

`New → Triaged → In Progress → Ready for Retest → Closed`
with `Rejected` from Triaged, and `Reopened` from Ready for Retest.

Two rules:

1. **Only the tester closes a defect.** The developer moves it to Ready for
   Retest. 
2. **Every closed defect leaves a regression test behind.** A defect that was
   possible once is possible again.

## Severity is set by the tester; priority is set by the Scrum Master

Keeping them separate stops "how bad is this" and "when do we fix it" being
argued as one question.

| Severity | Definition | Target |
|---|---|---|
| Critical | Data corruption, authorization bypass, wrong credit or CO₂ value | Before the next merge to main |
| High | A core journey cannot be completed, no workaround | Within the sprint |
| Medium | Journey completable, a defined behaviour is wrong | Within the sprint if capacity allows |
| Low | Cosmetic or minor usability | Backlog |

**Override:** any defect touching the credit ledger, authorization scope or a
lifecycle guard is Critical by default and downgraded only with a written
reason. These three fail *silently* and produce wrong data rather than visible
errors — the class of defect that survives to a demonstration.

## Log

| ID | Title | Story/AC | Sev | Pri | Found in | Found by | State | Fixed in PR | Regression test |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

## Metrics reported per milestone

- Defects found, by severity
- Defects found per epic (concentration points to weak design, not weak coders)
- Escape rate: found after merge ÷ total found
- Reopen rate: a high rate means "Ready for Retest" is being used as "I think I fixed it"
- Mean time from New to Closed, by severity
