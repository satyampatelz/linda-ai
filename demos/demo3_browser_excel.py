"""Demo 3 (standalone, no LLM needed): research a topic on Wikipedia in the
VISIBLE browser and save an Excel report.

Usage (from the project root, venv active):
    python demos/demo3_browser_excel.py "Machine Learning"

What friends see: Chromium opens on screen, goes to the Wikipedia page,
and a moment later an Excel report appears in workspace/.

Tip: the same demo also works through the chat UI — just ask Linda:
"Research 'Machine Learning' on Wikipedia and make an Excel report
with 5 key points in the workspace."
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from backend.app.config import settings
from backend.app.tools import browser_tool


def main() -> None:
    topic = sys.argv[1] if len(sys.argv) > 1 else "Machine Learning"
    url = "https://en.wikipedia.org/wiki/" + topic.replace(" ", "_")

    print(f"[1/4] Opening in the browser: {url}")
    print("      " + browser_tool.browser_open(url))

    print("[2/4] Reading the page...")
    text = browser_tool.browser_read()
    body = text.split("Links (first 30):")[0]
    paragraphs = [p.strip() for p in body.split("\n") if len(p.strip()) > 80]
    key_points = paragraphs[:8]
    print(f"      Found {len(key_points)} key paragraphs.")

    print("[3/4] Taking a screenshot...")
    print("      " + browser_tool.browser_screenshot("demo3_wikipedia.png"))

    print("[4/4] Building the Excel report...")
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    ws["A1"] = f"Research Report: {topic}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Source: {url}"
    ws["A2"].font = Font(italic=True, size=10)
    ws["A4"] = "Key points (from Wikipedia)"
    ws["A4"].font = Font(bold=True, size=12)
    row = 5
    for i, point in enumerate(key_points, start=1):
        ws.cell(row=row, column=1, value=f"{i}. {point}")
        ws.cell(row=row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 45
        row += 1
    ws.column_dimensions["A"].width = 120

    out = settings.workspace_dir / f"{topic.replace(' ', '_')}_report.xlsx"
    wb.save(out)
    print(f"      Report saved: {out}")
    print("Done! The browser is still open — use browser_close to close it.")
    print("      (Or close the browser window by hand.)")


if __name__ == "__main__":
    main()
