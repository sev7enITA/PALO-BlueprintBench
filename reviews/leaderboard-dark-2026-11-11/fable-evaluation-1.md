# Evaluation — Attempt 1

**Basis:** I reviewed the five supplied screenshots and your listed test results; I did not open the page myself, and no report file was written, so the report is returned here. The 768px view, the internal-tab filters, the compare dialog, hover/focus states and the mobile table were not in the screenshots, so they are taken from your test list, not confirmed by me. This is an advisory AI design review.

## Overall Verdict: PASS (conditional on fixes 1 and 2 before the page is shown externally)

## Overall Assessment
The page aims to be a sober, dark research workspace that exposes every tested configuration without implying a ranking, and it largely succeeds. The palette matches the overview, the zero-qualified hero card is gone, the limitations section sits lower with the requested title, and the catalogue is the default tab with cohort and assay labels. It is held back by too much stacked chrome above the first model row, micro-type that is too small, and a few data labels that blur "not yet run" with "failed".

## Scores
| Criterion | Score | Status | Weight | Notes |
|-----------|-------|--------|--------|-------|
| Design Quality | 2/3 | PASS | HIGH | Coherent navy/cyan/amber/coral system with hairline rules, mono eyebrows and visible denominators. Loosened by a stray serif heading and vertical bloat. |
| Originality | 2/3 | PASS | HIGH | A low 2. The custom decisions are honesty-driven: no rank column, cohort bands, "72 / 324" fractions, "exploratory sort" band. The shell itself is a familiar dark dashboard. |
| Craft | 1/3 | PASS | MEDIUM | Noticeable issues: roughly 8px mono text, near-touching h1 tracking, 85–105px rows, misaligned limits intro, orphaned "Reset filters". |
| Functionality | 2/3 | PASS | MEDIUM | Sort affordances, active tab and buttons read clearly, and your listed tests pass. Kept from 3 by the fold problem and ambiguous status labels. |

## What's Working Well
- **Palette:** the leaderboard and overview screenshots are visually indistinguishable in background, panel, cyan, amber and coral usage.
- **Limitations section:** it carries the exact requested title, keeps all the accurate statements (internal tests, 0 qualified, one synthetic family, no PBI) and is no longer a warning hero.
- **Sort disclaimer:** the table band "Internal tests · Frozen draft labels · Exploratory sort" is concise and sits where the sorting happens.
- **Sort affordance:** the active column is tinted with a single arrow and inactive columns show ↕, which is legible at a glance.
- **Catalogue honesty:** it shows a cohort badge and task/coverage per row and no pooled score; the historical row previewed at the fold shows a task label ("Adapter contract checks"), not a score.
- **Metric colour:** coral for non-zero disagreements and amber for missing use the palette semantically.

## Issues Found
### Issue 1: Models still start too low
- **What**: At 1440×1000 the first model row begins around y≈855, so only one row is visible. At 375 the first 1000px contain no rows at all.
- **Where**: Hero, stats strip, "Explore the record" header, tabs, notice line, filters, status line and table band, all stacked above the table.
- **Why it matters**: "Models visible sooner" was an explicit goal. On a 900px laptop the first row is barely visible.
- **Suggested fix**: Shrink the h1 to about 44px and move the four stats into a hero right column. Drop the "Evidence workspace / Explore the record." heading and put Share/Export on the tab row. Merge the notice line into the table band. Target the first row at 600px or higher on desktop.

### Issue 2: "Missing" conflates not-yet-run with failed
- **What**: The hero says 324 assigned, 90 complete, 2 incomplete, which leaves 232 calls unexplained. In the table those calls appear as amber "Missing — Unclassified / absent" (e.g. 288 for a 3/18 model). Fugu Max shows 0/18 calls but "Known USD 0.000000".
- **Where**: Hero stats strip; Missing and Known USD columns of the internal table.
- **Why it matters**: A pending model looks like a failing one. A model with no completed calls would likely sort as cheapest, and a "failures/missing only" filter would match almost everything.
- **Suggested fix**: Split the status into pending and failed/absent, and add a "232 not yet run" stat or relabel the existing one. Render cost as "—"/Unknown when no calls are complete, so it sorts last.

### Issue 3: Micro-type is too small
- **What**: Mono sublines, "Unclassified / absent", band labels, "01 / Measurement" and the revision stamp render at roughly 8px.
- **Where**: Tables, limits section, header edition stamp.
- **Why it matters**: The provider and reasoning sublines carry real information but are hard to read, and amber at that size is weak.
- **Suggested fix**: Set an 11px floor for mono labels, 12px for data sublines.

### Issue 4: Rows are too tall and repeat information
- **What**: Catalogue rows are about 105px and internal rows about 85px. The provider appears both in the model subline and in its own column.
- **Where**: Both tables.
- **Why it matters**: 28 rows come to roughly 2,900px, which makes scanning and comparing harder as the data grows.
- **Suggested fix**: Aim for 56–64px rows. Drop the provider from the catalogue subline and put the API identifier on one line.

### Issue 5: Typography is not yet coherent
- **What**: "An open chain of evidence." is serif, directly below sans headings. The h1 tracking is tight enough that glyphs nearly touch. The limits intro paragraph sits at about x=755 while