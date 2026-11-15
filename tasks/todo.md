# nepse-expert: task list

Skill source: `nepse-expert/` in this folder. Installed copy: `C:\Users\HP\.claude\skills\nepse-expert\`. Keep the two the same. Workspace: `nepse-expert-workspace/`.

## Done
- [x] Version 0: screenshot parse and confirm, live fetch, price adjustment, tax and costs, portfolio summary, decision log (84 unit tests)
- [x] Cleanup, 10 Nov 2026: source copied into this folder, made-up calibration numbers removed, 10 percent band text fixed, docs corrected
- [x] Graded the 34 saved eval answers, 15 Nov 2026: the skill passes 81 of 90 checks, plain Claude 66 of 90. Results and notes: `nepse-expert-workspace/iteration-1/benchmark.md`, one `grading.json` per run

## Next
- [ ] Test version 0 on a real portfolio screenshot and check the numbers by hand
- [ ] Re-verify `nepse-expert/data/rates.json` (verified 2026-10-24, 30-day limit)
- [ ] Check two possible defects found while grading: SHL fails validation (a Rs 10 face value read as bad data?), and the decision-log scrubber removes dates from free text
- [ ] Fix the eval checks that grading showed are wrong (they assume five verdicts, or that the user's premise is true), and save transcripts on the next run
- [ ] Plan a real version 1 from what the two tests show is missing

## Not built (stub files exist, see README)
- [ ] Version 1: sector playbooks with thresholds, `indicators.py` wired into `SKILL.md`, screener on live data, event calendar
- [ ] Version 2: backtest, calibration scoring, floorsheet, primary market
- [ ] Version 3: forecasting and ensemble, only if a baseline is beaten after costs (plan on hold in `tasks/plan.md`)
