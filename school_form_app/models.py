from dataclasses import dataclass, field
from typing import List


@dataclass
class AnswerOption:
    text: str
    score: int = 0


@dataclass
class Question:
    number: int
    title: str
    options: List[AnswerOption]


@dataclass
class GradeThreshold:
    min_score: int
    max_score: int
    label: str


@dataclass
class ParsedTest:
    title: str
    instructions: str | None
    questions: List[Question]
    thresholds: List[GradeThreshold] = field(default_factory=list)