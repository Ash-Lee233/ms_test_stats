# Test Case Quality Scoring System (A/B/C)

## Overview

This project introduces a lightweight static test quality scoring model to evaluate
pytest-based test cases and classify them into three grades:

- A – High quality
- B – Medium quality
- C – Low quality / improvement needed

The scoring is designed to be:

- Static – based only on source code analysis (AST parsing)
- Fast – suitable for large repositories
- Explainable – every grade is derived from explicit rules
- Configurable – rules can be tuned in code

It is not a replacement for execution-based metrics (such as flakiness or failure
detection rate), but a first-level structural quality indicator.

---

## Goals

The scoring system aims to:

- Identify weak or superficial test cases
- Highlight high-value, well-structured tests
- Provide quantitative insights for test quality dashboards
- Support quality gating in CI
- Track quality evolution over time

---

## What Is Analyzed

Each pytest test function (test_*) is inspected using Python AST and the following
features are extracted:

| Feature | Description |
|--------|-----------|
| assert_count | Number of assertion statements or assertion-like calls |
| has_docstring | Whether the test has a docstring |
| has_parametrize | Whether pytest.mark.parametrize is used |
| markers | All pytest markers on the test |

---

## Scoring Rules

The default scoring logic is implemented in:

ms_test_stats/quality.py

### Positive Signals

| Rule | Score |
|-----|------|
| At least 1 assertion | +2 |
| 3 or more assertions | +1 |
| Uses @pytest.mark.parametrize | +1 |
| Has a docstring | +1 |

### Negative Signals

| Rule | Score |
|-----|------|
| Marked with skip, skipif, or xfail | -1 |

---

## Grade Mapping

Final numeric scores are mapped into letter grades:

| Score | Grade |
|------|------|
| >= 4 | A |
| 2–3 | B |
| <= 1 | C |

---

## Output Fields

The following columns are added to the cases sheet in Excel:

| Column | Description |
|-------|-----------|
| assert_count | Total number of assertions |
| has_docstring | Boolean |
| has_parametrize | Boolean |
| quality_score | Final numeric score |
| quality_grade | A / B / C |

---

## Aggregated Reports

Additional Excel summary sheets are generated:

- summary_quality – overall A/B/C distribution
- summary_quality_level – quality grade per level
- summary_quality_dir – quality grade per directory group

---

## Web Dashboard Visualizations

Two new charts appear in the web UI:

1. Quality Grade Distribution
   - Bar chart showing total number of A/B/C tests

2. Level × Quality Grade
   - Stacked bar chart
   - Shows quality breakdown per test level
   - unmarked is excluded from charts but kept in Excel

All bars display numeric value labels.

---

## Interpretation Guidelines

### Grade A – High Quality

Typical characteristics:

- Multiple meaningful assertions
- Uses parametrization
- Has descriptive docstring
- Not skipped
- Tests observable behavior, not implementation details

Recommended action: keep as benchmark examples.

---

### Grade B – Medium Quality

Typical characteristics:

- At least one assertion
- Limited coverage
- Missing parametrization or docstring

Recommended action: improve gradually.

---

### Grade C – Low Quality

Typical characteristics:

- No or very few assertions
- No docstring
- Often skipped or xfailed
- Possibly smoke tests only

Recommended action:

- Add stronger assertions
- Clarify intent with docstring
- Convert to parametrized tests
- Remove obsolete skips
- Split into focused cases

---

## Limitations

This scoring system:

- Does not measure runtime behavior
- Does not detect flaky tests
- Does not assess functional correctness
- Does not use coverage metrics
- May misclassify complex helper-based tests
- Counts static asserts only

It should be treated as a heuristic, not an absolute truth.

---

## Customization

To tune the model, modify:

ms_test_stats/quality.py

You can adjust:

- Score weights
- Thresholds
- Add new signals (e.g., fixture usage, timeout markers, randomness detection)
- Penalize very long tests
- Reward regression-linked tests

---

## Suggested Future Enhancements

- Incorporate CI history (flake rate, failure rate)
- Track execution time
- Link tests to bug IDs / PRs
- Code coverage attribution
- Historical trend analysis
- Per-team quality scores
- Quality gates in CI pipelines
