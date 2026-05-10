from dataclasses import dataclass


@dataclass(slots=True)
class Question:
    number: int
    prompt: str
    options: list[str]
    correct_index: int


@dataclass(slots=True)
class PresentedQuestion:
    source: Question
    options: list[str]
    correct_index: int

    @property
    def number(self) -> int:
        return self.source.number

    @property
    def prompt(self) -> str:
        return self.source.prompt


@dataclass(slots=True)
class QuizResult:
    question: PresentedQuestion
    selected_index: int | None

    @property
    def is_correct(self) -> bool:
        return self.selected_index == self.question.correct_index
