from __future__ import annotations

import html
import secrets
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from .history import load_history, save_history
from .models import PresentedQuestion, Question, QuizResult
from .quiz import (
    build_correct_answer_text,
    build_explanation,
    build_quiz,
    filter_questions_by_ranges,
    label_for_option,
    parse_answer,
    score_results,
)

PAGE_STYLE = """
<style>
  :root {
    --bg: #f4ede1;
    --ink: #1e1a18;
    --panel: rgba(255, 250, 244, 0.92);
    --accent: #b1442b;
    --accent-soft: #f4c8ad;
    --accent-pale: rgba(244, 200, 173, 0.38);
    --edge: #241a15;
    --muted: #6f6057;
    --good: #27593d;
    --good-soft: rgba(39, 89, 61, 0.12);
    --bad: #8b2e1d;
    --shadow: 0 18px 50px rgba(44, 24, 14, 0.14);
    --paper-shadow: inset 0 0 0 1px rgba(36, 26, 21, 0.08);
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    color: var(--ink);
    background:
      radial-gradient(circle at top left, rgba(177, 68, 43, 0.16), transparent 28%),
      radial-gradient(circle at bottom right, rgba(96, 128, 96, 0.18), transparent 24%),
      linear-gradient(135deg, #e9ddcb, #f8f1e7 48%, #eadfcf);
    font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  }

  .shell {
    max-width: 1120px;
    margin: 0 auto;
    padding: 32px 20px 64px;
  }

  .masthead {
    position: relative;
    overflow: hidden;
    border: 2px solid var(--edge);
    border-radius: 28px;
    padding: 32px;
    background:
      linear-gradient(120deg, rgba(255, 247, 236, 0.96), rgba(246, 234, 221, 0.88)),
      repeating-linear-gradient(
        45deg,
        rgba(177, 68, 43, 0.05),
        rgba(177, 68, 43, 0.05) 10px,
        transparent 10px,
        transparent 20px
      );
    box-shadow: var(--shadow), var(--paper-shadow);
  }

  .masthead::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -60px;
    top: -70px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(177, 68, 43, 0.35), transparent 68%);
  }

  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.78rem;
    color: var(--accent);
    margin-bottom: 12px;
    font-weight: 700;
  }

  h1, h2, h3 {
    font-family: "Palatino Linotype", "Book Antiqua", serif;
    margin: 0;
    line-height: 1.05;
  }

  h1 {
    font-size: clamp(2.3rem, 5vw, 4.6rem);
    max-width: 11ch;
  }

  .lede {
    max-width: 56ch;
    margin-top: 16px;
    font-size: 1.02rem;
    line-height: 1.7;
    color: var(--muted);
  }

  .grid {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 24px;
    margin-top: 28px;
    align-items: start;
  }

  .panel, .history-card, .question-card {
    background: var(--panel);
    border: 2px solid rgba(36, 26, 21, 0.9);
    border-radius: 24px;
    box-shadow: var(--shadow), var(--paper-shadow);
  }

  .panel {
    padding: 24px;
  }

  .panel.compact {
    gap: 2px;
    align-content: start;
  }

  .panel.compact h2 {
    margin: 0;
  }

  .panel.compact form {
    margin: 0;
  }

  .stack {
    display: grid;
    gap: 18px;
  }

  .form-stack {
    gap: 14px;
    margin-top: 0;
  }

  label {
    display: grid;
    gap: 8px;
    font-weight: 700;
    font-size: 0.92rem;
  }

  input[type="number"],
  input[type="text"] {
    width: 100%;
    border: 2px solid rgba(36, 26, 21, 0.8);
    background: rgba(255, 255, 255, 0.78);
    border-radius: 14px;
    padding: 12px 14px;
    font-size: 1rem;
  }

  .toggle {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
  }

  .toggle input {
    width: 18px;
    height: 18px;
  }

  .button-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 10px;
  }

  .count-block {
    display: grid;
    gap: 10px;
  }

  .count-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
  }

  .count-value {
    min-width: 86px;
    text-align: center;
    font-size: 1.05rem;
    font-weight: 800;
    border: 2px solid rgba(36, 26, 21, 0.8);
    border-radius: 14px;
    padding: 12px 10px;
    background: rgba(255, 255, 255, 0.78);
  }

  .count-slider {
    width: 100%;
    accent-color: var(--accent);
  }

  .preset-grid {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .preset-chip {
    border: 1px solid rgba(36, 26, 21, 0.28);
    border-radius: 999px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.72);
    color: var(--ink);
    font-size: 0.88rem;
    font-weight: 800;
    letter-spacing: 0;
    box-shadow: none;
  }

  .preset-chip:hover {
    background: rgba(244, 200, 173, 0.82);
  }

  .range-hint {
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.5;
  }

  .button, button {
    border: 0;
    border-radius: 999px;
    padding: 14px 22px;
    font-weight: 800;
    letter-spacing: 0.03em;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #fffaf3;
    background: linear-gradient(135deg, #1d1b18, #b1442b 80%);
    box-shadow: 0 10px 24px rgba(42, 28, 19, 0.24);
  }

  .button.secondary {
    color: var(--ink);
    background: linear-gradient(135deg, #f3deca, #f7efe4);
    border: 2px solid rgba(36, 26, 21, 0.85);
    box-shadow: none;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 14px;
    margin-top: 22px;
  }

  .stat {
    padding: 16px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.58);
    border: 1px dashed rgba(36, 26, 21, 0.5);
  }

  .stat strong {
    display: block;
    font-size: 1.7rem;
    margin-bottom: 6px;
  }

  .history-list, .result-list {
    display: grid;
    gap: 16px;
  }

  .history-card, .question-card {
    padding: 18px;
  }

  .history-meta, .fine {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.6;
  }

  .question-card {
    padding: 24px;
  }

  .question-index {
    display: inline-block;
    margin-bottom: 12px;
    padding: 6px 10px;
    border-radius: 999px;
    background: var(--accent-soft);
    font-size: 0.82rem;
    font-weight: 800;
  }

  .options {
    display: grid;
    gap: 10px;
    margin-top: 16px;
  }

  .option {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid rgba(36, 26, 21, 0.18);
    background: rgba(255, 255, 255, 0.6);
  }

  .option input {
    margin-top: 4px;
  }

  .option.correct {
    border-color: rgba(39, 89, 61, 0.4);
    background: var(--good-soft);
  }

  .option.correct .option-note {
    display: inline-flex;
  }

  .option-note {
    display: none;
    margin-top: 8px;
    padding: 4px 8px;
    border-radius: 999px;
    background: rgba(39, 89, 61, 0.14);
    color: var(--good);
    font-size: 0.78rem;
    font-weight: 800;
  }

  .correct-banner {
    margin-top: 14px;
    padding: 14px 16px;
    border-radius: 16px;
    border-left: 5px solid var(--good);
    background: rgba(39, 89, 61, 0.08);
    font-weight: 700;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 800;
  }

  .badge.good { color: var(--good); }
  .badge.bad { color: var(--bad); }

  .explanation {
    margin-top: 12px;
    padding: 16px;
    border-radius: 16px;
    background: rgba(255, 247, 240, 0.94);
    border-left: 5px solid var(--accent);
    white-space: pre-line;
  }

  .empty {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.56);
    color: var(--muted);
  }

  @media (max-width: 840px) {
    .grid {
      grid-template-columns: 1fr;
    }

    .shell {
      padding: 18px 14px 44px;
    }

    .masthead, .panel, .question-card, .history-card {
      border-radius: 22px;
    }

    .count-row {
      grid-template-columns: 1fr;
    }
  }
</style>
<script>
  function quizSetCount(value) {
    const input = document.getElementById("question-count-input");
    const slider = document.getElementById("question-count-slider");
    if (input) input.value = value;
    if (slider) slider.value = value;
  }

  function quizSyncCount(sourceId, targetId) {
    const source = document.getElementById(sourceId);
    const target = document.getElementById(targetId);
    if (!source || !target) return;
    target.value = source.value;
  }
</script>
"""


