from __future__ import annotations

import random
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


def render_question(question: PresentedQuestion, index: int, total: int) -> str:
    lines = [f"Вопрос {index}/{total}", question.prompt]

    for option_index, option in enumerate(question.options):
        lines.append(f"  {label_for_option(option_index)}. {option}")

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


def build_explanation(result: QuizResult) -> str:
    question = result.question
    correct_index = question.correct_index
    correct_label = label_for_option(correct_index)
    correct_text = question.options[correct_index]

    if result.selected_index is None:
        chosen_label = "Нет ответа"
        chosen_text = "Вы пропустили этот вопрос."
    else:
        chosen_label = label_for_option(result.selected_index)
        chosen_text = question.options[result.selected_index]

    return (
        f"Ваш ответ: {chosen_label} - {chosen_text}\n"
        f"Правильный ответ: {correct_label} - {correct_text}\n"
        f"Объяснение: в ключе ответов, встроенном в PDF, правильным для этого вопроса отмечен вариант "
        f"{correct_label}, поэтому ваш ответ не совпал с указанным ключом."
    )


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
