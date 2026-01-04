<p align="center">
  <h1 align="center">🎬 TestCaseer</h1>
  <p align="center">
    <strong>Запишите один раз — тестируйте везде</strong><br>
    <em>Record once — test everywhere</em>
  </p>
</p>

<p align="center">
  <a href="https://github.com/testcaseer/testcaseer/actions/workflows/ci.yml"><img src="https://github.com/testcaseer/testcaseer/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13-blue.svg" alt="Python 3.13"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

---

## 🇷🇺 О проекте

**TestCaseer** — это open-source CLI-инструмент, который превращает ваши действия в браузере в готовые тест-кейсы. Забудьте о ручном написании документации — просто записывайте свои действия, а TestCaseer создаст подробные отчёты со скриншотами, понятные как QA-инженерам, так и AI-агентам.

### Для кого?

- 🧪 **QA-инженеры** — автоматизируйте документирование тестовых сценариев
- 🤖 **AI/ML разработчики** — создавайте датасеты для обучения автоматизации тестирования
- 👨‍💻 **Разработчики** — фиксируйте баги с полным контекстом действий пользователя

### Почему TestCaseer?

- ⚡ **Один клик** — начните запись прямо из браузера
- 📸 **Скриншоты на каждом шаге** — визуальное подтверждение действий
- 🌐 **Логи сети и консоли** — полная картина происходящего под капотом
- 📄 **3 формата вывода** — JSON для автоматизации, Markdown для документации, HTML для презентаций
- 🔓 **100% Open Source** — используйте и модифицируйте бесплатно

---

## 🇬🇧 About

**TestCaseer** is an open-source CLI tool that transforms your browser actions into ready-to-use test cases. Stop writing documentation manually — just record your actions, and TestCaseer generates detailed reports with screenshots, readable by both QA engineers and AI agents.

### Who is it for?

- 🧪 **QA Engineers** — automate test scenario documentation
- 🤖 **AI/ML Developers** — create datasets for test automation training
- 👨‍💻 **Developers** — capture bugs with full user action context

### Why TestCaseer?

- ⚡ **One click** — start recording directly from browser
- 📸 **Screenshot every step** — visual proof of actions
- 🌐 **Network & console logs** — full picture of what happens under the hood
- 📄 **3 output formats** — JSON for automation, Markdown for docs, HTML for presentations
- 🔓 **100% Open Source** — use and modify for free

---

## ✨ Features

- 🎬 **Record browser actions** — clicks, inputs, navigation, and more
- 📸 **Automatic screenshots** — capture every step with visual documentation
- 🌐 **Network request logging** — track API calls with headers & body
- 📝 **Console log capture** — JavaScript errors and console output
- 📄 **Multiple output formats** — JSON, Markdown, and HTML reports
- 🎛️ **In-browser control panel** — start/stop recording with UI buttons
- 🖥️ **Cross-platform** — works on Windows, macOS, and Linux

---

## 🚀 Installation

```bash
pip install testcaseer
playwright install chromium
```

## ⚡ Quick Start

```bash
# Record a test case
testcaseer record https://example.com --output ./my_test

# With options
testcaseer record https://example.com -o ./tests -n "Login Flow" -b firefox
```

## 📖 Usage

### Recording a Test Case

1. Run the `record` command with a URL:
   ```bash
   testcaseer record https://example.com -o ./output
   ```

2. A browser window opens with a control panel in the top-right corner

3. Click **"▶ Начать"** (Start) to begin recording

4. Perform your test actions in the browser

5. Click **"⏹ Стоп"** (Stop) to finish and save

### Output

After recording, you'll find these files in your output directory:

```
output/
├── screenshots/
│   ├── 001_click_login-button.png
│   ├── 002_input_email-field.png
│   └── ...
├── testcase.json    # Machine-readable format
├── testcase.md      # Markdown documentation
└── testcase.html    # Visual HTML report
```

---

## 🛠️ CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory for test case files | (required) |
| `--name` | `-n` | Test case name | auto-generated |
| `--browser` | `-b` | Browser: chromium, firefox, webkit | chromium |
| `--headless` | | Run browser in headless mode | false |
| `--timeout` | `-t` | Action timeout in milliseconds | 30000 |

---

## 🧑‍💻 Development

### Setup

```bash
git clone https://github.com/testcaseer/testcaseer.git
cd testcaseer
pip install -e ".[dev]"
playwright install chromium
```

### Run Tests

```bash
pytest                      # All tests
pytest -m "not slow"        # Skip slow tests
pytest --cov=testcaseer     # With coverage
```

### Linting

```bash
ruff check src/
ruff format src/
mypy src/testcaseer --ignore-missing-imports
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>⭐ Star us on GitHub if TestCaseer helps you!</strong>
</p>
