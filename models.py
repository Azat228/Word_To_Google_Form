from dataclasses import dataclass
from typing import List


@dataclass
class Question:
    text: str
    options: List[str]
    correct_answer: str | None = None


@dataclass
class ParsedTest:
    title: str
    questions: List[Question]