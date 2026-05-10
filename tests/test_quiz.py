import pytest

from quiz_formatter.models import Question, QuizResult
from quiz_formatter.quiz import build_explanation, build_quiz, parse_answer, score_results


def _question(number: int) -> Question:
    return Question(
        number=number,
        prompt=f"Question {number}",
        options=["Alpha", "Bravo", "Charlie", "Delta"],
        correct_index=1,
    )


def test_build_quiz_returns_requested_number_without_duplicates():
    questions = [_question(index) for index in range(1, 21)]

    quiz = build_quiz(questions, 10, seed=7)

    assert len(quiz) == 10
    assert len({question.number for question in quiz}) == 10


def test_build_quiz_shuffles_answers_but_preserves_correct_mapping():
    question = Question(
        number=1,
        prompt="Prompt",
        options=["Alpha", "Bravo", "Charlie", "Delta"],
        correct_index=1,
    )

    shuffled = build_quiz([question], 1, seed=2, shuffle_answers=True)[0]

    assert shuffled.options != question.options
    assert shuffled.options[shuffled.correct_index] == "Bravo"


def test_build_quiz_rejects_request_larger_than_bank():
    with pytest.raises(ValueError):
        build_quiz([_question(1)], 2)


def test_parse_answer_accepts_case_insensitive_labels_and_skips_empty():
    assert parse_answer("b", 4) == 1
    assert parse_answer("", 4) is None
    assert parse_answer("z", 4) is None


def test_score_results_and_explanation():
    question = _question(5)
    results = [
        QuizResult(question=question, selected_index=1),
        QuizResult(question=question, selected_index=2),
        QuizResult(question=question, selected_index=None),
    ]

    assert score_results(results) == (1, 3)

    explanation = build_explanation(results[1])
    assert "Ваш ответ: C - Charlie" in explanation
    assert "Правильный ответ: B - Bravo" in explanation
