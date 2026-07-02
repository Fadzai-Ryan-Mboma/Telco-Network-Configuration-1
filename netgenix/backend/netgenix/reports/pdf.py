"""Small dependency-free PDF writer for executive report summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from textwrap import wrap
from typing import Mapping, Sequence


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 44


def _safe_text(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


class _PdfCanvas:
    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self.current: list[str] = []
        self.y = PAGE_HEIGHT - MARGIN
        self.add_page()

    def add_page(self) -> None:
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = PAGE_HEIGHT - MARGIN
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=(0.96, 0.98, 1.0), stroke=None)
        self.rect(0, PAGE_HEIGHT - 92, PAGE_WIDTH, 92, fill=(0.02, 0.10, 0.18), stroke=None)
        self.text(MARGIN, PAGE_HEIGHT - 42, "NetGenix", size=22, color=(1, 1, 1), bold=True)
        self.text(MARGIN, PAGE_HEIGHT - 66, "Network Performance Report", size=12, color=(0.58, 0.90, 0.86))
        self.y = PAGE_HEIGHT - 122

    def ensure_space(self, height: int) -> None:
        if self.y - height < MARGIN:
            self.add_page()

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: tuple[float, float, float] | None,
        stroke: tuple[float, float, float] | None = (0.80, 0.86, 0.91),
    ) -> None:
        if fill:
            self.current.append(f"{fill[0]} {fill[1]} {fill[2]} rg")
        if stroke:
            self.current.append(f"{stroke[0]} {stroke[1]} {stroke[2]} RG")
        self.current.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re")
        self.current.append("B" if fill and stroke else "f" if fill else "S")

    def text(
        self,
        x: float,
        y: float,
        text: object,
        *,
        size: int = 10,
        color: tuple[float, float, float] = (0.09, 0.13, 0.20),
        bold: bool = False,
    ) -> None:
        font = "F2" if bold else "F1"
        self.current.append(f"{color[0]} {color[1]} {color[2]} rg")
        self.current.append(f"BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({_safe_text(text)}) Tj ET")

    def paragraph(
        self,
        text: object,
        *,
        x: float = MARGIN,
        width: int = 86,
        size: int = 10,
        leading: int = 14,
        color: tuple[float, float, float] = (0.22, 0.28, 0.36),
    ) -> None:
        lines = wrap(str(text), width=width) or [""]
        self.ensure_space(len(lines) * leading + 4)
        for line in lines:
            self.text(x, self.y, line, size=size, color=color)
            self.y -= leading

    def heading(self, label: str) -> None:
        self.ensure_space(32)
        self.text(MARGIN, self.y, label, size=15, color=(0.02, 0.10, 0.18), bold=True)
        self.y -= 10
        self.rect(MARGIN, self.y, 64, 2, fill=(0.00, 0.55, 0.48), stroke=None)
        self.y -= 22

    def finish(self) -> bytes:
        if self.current:
            self.pages.append(self.current)
            self.current = []

        objects: list[bytes] = []
        catalog_id = 1
        pages_id = 2
        font_regular_id = 3
        font_bold_id = 4
        page_ids = []

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        for page in self.pages:
            content = "\n".join(page).encode("latin-1", errors="replace")
            content_id = len(objects) + 1
            objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
            page_id = len(objects) + 1
            page_ids.append(page_id)
            page_obj = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
            objects.append(page_obj)

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{index} 0 obj\n".encode())
            output.extend(obj)
            output.extend(b"\nendobj\n")

        xref_offset = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode())
        output.extend(
            f"trailer << /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode()
        )
        return bytes(output)


def _fmt(value: object, suffix: str = "") -> str:
    if isinstance(value, (int, float)):
        return f"{value:,.2f}{suffix}"
    return f"{value}{suffix}"


def _metric_card(canvas: _PdfCanvas, x: float, y: float, label: str, value: str, accent: tuple[float, float, float]) -> None:
    canvas.rect(x, y, 156, 70, fill=(1, 1, 1), stroke=(0.83, 0.88, 0.93))
    canvas.rect(x, y + 66, 156, 4, fill=accent, stroke=None)
    canvas.text(x + 12, y + 44, value, size=16, color=(0.02, 0.10, 0.18), bold=True)
    canvas.text(x + 12, y + 22, label, size=8, color=(0.38, 0.45, 0.54))


def _table(canvas: _PdfCanvas, title: str, rows: Sequence[Mapping[str, object]], metric: str, metric_label: str) -> None:
    canvas.heading(title)
    canvas.ensure_space(190)
    x = MARGIN
    canvas.rect(x, canvas.y - 18, 507, 24, fill=(0.90, 0.95, 0.97), stroke=(0.78, 0.85, 0.90))
    canvas.text(x + 10, canvas.y - 10, "Site", size=9, bold=True)
    canvas.text(x + 330, canvas.y - 10, metric_label, size=9, bold=True)
    canvas.text(x + 430, canvas.y - 10, "PRB %", size=9, bold=True)
    canvas.y -= 24
    for row in rows[:10]:
        canvas.ensure_space(22)
        canvas.rect(x, canvas.y - 16, 507, 22, fill=(1, 1, 1), stroke=(0.90, 0.93, 0.96))
        canvas.text(x + 10, canvas.y - 9, str(row.get("site_name", ""))[:46], size=8)
        canvas.text(x + 330, canvas.y - 9, _fmt(row.get(metric, 0.0)), size=8)
        canvas.text(x + 430, canvas.y - 9, _fmt(row.get("prb_busy_hour_weekly_average", 0.0)), size=8)
        canvas.y -= 22
    canvas.y -= 10


def write_pdf_report(
    output_path: Path,
    *,
    run_id: str,
    site_metrics: Sequence[Mapping[str, object]],
    top_sites: Sequence[Mapping[str, object]],
    bottom_sites: Sequence[Mapping[str, object]],
    top_prb_sites: Sequence[Mapping[str, object]],
    top_code_drop_sites: Sequence[Mapping[str, object]],
    executive_kpis: Mapping[str, object],
    original_filename: str,
) -> None:
    canvas = _PdfCanvas()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    included_sites = [site for site in site_metrics if not site.get("excluded")]

    canvas.text(MARGIN, canvas.y, f"Run {run_id}", size=10, color=(0.00, 0.55, 0.48), bold=True)
    canvas.y -= 18
    canvas.paragraph(
        "Executive-ready view of the Brighton weekly workflow: network KPIs, traffic rankings, PRB pressure, "
        "drop-rate watchlist, and source audit from uploaded raw MAE/Telrad/EPC/subscriber exports.",
        size=10,
    )
    canvas.y -= 8

    card_y = canvas.y - 74
    _metric_card(canvas, MARGIN, card_y, "Network Traffic", _fmt(executive_kpis.get("total_network_traffic_tb", 0.0), " TB"), (0.00, 0.55, 0.48))
    _metric_card(canvas, MARGIN + 176, card_y, "Availability", _fmt(executive_kpis.get("radio_network_availability", 0.0), "%"), (0.06, 0.62, 0.43))
    _metric_card(canvas, MARGIN + 352, card_y, "Sites Processed", f"{len(included_sites):,}", (0.82, 0.45, 0.00))
    canvas.y = card_y - 28

    canvas.heading("Key Insights")
    busiest = top_sites[0] if top_sites else {}
    lowest = bottom_sites[0] if bottom_sites else {}
    prb_hot = top_prb_sites[0] if top_prb_sites else {}
    drop_hot = top_code_drop_sites[0] if top_code_drop_sites else {}
    insights = [
        f"Total reported traffic is {_fmt(executive_kpis.get('total_network_traffic_tb', 0.0), ' TB')} across {len(included_sites):,} included sites.",
        f"Highest traffic site is {busiest.get('site_name', 'n/a')} with {_fmt(busiest.get('weekly_traffic_tb', 0.0), ' TB')}.",
        f"Lowest traffic site is {lowest.get('site_name', 'n/a')} with {_fmt(lowest.get('weekly_traffic_gb', 0.0), ' GB')}.",
        f"Highest PRB pressure is {prb_hot.get('site_name', 'n/a')} at {_fmt(prb_hot.get('prb_busy_hour_weekly_average', 0.0), '%')}.",
        f"Highest code/drop rate is {drop_hot.get('site_name', 'n/a')} at {_fmt(drop_hot.get('code_drop_average', 0.0), '%')}.",
    ]
    for insight in insights:
        canvas.paragraph(f"- {insight}", x=MARGIN + 8, width=82, size=9)

    _table(canvas, "Top Traffic Sites", top_sites, "weekly_traffic_tb", "Traffic TB")
    _table(canvas, "Bottom Traffic Sites", bottom_sites, "weekly_traffic_gb", "Traffic GB")
    _table(canvas, "PRB Pressure Watchlist", top_prb_sites, "prb_busy_hour_weekly_average", "PRB %")
    _table(canvas, "Code Drop Watchlist", top_code_drop_sites, "code_drop_average", "Drop %")

    canvas.heading("Audit And Source Notes")
    canvas.paragraph(f"Generated at: {generated_at}", size=9)
    canvas.paragraph(f"Source files: {original_filename}", size=9)
    canvas.paragraph(
        "Subscriber, penetration, and EPC-only measures are marked N/A when the report uses Evaluation data only.",
        size=9,
    )

    output_path.write_bytes(canvas.finish())
