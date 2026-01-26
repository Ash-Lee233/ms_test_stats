"""
Author: Shawny
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Set

SKIP_MARKS = {"skip", "skipif", "xfail"}

@dataclass(frozen=True)
class QualityResult:
    score: int
    grade: str  # A/B/C

def score_test_case(assert_count: int, has_parametrize: bool, has_docstring: bool, markers: Set[str]) -> QualityResult:
    score = 0
    if assert_count >= 1:
        score += 2
    if assert_count >= 3:
        score += 1
    if has_parametrize:
        score += 1
    if has_docstring:
        score += 1

    m_lower = {m.lower() for m in markers}
    if any(m in SKIP_MARKS for m in m_lower):
        score -= 1

    if score >= 4:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"

    return QualityResult(score=score, grade=grade)
