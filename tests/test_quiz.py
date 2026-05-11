import pytest

from quiz_formatter.models import Question, QuizResult
from quiz_formatter.quiz import (
    build_explanation,
    build_quiz,
    filter_questions_by_ranges,
    parse_answer,
    parse_question_ranges,
    render_question,
    score_results,
)


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
    question = build_quiz([_question(5)], 1, seed=1, shuffle_answers=False)[0]
    results = [
        QuizResult(question=question, selected_index=1),
        QuizResult(question=question, selected_index=2),
        QuizResult(question=question, selected_index=None),
    ]

    assert score_results(results) == (1, 3)

    explanation = build_explanation(results[1])
    assert "Ваш ответ:" in explanation
    assert "Правильный ответ:" in explanation


def test_parse_question_ranges_supports_single_numbers_and_ranges():
    assert parse_question_ranges("1-5; 7; 10-12") == [(1, 5), (7, 7), (10, 12)]


def test_parse_question_ranges_rejects_invalid_syntax():
    with pytest.raises(ValueError):
        parse_question_ranges("5-2")

    with pytest.raises(ValueError):
        parse_question_ranges("abc")


def test_filter_questions_by_ranges_returns_only_matching_questions():
    questions = [_question(index) for index in range(1, 11)]

    filtered = filter_questions_by_ranges(questions, "2-4; 8")

    assert [question.number for question in filtered] == [2, 3, 4, 8]


def test_render_question_can_show_correct_answer_immediately():
    question = build_quiz([_question(9)], 1, seed=1, shuffle_answers=False)[0]

    rendered = render_question(question, 1, 1, reveal_correct=True)

    assert "Правильный ответ: B - Bravo" in rendered
