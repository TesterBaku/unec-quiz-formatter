from __future__ import annotations

import random
import re
from string import ascii_uppercase

from .models import PresentedQuestion, Question, QuizResult


def build_quiz(
    questions: list[Question],
    count: int,
    seed: int | None = None,
    shuffle_answers: bool = True,
) -> list[PresentedQuestion]:
    if count <= 0:
        raise ValueError("Количество вопросов в викторине должно быть положительным.")

    if len(questions) < count:
        raise ValueError(
            f"Запрошено {count} вопросов, но удалось распознать только {len(questions)}."
        )

    generator = random.Random(seed)
    selected_questions = generator.sample(questions, count)
    return [_present_question(question, generator, shuffle_answers) for question in selected_questions]


def render_question(
    question: PresentedQuestion,
    index: int,
    total: int,
    reveal_correct: bool = False,
) -> str:
    lines = [f"Вопрос {index}/{total}", question.prompt]

    for option_index, option in enumerate(question.options):
        lines.append(f"  {label_for_option(option_index)}. {option}")

    if reveal_correct:
        lines.append(f"Правильный ответ: {build_correct_answer_text(question)}")

    return "\n".join(lines)


def label_for_option(index: int) -> str:
    return ascii_uppercase[index]


def parse_answer(answer: str, option_count: int) -> int | None:
    answer = answer.strip().upper()
    if not answer:
        return None

    if len(answer) != 1 or answer not in ascii_uppercase[:option_count]:
        return None

    return ascii_uppercase.index(answer)


def score_results(results: list[QuizResult]) -> tuple[int, int]:
    correct = sum(1 for result in results if result.is_correct)
    total = len(results)
    return correct, total


def build_correct_answer_text(question: PresentedQuestion) -> str:
    return f"{label_for_option(question.correct_index)} - {question.options[question.correct_index]}"


def build_explanation(result: QuizResult) -> str:
    question = result.question
    correct_answer = build_correct_answer_text(question)

    if result.selected_index is None:
        chosen_label = "Нет ответа"
        chosen_text = "Вы пропустили этот вопрос."
    else:
        chosen_label = label_for_option(result.selected_index)
        chosen_text = question.options[result.selected_index]

    return (
        f"Ваш ответ: {chosen_label} - {chosen_text}\n"
        f"Правильный ответ: {correct_answer}\n"
        f"Объяснение: в ключе ответов, встроенном в PDF, правильным для этого вопроса отмечен вариант "
        f"{label_for_option(question.correct_index)}, поэтому ваш ответ не совпал с указанным ключом."
    )


def parse_question_ranges(range_spec: str | None) -> list[tuple[int, int]]:
    if range_spec is None or not range_spec.strip():
        return []

    segments = [segment.strip() for segment in re.split(r"[;,]", range_spec) if segment.strip()]
    if not segments:
        return []

    ranges: list[tuple[int, int]] = []

    for segment in segments:
        if re.fullmatch(r"\d+", segment):
            value = int(segment)
            if value <= 0:
                raise ValueError("Номера вопросов должны быть больше нуля.")
            ranges.append((value, value))
            continue

        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", segment)
        if not match:
            raise ValueError(
                "Неверный формат диапазона. Используйте вид 1-50; 120-160; 200."
            )

        start = int(match.group(1))
        end = int(match.group(2))
        if start <= 0 or end <= 0:
            raise ValueError("Номера вопросов должны быть больше нуля.")
        if end < start:
            raise ValueError("В диапазоне начало должно быть меньше или равно концу.")

        ranges.append((start, end))

    return ranges


def filter_questions_by_ranges(questions: list[Question], range_spec: str | None) -> list[Question]:
    ranges = parse_question_ranges(range_spec)
    if not ranges:
        return questions

    return [
        question
        for question in questions
        if any(start <= question.number <= end for start, end in ranges)
    ]


def _present_question(
    question: Question,
    generator: random.Random,
    shuffle_answers: bool,
) -> PresentedQuestion:
    decorated_options = [
        (option, index == question.correct_index)
        for index, option in enumerate(question.options)
    ]

    if shuffle_answers:
        generator.shuffle(decorated_options)

    options = [option for option, _ in decorated_options]
    correct_index = next(index for index, (_, is_correct) in enumerate(decorated_options) if is_correct)
    return PresentedQuestion(source=question, options=options, correct_index=correct_index)