@dataclass(slots=True)
class QuizSession:
    questions: list[PresentedQuestion]
    count: int
    seed: int | None
    shuffle_answers: bool
    range_spec: str
    reveal_answers: bool
    results: list[QuizResult] | None = None
    history_saved: bool = False


class QuizAppState:
    def __init__(
        self,
        questions: list[Question],
        pdf_path: Path,
        history_path: str | Path,
        default_count: int = 10,
        default_ranges: str = "",
        default_reveal_answers: bool = False,
        default_shuffle_answers: bool = True,
    ) -> None:
        self.questions = questions
        self.pdf_path = Path(pdf_path)
        self.history_path = Path(history_path)
        self.default_count = default_count
        self.default_ranges = default_ranges
        self.default_reveal_answers = default_reveal_answers
        self.default_shuffle_answers = default_shuffle_answers
        self.sessions: dict[str, QuizSession] = {}

    def create_session(
        self,
        count: int,
        seed: int | None,
        shuffle_answers: bool,
        range_spec: str,
        reveal_answers: bool,
    ) -> str:
        filtered_questions = filter_questions_by_ranges(self.questions, range_spec)
        if not filtered_questions:
            raise ValueError("По указанным диапазонам не найдено ни одного вопроса.")

        session_id = secrets.token_urlsafe(12)
        selected_questions = build_quiz(
            filtered_questions,
            count=count,
            seed=seed,
            shuffle_answers=shuffle_answers,
        )
        self.sessions[session_id] = QuizSession(
            questions=selected_questions,
            count=count,
            seed=seed,
            shuffle_answers=shuffle_answers,
            range_spec=range_spec.strip(),
            reveal_answers=reveal_answers,
        )
        return session_id


