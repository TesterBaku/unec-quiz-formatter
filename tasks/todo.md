# Todo

- [x] Confirm project shape and assumptions for a CLI quiz tool
- [x] Create a Python virtual environment and install dependencies
- [x] Scaffold project files and dependencies
- [x] Implement PDF text extraction and question parsing
- [x] Implement random 10-question quiz flow with scoring
- [x] Implement optional mistake explanations with correct answers
- [x] Add automated tests for parser and quiz logic
- [x] Verify behavior against the provided PDF
- [x] Add answer shuffling while preserving the correct-answer mapping
- [x] Persist quiz results to a history file
- [x] Add a simple local web UI for taking quizzes and reviewing results
- [x] Verify the updated CLI, history persistence, and web UI
- [x] Add a reproducible Windows executable build flow
- [x] Build a shareable executable from the current app
- [x] Verify the generated executable and document how to share it

# Review

- Installed a local Python 3.12 runtime with `uv`, created `.venv`, and installed `pypdf`, `pytest`, and the project itself in editable mode.
- Parsed the provided PDF successfully and extracted 678 multiple-choice questions with embedded correct answers.
- Verified automated tests with `.\.venv\Scripts\python.exe -m pytest` and received `8 passed`.
- Verified the interactive CLI with `.\.venv\Scripts\python.exe -m quiz_formatter --count 10 --seed 1`, including scoring and the follow-up explanation prompt for incorrect answers.
- Added answer shuffling that preserves the correct-answer mapping even if duplicate option text appears.
- Added persistent quiz history in `.quiz-cache/history.jsonl` and verified it via `.\.venv\Scripts\python.exe -m quiz_formatter --show-history`.
- Verified the updated CLI with `.\.venv\Scripts\python.exe -m pytest` and a live seeded quiz run that saved score history.
- Verified the web handlers through a real local `ThreadingHTTPServer` route test for home, start, submit, and explanations flows.
- Inspected the rendered web UI in the browser using preview files at `.quiz-cache\web-home-preview.html` and `.quiz-cache\web-results-preview.html`.
- Added a repeatable Windows packaging flow with `build_exe.ps1`, `launcher.py`, and `quiz_formatter.spec`.
- Installed `PyInstaller`, built `dist\quiz_formatter.exe`, and verified the executable with `--parse-only` and `--show-history`.
- Fixed a Windows console encoding crash in the frozen executable by configuring UTF-8 output at process startup.
