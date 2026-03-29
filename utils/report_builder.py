import io
import os
import tempfile
from datetime import datetime

from fpdf import FPDF
import plotly.graph_objects as go
import plotly.io as pio


def _sanitize(text: str) -> str:
    """Replace unicode characters that Helvetica can't render."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u2022": "-",   # bullet
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text


class ReportPDF(FPDF):
    def __init__(self, title: str = "Financial Report", user_name: str = ""):
        super().__init__()
        self.report_title = title
        self.user_name = user_name

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self.report_title, align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title_page(self, date_range: str = ""):
        self.add_page()
        self.ln(50)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(50, 50, 80)
        self.cell(0, 15, _sanitize(self.report_title), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(100, 100, 100)
        if self.user_name:
            self.cell(0, 10, _sanitize(f"Prepared for: {self.user_name}"), align="C", new_x="LMARGIN", new_y="NEXT")
        if date_range:
            self.cell(0, 10, _sanitize(f"Period: {date_range}"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(
            0, 10,
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )

    def add_section_header(self, text: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(50, 50, 80)
        self.cell(0, 12, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def add_stat_line(self, label: str, value: str):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(60, 60, 60)
        self.cell(70, 8, _sanitize(label), new_x="RIGHT")
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, _sanitize(value), new_x="LMARGIN", new_y="NEXT")

    def add_chart_image(self, fig: go.Figure, width: int = 180):
        """Render a Plotly figure to a temp PNG and embed it."""
        import subprocess
        import sys
        import json as _json

        tmp_json = os.path.join(tempfile.gettempdir(), f"fk_fig_{id(fig)}.json")
        tmp_png = os.path.join(tempfile.gettempdir(), f"fk_fig_{id(fig)}.png")

        try:
            # Write figure JSON, then render in a clean subprocess
            # (avoids kaleido conflicts with Streamlit's event loop)
            # Add extra bottom margin so axis labels don't get clipped
            fig.update_layout(margin=dict(l=60, r=40, t=50, b=80))
            with open(tmp_json, "w") as f:
                f.write(fig.to_json())

            script = (
                "import plotly.io as pio, json, sys;"
                f"fig = pio.from_json(open(r'{tmp_json}').read());"
                f"fig.write_image(r'{tmp_png}', format='png', width=900, height=600, scale=2)"
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr[-200:])

            self.image(tmp_png, w=width)
            self.ln(6)
        except Exception as e:
            self.set_font("Helvetica", "I", 10)
            self.cell(0, 8, f"[Chart error: {_sanitize(str(e)[:80])}]",
                      new_x="LMARGIN", new_y="NEXT")
        finally:
            for p in (tmp_json, tmp_png):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def add_table(self, headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None):
        if col_widths is None:
            page_w = self.w - self.l_margin - self.r_margin
            col_widths = [int(page_w / len(headers))] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(50, 50, 80)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, _sanitize(h), border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(40, 40, 40)
        for row in rows:
            if self.get_y() > 265:
                self.add_page()
            for i, cell_text in enumerate(row):
                self.cell(col_widths[i], 7, _sanitize(str(cell_text)[:40]), border=1, align="C")
            self.ln()

    def get_bytes(self) -> bytes:
        self.alias_nb_pages()
        return bytes(self.output())
