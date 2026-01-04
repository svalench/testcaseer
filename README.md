# TestCaseer

> CLI tool for recording browser actions and generating test cases for QA engineers.

[![CI](https://github.com/testcaseer/testcaseer/actions/workflows/ci.yml/badge.svg)](https://github.com/testcaseer/testcaseer/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎬 **Record browser actions** — clicks, inputs, navigation, and more
- 📸 **Automatic screenshots** — capture every step with visual documentation
- 🌐 **Network request logging** — track API calls triggered by actions
- 📄 **Multiple output formats** — JSON, Markdown, and HTML reports
- 🎛️ **In-browser control panel** — start/stop recording with UI buttons
- 🖥️ **Cross-platform** — works on Windows, macOS, and Linux

## Installation

```bash
pip install testcaseer
playwright install chromium
```

## Quick Start

```bash
# Record a test case
testcaseer record https://example.com --output ./my_test

# With options
testcaseer record https://example.com -o ./tests -n "Login Flow" -b firefox
```

## Usage

### Recording a Test Case

1. Run the `record` command with a URL:
   ```bash
   testcaseer record https://example.com -o ./output
   ```

2. A browser window opens with a control panel in the top-right corner

3. Click **"▶ Начать"** to start recording

4. Perform your test actions in the browser

5. Click **"⏹ Стоп"** to stop recording and save

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

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory for test case files | (required) |
| `--name` | `-n` | Test case name | auto-generated |
| `--browser` | `-b` | Browser to use: chromium, firefox, webkit | chromium |
| `--headless` | | Run browser in headless mode | false |
| `--timeout` | | Action timeout in milliseconds | 30000 |

## Development

### Setup

```bash
git clone https://github.com/testcaseer/testcaseer.git
cd testcaseer
pip install -e ".[dev]"
playwright install chromium
```

### Run Tests

```bash
# All tests
pytest

# Without slow tests
pytest -m "not slow"

# With coverage
pytest --cov=testcaseer
```

### Linting

```bash
ruff check src/
mypy src/
```

## License

MIT License — see [LICENSE](LICENSE) for details.

