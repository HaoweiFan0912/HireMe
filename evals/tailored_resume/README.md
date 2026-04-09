# Tailored Resume Eval Set

- `profile_maya_chen_v0.json`: frozen candidate profile for the first prompt-tuning round.
- `cases_v0.json`: 10 job-description cases split into `close_fit`, `adjacent_fit`, and `stretch_fit`.

This dataset is intended for comparing:

1. `general resume`
2. `v0 baseline tailored resume` (single-shot prompt)
3. `current tailored resume` (multi-step analysis/alignment/draft/safety pipeline)

Run the eval script from the repo root:

```bash
python3 scripts/evaluate_tailored_resume.py
```

Optional flags:

```bash
python3 scripts/evaluate_tailored_resume.py --skip-judge
python3 scripts/evaluate_tailored_resume.py --case-id close_fit_machine_learning_intern
python3 scripts/evaluate_tailored_resume.py --output runtime/evals/tailored_resume_eval.json
```