def serve_web_app(
    questions: list[Question],
    pdf_path: Path,
    host: str,
    port: int,
    history_path: str | Path,
    default_count: int = 10,
    default_ranges: str = "",
    default_reveal_answers: bool = False,
    default_shuffle_answers: bool = True,
) -> int:
    state = QuizAppState(
        questions=questions,
        pdf_path=pdf_path,
        history_path=history_path,
        default_count=default_count,
        default_ranges=default_ranges,
        default_reveal_answers=default_reveal_answers,
        default_shuffle_answers=default_shuffle_answers,
    )
    server = ThreadingHTTPServer((host, port), _build_handler(state))
    print(f"Веб-интерфейс викторины запущен по адресу http://{host}:{port}")
    print("Нажмите Ctrl+C, чтобы остановить сервер.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()

    return 0


def _build_handler(state: QuizAppState) -> type[BaseHTTPRequestHandler]:
    class QuizHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._render_home()
                return
            if parsed.path == "/quiz":
                session = self._get_session(parsed.query)
                if session is None:
                    self._redirect("/")
                    return
                self._render_quiz(session)
                return
            self._send_html("Не найдено", _message_page("Не найдено", "Такой страницы не существует."), status=404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            form = self._read_form_data()

            if parsed.path == "/start":
                self._start_session(form)
                return
            if parsed.path == "/submit":
                session = self._get_session(parsed.query)
                if session is None:
                    self._redirect("/")
                    return
                self._submit_quiz(session, form)
                return
            if parsed.path == "/explanations":
                session = self._get_session(parsed.query)
                if session is None or session.results is None:
                    self._redirect("/")
                    return
                self._render_results(session, show_explanations=True)
                return

            self._send_html("Не найдено", _message_page("Не найдено", "Такой страницы не существует."), status=404)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _render_home(self) -> None:
            history_entries = load_history(state.history_path, limit=8)
            body = _page_shell(
                title="Лаборатория Викторин",
                content=_home_markup(
                    pdf_name=state.pdf_path.name,
                    question_count=len(state.questions),
                    history_entries=history_entries,
                    default_count=state.default_count,
                    default_ranges=state.default_ranges,
                    default_reveal_answers=state.default_reveal_answers,
                    default_shuffle_answers=state.default_shuffle_answers,
                ),
            )
            self._send_html("Главная", body)

        def _render_quiz(self, session: QuizSession) -> None:
            session_id = self._session_id_from_query(urlparse(self.path).query)
            body = _page_shell(
                title="Режим изучения" if session.reveal_answers else "Пройти викторину",
                content=_quiz_markup(session, session_id),
            )
            self._send_html("Вопросы", body)

        def _render_results(self, session: QuizSession, show_explanations: bool) -> None:
            assert session.results is not None
            session_id = self._session_id_from_query(urlparse(self.path).query)
            body = _page_shell(
                title="Результаты",
                content=_results_markup(session, session_id, show_explanations),
            )
            self._send_html("Результаты", body)

        def _start_session(self, form: dict[str, list[str]]) -> None:
            try:
                count = int(form.get("count", [str(state.default_count)])[0])
            except ValueError:
                count = state.default_count

            seed_raw = form.get("seed", [""])[0].strip()
            try:
                seed = int(seed_raw) if seed_raw else None
            except ValueError:
                seed = None

            shuffle_answers = form.get("shuffle_answers", ["off"])[0] == "on"
            reveal_answers = form.get("reveal_answers", ["off"])[0] == "on"
            range_spec = form.get("ranges", [""])[0].strip()

            try:
                session_id = state.create_session(
                    count=count,
                    seed=seed,
                    shuffle_answers=shuffle_answers,
                    range_spec=range_spec,
                    reveal_answers=reveal_answers,
                )
            except ValueError as error:
                body = _page_shell(
                    title="Не удалось запустить викторину",
                    content=_message_page("Не удалось запустить викторину", html.escape(str(error))),
                )
                self._send_html("Не удалось запустить викторину", body, status=400)
                return

            self._redirect(f"/quiz?{urlencode({'session': session_id})}")

        def _submit_quiz(self, session: QuizSession, form: dict[str, list[str]]) -> None:
            if session.reveal_answers:
                self._redirect(f"/quiz?{urlencode({'session': self._session_id_from_query(urlparse(self.path).query) or ''})}")
                return

            results: list[QuizResult] = []
            for index, question in enumerate(session.questions):
                key = f"answer_{index}"
                answer = form.get(key, [""])[0]
                selected_index = parse_answer(answer, len(question.options))
                results.append(QuizResult(question=question, selected_index=selected_index))

            session.results = results
            if not session.history_saved:
                save_history(
                    results=results,
                    pdf_name=state.pdf_path.name,
                    count=session.count,
                    seed=session.seed,
                    shuffle_answers=session.shuffle_answers,
                    mode="web",
                    history_path=state.history_path,
                    range_spec=session.range_spec,
                    reveal_answers=False,
                )
                session.history_saved = True

            self._render_results(session, show_explanations=False)

        def _read_form_data(self) -> dict[str, list[str]]:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8")
            return parse_qs(payload, keep_blank_values=True)

        def _get_session(self, query: str) -> QuizSession | None:
            session_id = self._session_id_from_query(query)
            if not session_id:
                return None
            return state.sessions.get(session_id)

        @staticmethod
        def _session_id_from_query(query: str) -> str | None:
            return parse_qs(query).get("session", [None])[0]

        def _send_html(self, title: str, body: str, status: int = 200) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", location)
            self.end_headers()

    return QuizHandler


def _page_shell(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  {PAGE_STYLE}
</head>
<body>
  <div class="shell">
    {content}
  </div>
</body>
</html>"""


def _home_markup(
    pdf_name: str,
    question_count: int,
    history_entries: list[dict[str, Any]],
    default_count: int,
    default_ranges: str,
    default_reveal_answers: bool,
    default_shuffle_answers: bool,
) -> str:
    history_html = _history_markup(history_entries)
    quick_counts = [value for value in (5, 10, 20, 30) if value <= question_count]
    if question_count not in quick_counts and question_count < 30:
        quick_counts.append(question_count)

    preset_buttons = "".join(
        f'<button class="preset-chip" type="button" onclick="quizSetCount({value})">{value}</button>'
        for value in quick_counts
    )
    reveal_checked = "checked" if default_reveal_answers else ""
    shuffle_checked = "checked" if default_shuffle_answers else ""

    return f"""
    <section class="masthead">
      <div class="eyebrow">Лаборатория Викторин</div>
      <h1>Превратите один PDF в бесконечную практику.</h1>
      <p class="lede">
        Локальное приложение извлекает отмеченные ответы из файла <strong>{html.escape(pdf_name)}</strong>,
        перемешивает варианты, собирает викторины по выбранным диапазонам и сохраняет историю ваших результатов.
      </p>
      <div class="stats">
        <div class="stat"><strong>{question_count}</strong>Распознанных вопросов</div>
        <div class="stat"><strong>{default_count}</strong>Вопросов по умолчанию</div>
        <div class="stat"><strong>Локально</strong>Работает полностью на вашем компьютере</div>
      </div>
    </section>

    <div class="grid">
      <section class="panel stack compact">
        <h2>Начать новую викторину</h2>
        <form method="post" action="/start" class="stack form-stack">
          <label>
            Количество вопросов
            <div class="count-block">
              <div class="count-row">
                <input
                  id="question-count-input"
                  type="number"
                  name="count"
                  min="1"
                  max="{question_count}"
                  value="{default_count}"
                  oninput="quizSyncCount('question-count-input', 'question-count-slider')"
                >
                <div class="count-value">1-{question_count}</div>
              </div>
              <input
                id="question-count-slider"
                class="count-slider"
                type="range"
                min="1"
                max="{question_count}"
                value="{default_count}"
                oninput="quizSyncCount('question-count-slider', 'question-count-input')"
              >
              <div class="preset-grid">
                {preset_buttons}
              </div>
              <div class="range-hint">Можно ввести число вручную, подвигать ползунок или выбрать быстрое значение.</div>
            </div>
          </label>
          <label>
            Диапазоны вопросов
            <input
              type="text"
              name="ranges"
              value="{html.escape(default_ranges)}"
              placeholder="Например: 1-50; 120-160; 200"
            >
          </label>
          <div class="range-hint">Оставьте поле пустым, чтобы использовать весь банк вопросов.</div>
          <label>
            Seed (необязательно)
            <input type="text" name="seed" placeholder="Оставьте пустым для новой случайной выборки">
          </label>
          <label class="toggle">
            <input type="checkbox" name="shuffle_answers" {shuffle_checked}>
            Перемешивать варианты ответов в каждом вопросе
          </label>
          <label class="toggle">
            <input type="checkbox" name="reveal_answers" {reveal_checked}>
            Режим изучения: сразу показывать правильные ответы
          </label>
          <div class="button-row">
            <button type="submit">Запустить викторину</button>
          </div>
          <div class="fine">Совет: используйте одинаковый seed, чтобы повторить тот же набор вопросов и порядок ответов.</div>
        </form>
      </section>
      <section class="panel stack">
        <h2>Последние попытки</h2>
        {history_html}
      </section>
    </div>
    """


def _history_markup(history_entries: list[dict[str, Any]]) -> str:
    if not history_entries:
        return '<div class="empty">Пока нет сохранённых попыток. После первой викторины результат появится здесь.</div>'

    cards: list[str] = ['<div class="history-list">']
    for entry in history_entries:
        score = entry["score"]
        extra = []
        if entry.get("range_spec"):
            extra.append(f"диапазоны={html.escape(entry['range_spec'])}")
        extra.append(f"перемешивание={_format_bool(entry['shuffle_answers'])}")
        extra_text = " | ".join(extra)
        cards.append(
            f"""
            <article class="history-card">
              <h3>{score['correct']}/{score['total']} правильных</h3>
              <div class="history-meta">
                {html.escape(entry['timestamp'])}<br>
                {_format_mode(entry['mode'])} | {extra_text}<br>
                {score['percentage']:.1f}% · {html.escape(entry['pdf_name'])}
              </div>
            </article>
            """
        )
    cards.append("</div>")
    return "".join(cards)


def _quiz_markup(session: QuizSession, session_id: str | None) -> str:
    if session.reveal_answers:
        return _study_markup(session)

    question_cards: list[str] = []

    for index, question in enumerate(session.questions, start=1):
        options = []
        for option_index, option in enumerate(question.options):
            label = label_for_option(option_index)
            options.append(
                f"""
                <label class="option">
                  <input type="radio" name="answer_{index - 1}" value="{label}">
                  <span><strong>{label}.</strong> {html.escape(option)}</span>
                </label>
                """
            )

        question_cards.append(
            f"""
            <article class="question-card">
              <div class="question-index">Вопрос {index} из {len(session.questions)}</div>
              <h2>{html.escape(question.prompt)}</h2>
              <div class="options">{''.join(options)}</div>
            </article>
            """
        )

    action = f"/submit?{urlencode({'session': session_id or ''})}"
    return f"""
    <section class="masthead">
      <div class="eyebrow">Онлайн Викторина</div>
      <h1>Пройдите полную викторину за один подход.</h1>
      <p class="lede">Любой вопрос можно пропустить. Объяснения появятся только после просмотра результата.</p>
      <div class="button-row">
        <a class="button secondary" href="/">На главную</a>
      </div>
    </section>
    <form method="post" action="{action}" class="stack" style="margin-top: 24px;">
      {''.join(question_cards)}
      <div class="panel">
        <div class="button-row">
          <button type="submit">Проверить результат</button>
        </div>
      </div>
    </form>
    """


def _study_markup(session: QuizSession) -> str:
    question_cards: list[str] = []

    for index, question in enumerate(session.questions, start=1):
        options = []
        for option_index, option in enumerate(question.options):
            label = label_for_option(option_index)
            correct_class = " correct" if option_index == question.correct_index else ""
            note = '<div class="option-note">Правильный ответ</div>' if option_index == question.correct_index else ""
            options.append(
                f"""
                <div class="option{correct_class}">
                  <span><strong>{label}.</strong> {html.escape(option)}{note}</span>
                </div>
                """
            )

        question_cards.append(
            f"""
            <article class="question-card">
              <div class="question-index">Вопрос {index} из {len(session.questions)}</div>
              <h2>{html.escape(question.prompt)}</h2>
              <div class="options">{''.join(options)}</div>
              <div class="correct-banner">Правильный ответ: {html.escape(build_correct_answer_text(question))}</div>
            </article>
            """
        )

    range_text = (
        f" Диапазоны: {html.escape(session.range_spec)}."
        if session.range_spec
        else ""
    )

    return f"""
    <section class="masthead">
      <div class="eyebrow">Режим Изучения</div>
      <h1>Правильные ответы показаны сразу.</h1>
      <p class="lede">Это не тестирование, а режим просмотра. Здесь отображаются только выбранные вопросы и их правильные ответы.{range_text}</p>
      <div class="button-row">
        <a class="button secondary" href="/">На главную</a>
      </div>
    </section>
    <div class="stack" style="margin-top: 24px;">
      {''.join(question_cards)}
    </div>
    """


def _results_markup(session: QuizSession, session_id: str | None, show_explanations: bool) -> str:
    assert session.results is not None
    correct, total = score_results(session.results)
    percentage = (correct / total) * 100 if total else 0
    wrong_results = [result for result in session.results if not result.is_correct]

    result_cards: list[str] = ['<div class="result-list">']
    for result in session.results:
        badge_class = "good" if result.is_correct else "bad"
        badge_text = "Верно" if result.is_correct else "Ошибка"
        selected = (
            f"{label_for_option(result.selected_index)}. {html.escape(result.question.options[result.selected_index])}"
            if result.selected_index is not None
            else "Пропущено"
        )
        correct_answer = html.escape(build_correct_answer_text(result.question))
        explanation_html = ""
        if show_explanations and not result.is_correct:
            explanation_html = f'<div class="explanation">{html.escape(build_explanation(result))}</div>'

        result_cards.append(
            f"""
            <article class="question-card">
              <div class="badge {badge_class}">{badge_text}</div>
              <h2>{html.escape(result.question.prompt)}</h2>
              <p><strong>Ваш ответ:</strong> {selected}</p>
              <p><strong>Правильный ответ:</strong> {correct_answer}</p>
              {explanation_html}
            </article>
            """
        )
    result_cards.append("</div>")

    explanation_prompt = ""
    if wrong_results and not show_explanations:
        explanation_prompt = f"""
        <section class="panel">
          <h2>Показать объяснения для неправильных ответов?</h2>
          <div class="button-row">
            <form method="post" action="/explanations?{urlencode({'session': session_id or ''})}">
              <button type="submit">Показать объяснения</button>
            </form>
          </div>
        </section>
        """

    range_suffix = f" | диапазоны: {html.escape(session.range_spec)}" if session.range_spec else ""

    return f"""
    <section class="masthead">
      <div class="eyebrow">Итоги</div>
      <h1>{correct}/{total} правильных.</h1>
      <p class="lede">Последняя попытка уже сохранена в локальной истории результатов.{range_suffix}</p>
      <div class="stats">
        <div class="stat"><strong>{percentage:.1f}%</strong>Точность</div>
        <div class="stat"><strong>{len(wrong_results)}</strong>Ошибок</div>
        <div class="stat"><strong>{'Вкл' if session.shuffle_answers else 'Выкл'}</strong>Перемешивание ответов</div>
      </div>
      <div class="button-row" style="margin-top: 20px;">
        <a class="button secondary" href="/">На главную</a>
      </div>
    </section>
    <div class="stack" style="margin-top: 24px;">
      {explanation_prompt}
      {''.join(result_cards)}
    </div>
    """


def _message_page(title: str, message: str) -> str:
    return f"""
    <section class="masthead">
      <div class="eyebrow">Лаборатория Викторин</div>
      <h1>{title}</h1>
      <p class="lede">{message}</p>
      <div class="button-row">
        <a class="button secondary" href="/">На главную</a>
      </div>
    </section>
    """


def _format_mode(mode: str) -> str:
    return {"cli": "Терминал", "web": "Веб"}.get(mode, mode)


def _format_bool(value: bool) -> str:
    return "да" if value else "нет"
