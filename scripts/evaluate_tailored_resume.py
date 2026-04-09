import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.extraction.common import normalize_text
from app.generation.models import GeneratedResumeDocument, TailoredResumeGeneration
from app.generation.service import (
    generate_general_resume_from_record,
    judge_generated_resume,
    render_resume_document,
    review_tailored_resume_output,
    run_tailored_resume_pipeline,
    tailor_resume_to_job_description_baseline,
)


DEFAULT_PROFILE_PATH = REPO_ROOT / "evals" / "tailored_resume" / "profile_maya_chen_v0.json"
DEFAULT_CASES_PATH = REPO_ROOT / "evals" / "tailored_resume" / "cases_v0.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "runtime" / "evals"

FIT_THRESHOLDS = {
    "close_fit": {"total_score": 85, "keyword_coverage": 0.70},
    "adjacent_fit": {"total_score": 80, "keyword_coverage": 0.55},
    "stretch_fit": {"total_score": 75, "keyword_coverage": None, "gap_handling": 4.0},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def normalize_phrase(value: str) -> str:
    return normalize_text(value or "")


def text_contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_phrase(text)
    normalized_phrase = normalize_phrase(phrase)
    return bool(normalized_phrase) and normalized_phrase in normalized_text


def flatten_resume_text(document: GeneratedResumeDocument) -> str:
    return render_resume_document(document)


def collect_bullets(document: GeneratedResumeDocument) -> list[str]:
    bullets: list[str] = []
    for entry in document.education + document.professional_experience + document.activities:
        bullets.extend(entry.bullets)
    bullets.extend(document.summary)
    return [bullet.strip() for bullet in bullets]


def count_duplicate_bullets(bullets: list[str]) -> int:
    seen: set[str] = set()
    duplicates = 0
    for bullet in bullets:
        normalized = normalize_phrase(bullet)
        if not normalized:
            continue
        if normalized in seen:
            duplicates += 1
            continue
        seen.add(normalized)
    return duplicates


def count_empty_bullets(bullets: list[str]) -> int:
    return sum(1 for bullet in bullets if not bullet.strip())


def compute_keyword_coverage(rendered_text: str, keywords: list[str]) -> tuple[float, list[str]]:
    if not keywords:
        return 1.0, []
    hits = [keyword for keyword in keywords if text_contains_phrase(rendered_text, keyword)]
    return len(hits) / len(keywords), hits


def _match_expected_item(actual_values: list[str], expected_value: str) -> int | None:
    normalized_expected = normalize_phrase(expected_value)
    for index, value in enumerate(actual_values):
        if normalized_expected and normalized_expected in normalize_phrase(value):
            return index
    return None


def compute_section_priority_accuracy(document: GeneratedResumeDocument, expected: dict[str, list[str]]) -> float:
    checks: list[float] = []

    section_entries = {
        "professional_experience": [f"{entry.title} | {entry.subtitle or ''}" for entry in document.professional_experience],
        "education": [
            " | ".join(
                part for part in [entry.title, entry.subtitle or "", " ".join(entry.bullets)] if part.strip()
            )
            for entry in document.education
        ],
        "activities": [f"{entry.title} | {entry.subtitle or ''}" for entry in document.activities],
        "skills": [item for group in document.skills for item in group.items],
    }

    for section_name, expected_items in expected.items():
        actual_values = section_entries.get(section_name, [])
        if not expected_items:
            continue

        section_limit = max(1, len(actual_values) // 2) if section_name != "skills" else min(12, max(1, len(actual_values)))
        positions = [_match_expected_item(actual_values, item) for item in expected_items]
        for position in positions:
            checks.append(1.0 if position is not None and position < section_limit else 0.0)

        valid_positions = [position for position in positions if position is not None]
        if len(valid_positions) > 1:
            checks.append(1.0 if valid_positions == sorted(valid_positions) else 0.0)

    if not checks:
        return 1.0
    return sum(checks) / len(checks)


def compute_gap_metrics(generated_missing: list[str], expected_missing: list[str]) -> dict[str, float]:
    normalized_generated = [normalize_phrase(item) for item in generated_missing if normalize_phrase(item)]
    normalized_expected = [normalize_phrase(item) for item in expected_missing if normalize_phrase(item)]

    matched_generated: set[int] = set()
    matched_expected: set[int] = set()
    for expected_index, expected_item in enumerate(normalized_expected):
        for generated_index, generated_item in enumerate(normalized_generated):
            if generated_index in matched_generated:
                continue
            if expected_item in generated_item or generated_item in expected_item:
                matched_generated.add(generated_index)
                matched_expected.add(expected_index)
                break

    precision = len(matched_generated) / len(normalized_generated) if normalized_generated else (1.0 if not normalized_expected else 0.0)
    coverage = len(matched_expected) / len(normalized_expected) if normalized_expected else 1.0
    return {
        "precision": precision,
        "coverage": coverage,
    }


def compute_must_not_claim_hits(rendered_text: str, must_not_claim: list[str]) -> list[str]:
    return [item for item in must_not_claim if text_contains_phrase(rendered_text, item)]


def weighted_total(judge_scores: dict[str, int]) -> float:
    return round(
        (
            judge_scores["groundedness"] * 35
            + judge_scores["jd_alignment"] * 25
            + judge_scores["prioritization"] * 15
            + judge_scores["resume_quality"] * 15
            + judge_scores["gap_handling"] * 10
        )
        / 5,
        2,
    )


def evaluate_current_variant(
    profile: dict[str, Any],
    case: dict[str, Any],
    *,
    api_key_override: str | None,
    skip_judge: bool,
) -> dict[str, Any]:
    general_resume = generate_general_resume_from_record(
        profile,
        target_role=case["target_role"],
        api_key_override=api_key_override,
    )
    pipeline = run_tailored_resume_pipeline(
        profile,
        case["job_description"],
        target_role=case["target_role"],
        api_key_override=api_key_override,
        base_resume=general_resume,
    )
    baseline_tailored = tailor_resume_to_job_description_baseline(
        profile,
        case["job_description"],
        target_role=case["target_role"],
        api_key_override=api_key_override,
        base_resume=general_resume,
    )
    baseline_safety = review_tailored_resume_output(
        profile,
        case["job_description"],
        api_key_override=api_key_override,
        jd_analysis=pipeline.jd_analysis,
        evidence_alignment=pipeline.evidence_alignment,
        tailored_resume=baseline_tailored,
    )

    variants = {
        "general": {
            "generation": general_resume.model_dump(mode="json"),
            "rendered_text": flatten_resume_text(general_resume.resume),
        },
        "baseline_tailored": {
            "generation": baseline_tailored.model_dump(mode="json"),
            "rendered_text": flatten_resume_text(baseline_tailored.resume),
            "safety_review": baseline_safety.model_dump(mode="json"),
        },
        "current_tailored": {
            "generation": pipeline.final_resume.model_dump(mode="json"),
            "rendered_text": flatten_resume_text(pipeline.final_resume.resume),
            "safety_review": pipeline.final_safety_review.model_dump(mode="json"),
            "jd_analysis": pipeline.jd_analysis.model_dump(mode="json"),
            "evidence_alignment": pipeline.evidence_alignment.model_dump(mode="json"),
        },
    }

    for variant_name, variant in variants.items():
        document = variant["generation"]["resume"]
        bullets = collect_bullets(GeneratedResumeDocument.model_validate(document))
        keyword_coverage, keyword_hits = compute_keyword_coverage(variant["rendered_text"], case["must_hit_keywords"])
        must_not_claim_hits = compute_must_not_claim_hits(variant["rendered_text"], case["must_not_claim"])
        section_priority_accuracy = compute_section_priority_accuracy(
            GeneratedResumeDocument.model_validate(document),
            case.get("expected_section_priority", {}),
        )
        gap_metrics = compute_gap_metrics(
            variant["generation"].get("missing_requirements", []),
            case.get("expected_missing_requirements", []),
        )

        safety_review = variant.get("safety_review", {})
        unsupported_claim_count = len(safety_review.get("unsupported_claims", [])) + len(must_not_claim_hits)
        duplicate_bullet_count = count_duplicate_bullets(bullets)
        empty_bullet_count = count_empty_bullets(bullets)

        variant["metrics"] = {
            "schema_validity": True,
            "unsupported_claim_count": unsupported_claim_count,
            "duplicate_bullet_count": duplicate_bullet_count,
            "empty_bullet_count": empty_bullet_count,
            "keyword_coverage_ratio": round(keyword_coverage, 3),
            "keyword_hits": keyword_hits,
            "section_promotion_accuracy": round(section_priority_accuracy, 3),
            "gap_precision": round(gap_metrics["precision"], 3),
            "gap_coverage": round(gap_metrics["coverage"], 3),
            "must_not_claim_hits": must_not_claim_hits,
            "hard_gate_pass": (
                unsupported_claim_count == 0
                and empty_bullet_count == 0
                and duplicate_bullet_count <= 1
            ),
        }

        if skip_judge:
            continue

        judge = judge_generated_resume(
            profile,
            case["job_description"],
            variant["generation"],
            expected_missing_requirements=case.get("expected_missing_requirements", []),
            api_key_override=api_key_override,
        )
        judge_payload = judge.model_dump(mode="json")
        variant["judge"] = {
            **judge_payload,
            "total_score": weighted_total(judge_payload),
        }

    if not skip_judge:
        general_alignment = variants["general"]["judge"]["jd_alignment"]
        baseline_alignment = variants["baseline_tailored"]["judge"]["jd_alignment"]
        current_alignment = variants["current_tailored"]["judge"]["jd_alignment"]
        variants["baseline_tailored"]["metrics"]["tailored_vs_general_lift"] = baseline_alignment - general_alignment
        variants["current_tailored"]["metrics"]["tailored_vs_general_lift"] = current_alignment - general_alignment
    else:
        general_ratio = variants["general"]["metrics"]["keyword_coverage_ratio"]
        baseline_ratio = variants["baseline_tailored"]["metrics"]["keyword_coverage_ratio"]
        current_ratio = variants["current_tailored"]["metrics"]["keyword_coverage_ratio"]
        variants["baseline_tailored"]["metrics"]["tailored_vs_general_lift"] = round(baseline_ratio - general_ratio, 3)
        variants["current_tailored"]["metrics"]["tailored_vs_general_lift"] = round(current_ratio - general_ratio, 3)

    return variants


def compute_case_pass(case: dict[str, Any], current_variant: dict[str, Any], skip_judge: bool) -> dict[str, Any]:
    threshold = FIT_THRESHOLDS[case["fit_tier"]]
    metrics = current_variant["metrics"]
    hard_gate_pass = metrics["hard_gate_pass"] and metrics["schema_validity"]
    pass_reasons = []

    if not hard_gate_pass:
        pass_reasons.append("hard_gate_failed")

    if metrics["keyword_coverage_ratio"] < threshold["keyword_coverage"] if threshold["keyword_coverage"] is not None else False:
        pass_reasons.append("keyword_coverage_below_threshold")

    if case["fit_tier"] == "stretch_fit" and not skip_judge:
        if current_variant["judge"]["gap_handling"] < threshold["gap_handling"]:
            pass_reasons.append("gap_handling_below_threshold")

    if not skip_judge:
        if current_variant["judge"]["total_score"] < threshold["total_score"]:
            pass_reasons.append("total_score_below_threshold")

    return {
        "pass": len(pass_reasons) == 0,
        "threshold": threshold,
        "reasons": pass_reasons,
    }


def build_summary(results: list[dict[str, Any]], skip_judge: bool) -> dict[str, Any]:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result["current_tailored_gate"]["pass"])
    current_variants = [result["variants"]["current_tailored"] for result in results]

    summary: dict[str, Any] = {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "hard_gate_pass_rate": round(
            sum(1 for variant in current_variants if variant["metrics"]["hard_gate_pass"]) / total_cases,
            3,
        ) if total_cases else 0.0,
        "avg_keyword_coverage": round(
            sum(variant["metrics"]["keyword_coverage_ratio"] for variant in current_variants) / total_cases,
            3,
        ) if total_cases else 0.0,
        "lift_over_general_rate": round(
            sum(1 for variant in current_variants if variant["metrics"]["tailored_vs_general_lift"] > 0) / total_cases,
            3,
        ) if total_cases else 0.0,
    }

    if not skip_judge and total_cases:
        summary["avg_total_score"] = round(
            sum(variant["judge"]["total_score"] for variant in current_variants) / total_cases,
            2,
        )
        summary["avg_groundedness"] = round(
            sum(variant["judge"]["groundedness"] for variant in current_variants) / total_cases,
            2,
        )
        summary["avg_jd_alignment"] = round(
            sum(variant["judge"]["jd_alignment"] for variant in current_variants) / total_cases,
            2,
        )

    return summary


def print_summary(summary: dict[str, Any], results: list[dict[str, Any]], skip_judge: bool) -> None:
    print("Tailored Resume Eval Summary")
    print(json.dumps(summary, indent=2))
    print()
    print("Lowest-performing current tailored cases:")

    def sort_key(result: dict[str, Any]) -> float:
        if not skip_judge:
            return result["variants"]["current_tailored"]["judge"]["total_score"]
        return result["variants"]["current_tailored"]["metrics"]["keyword_coverage_ratio"]

    for result in sorted(results, key=sort_key)[:3]:
        current_variant = result["variants"]["current_tailored"]
        print(f"- {result['case_id']}: pass={result['current_tailored_gate']['pass']}")
        if not skip_judge:
            print(f"  total_score={current_variant['judge']['total_score']}, jd_alignment={current_variant['judge']['jd_alignment']}")
        print(
            "  "
            f"hard_gate={current_variant['metrics']['hard_gate_pass']}, "
            f"keyword_coverage={current_variant['metrics']['keyword_coverage_ratio']}, "
            f"lift={current_variant['metrics']['tailored_vs_general_lift']}"
        )
        print(f"  reasons={result['current_tailored_gate']['reasons']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate tailored resume prompts against a fixed JD case set.")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE_PATH))
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--case-id")
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--api-key")
    args = parser.parse_args()

    profile = load_json(Path(args.profile))
    cases = load_json(Path(args.cases))
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            raise ValueError(f"No eval case matched --case-id={args.case_id}")

    results = []
    for case in cases:
        print(f"Evaluating {case['id']}...")
        variants = evaluate_current_variant(
            profile,
            case,
            api_key_override=args.api_key,
            skip_judge=args.skip_judge,
        )
        current_tailored_gate = compute_case_pass(case, variants["current_tailored"], args.skip_judge)
        results.append(
            {
                "case_id": case["id"],
                "fit_tier": case["fit_tier"],
                "target_role": case["target_role"],
                "current_tailored_gate": current_tailored_gate,
                "variants": variants,
            }
        )

    summary = build_summary(results, args.skip_judge)
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "baseline_version": "v0_single_shot_tailored_prompt",
        "profile_path": str(Path(args.profile)),
        "cases_path": str(Path(args.cases)),
        "skip_judge": args.skip_judge,
        "summary": summary,
        "results": results,
    }

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"tailored_resume_eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))

    print_summary(summary, results, args.skip_judge)
    print()
    print(f"Wrote eval report to {output_path}")


if __name__ == "__main__":
    main()
