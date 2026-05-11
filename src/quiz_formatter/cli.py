from __future__ import annotations

import argparse
from pathlib import Path

from .extractor import extract_pdf_text
from .history import load_history, save_history
from .models import QuizResult
from .parser import parse_questions
from .quiz import (
    build_explanation,
    build_quiz,
    filter_questions_by_ranges,
    parse_answer,
    render_question,
    score_results,
)
from .web import serve_web_app


def main() -> int:
    args = _build_parser().parse_args()

    if args.show_history:
        _print_history(args.history_path)
        return 0

    try:
        pdf_path = _resolve_pdf_path(args.pdf)
    except FileNotFoundError as error:
        print(error)
        return 1

    raw_text = extract_pdf_text(pdf_path)
    questions = parse_questions(raw_text)

    if not questions:
        print(f"Не удалось распознать вопросы теста из файла {pdf_path.name}.")
        return 1

    try:
        active_questions = filter_questions_by_ranges(questions, args.ranges)
    except ValueError as error:
        print(error)
        return 1

    if args.ranges and not active_questions:
        print("По указанным диапазонам не найдено ни одного вопроса.")
        return 1

    if args.parse_only:
        print(f"Из файла {pdf_path.name} распознано вопросов: {len(active_questions)}.")
        preview_count = min(args.preview, len(active_questions))
        for question in active_questions[:preview_count]:
            print()
            print(f"{question.number}. {question.prompt}")
            for index, option in enumerate(question.options):
                marker = "*" if index == question.correct_index else "-"
                label = chr(65 + index)
                print(f"  {marker} {label}. {option}")
        return 0

    if args.web:
        return serve_web_app(
            questions=questions,
            pdf_path=pdf_path,
            host=args.host,
            port=args.port,
            history_path=args.history_path,
            default_count=args.count,
            default_ranges=args.ranges,
            default_reveal_answers=args.show_correct_from_start,
            default_shuffle_answers=args.shuffle_answers,
        )

    try:
        quiz_questions = build_quiz(
            active_questions,
            args.count,
            seed=args.seed,
            shuffle_answers=args.shuffle_answers,
        )
    except ValueError as error:
        print(error)
        return 1

    if args.show_correct_from_start:
        print("Режим изучения: правильные ответы показаны сразу.")
        for index, question in enumerate(quiz_questions, start=1):
            print()
            print(render_question(question, index, len(quiz_questions), reveal_correct=True))
        return 0

    results: list[QuizResult] = []

    for index, question in enumerate(quiz_questions, start=1):
        print()
        print(render_question(question, index, len(quiz_questions)))
        selected_index = _prompt_for_answer(question)
        results.append(QuizResult(question=question, selected_index=selected_index))

    correct, total = score_results(results)
    percentage = (correct / total) * 100 if total else 0

    print()
    print(f"Результат: {correct}/{total} ({percentage:.1f}%)")

    wrong_results = [result for result in results if not result.is_correct]
    if wrong_results and _prompt_yes_no("Показать объяснения для неправильных ответов? [y/N]: "):
        print()
        for result in wrong_results:
            print(f"Вопрос {result.question.number}: {result.question.prompt}")
            print(build_explanation(result))
            print()

    save_history(
        results=results,
        pdf_name=pdf_path.name,
        count=args.count,
        seed=args.seed,
        shuffle_answers=args.shuffle_answers,
        mode="cli",
        history_path=args.history_path,
        range_spec=args.ranges,
        reveal_answers=False,
    )

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Распознаёт вопросы с вариантами ответов из PDF и запускает случайную викторину."
    )
    parser.add_argument("pdf", nargs="?", help="Путь к PDF-файлу. По умолчанию берётся первый PDF в папке.")
    parser.add_argument("--count", type=int, default=10, help="Сколько случайных вопросов задать.")
    parser.add_argument("--seed", type=int, default=None, help="Начальное значение для повторяемой выборки вопросов.")
    parser.add_argument(
        "--ranges",
        default="",
        help="Диапазоны номеров вопросов, например 1-50; 120-160; 200.",
    )
    parser.add_argument(
        "--show-correct-from-start",
        action="store_true",
        help="Режим изучения: сразу показывать правильные ответы без тестирования.",
    )
    parser.add_argument(
        "--no-shuffle-answers",
        action="store_false",
        dest="shuffle_answers",
        help="Оставить варианты ответов в исходном порядке из PDF.",
    )
    parser.add_argument("--parse-only", action="store_true", help="Только распознать PDF и показать предпросмотр.")
    parser.add_argument("--preview", type=int, default=3, help="Сколько распознанных вопросов показать в предпросмотре.")
    parser.add_argument("--show-history", action="store_true", help="Показать последние попытки и завершить работу.")
    parser.add_argument("--history-path", default=".quiz-cache/history.jsonl", help="Путь к файлу с историей результатов.")
    parser.add_argument("--web", action="store_true", help="Запустить локальный веб-интерфейс вместо терминальной версии.")
    parser.add_argument("--host", default="127.0.0.1", help="Адрес, на котором будет доступен локальный веб-интерфейс.")
    parser.add_argument("--port", type=int, default=8000, help="Порт для локального веб-интерфейса.")
    parser.set_defaults(shuffle_answers=True)
    return parser


def _resolve_pdf_path(pdf_argument: str | None) -> Path:
    if pdf_argument:
        pdf_path = Path(pdf_argument)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF-файл не найден: {pdf_path}")
        return pdf_path

    pdf_files = sorted(Path.cwd().glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError("В текущей папке не найдено PDF-файлов.")

    return pdf_files[0]


def _prompt_for_answer(question) -> int | None:
    option_range = f"A-{chr(64 + len(question.options))}"

    while True:
        answer = input(f"Ваш ответ ({option_range}, или Enter чтобы пропустить): ")
        selected_index = parse_answer(answer, len(question.options))
        if selected_index is not None or not answer.strip():
            return selected_index
        print(f"Введите корректную букву варианта в диапазоне {option_range}.")


def _prompt_yes_no(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def _print_history(history_path: str) -> None:
    entries = load_history(history_path)
    if not entries:
        print("История попыток пока пуста.")
        return

    print("Последние попытки:")
    for entry in entries:
        score = entry["score"]
        range_suffix = f" | диапазоны={entry['range_spec']}" if entry.get("range_spec") else ""
        print(
            f"- {entry['timestamp']} | {_format_mode(entry['mode'])} | {score['correct']}/{score['total']} "
            f"({score['percentage']:.1f}%) | перемешивание={_format_bool(entry['shuffle_answers'])}{range_suffix} | {entry['pdf_name']}"
        )


def _format_mode(mode: str) -> str:
    return {"cli": "терминал", "web": "веб"}.get(mode, mode)


def _format_bool(value: bool) -> str:
    return "да" if value else "нет"
