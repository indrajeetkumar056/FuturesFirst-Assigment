from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas


def _write_pdf(path: Path, title: str, sections: list[tuple[str, list[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(path), pagesize=LETTER)
    width, height = LETTER

    def header(page_title: str):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, page_title)
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1.25 * inch, f"Generated: {date.today().isoformat()}")

    y = height - 1.7 * inch
    header(title)
    c.setFont("Helvetica", 11)

    for section_title, bullets in sections:
        if y < 2 * inch:
            c.showPage()
            header(title)
            y = height - 1.7 * inch
            c.setFont("Helvetica", 11)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, section_title)
        y -= 0.3 * inch
        c.setFont("Helvetica", 11)
        for b in bullets:
            if y < 1.5 * inch:
                c.showPage()
                header(title)
                y = height - 1.7 * inch
                c.setFont("Helvetica", 11)
            c.drawString(1.2 * inch, y, f"- {b}")
            y -= 0.25 * inch
        y -= 0.15 * inch

    c.save()


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "demo_data" / "pdfs"
    _write_pdf(
        out_dir / "quarterly_executive_report.pdf",
        "Quarterly Executive Report (Q4 2025)",
        [
            (
                "Executive Summary",
                [
                    "Sci-Fi engagement increased notably in October–December driven by Stellar Run and Dark Orbit.",
                    "Comedy underperformed in retention; reviews cite predictable plot and lower rewatch intent.",
                    "Mumbai and Bengaluru show strongest engagement momentum across premium segments.",
                ],
            ),
            (
                "Recommendations",
                [
                    "Increase marketing concentration in top-performing cities for Sci-Fi titles.",
                    "Pilot a comedy refresh strategy: stronger hooks in first 10 minutes, tighter episode cadence.",
                    "Focus Q1 roadmap on Sci-Fi + Action bundles for premium upsell.",
                ],
            ),
        ],
    )

    _write_pdf(
        out_dir / "campaign_performance_summary.pdf",
        "Campaign Performance Summary",
        [
            (
                "Key Observations",
                [
                    "Stellar Run campaign: higher CTR and sustained watch-time per viewer in late 2025.",
                    "Dark Orbit benefited from influencer clips; spikes correlated to short-form releases.",
                    "Comedy creatives generated clicks but did not convert to long-session watch-time.",
                ],
            )
        ],
    )

    _write_pdf(
        out_dir / "content_roadmap.pdf",
        "Content Roadmap (Next 2 Quarters)",
        [
            (
                "Planned Releases",
                [
                    "Sci-Fi: Stellar Run Season 2 (tentative), Dark Orbit spin-off (concept).",
                    "Drama: Last Kingdom limited series extension.",
                    "Comedy: new writers-room reboot for Laugh Riot format; aim for higher retention.",
                ],
            )
        ],
    )

    _write_pdf(
        out_dir / "audience_behavior_report.pdf",
        "Audience Behavior Report",
        [
            (
                "Audience Segments",
                [
                    "Gen Z shows highest sensitivity to short-form marketing and quick plot progression.",
                    "Premium users watch longer sessions; strongest in Mumbai, London, and Tokyo cohorts.",
                    "Family segment prefers animation and fantasy; higher weekend watch-time.",
                ],
            )
        ],
    )

    _write_pdf(
        out_dir / "policy_guidelines.pdf",
        "Policy Guidelines (Internal)",
        [
            (
                "Data Handling",
                [
                    "Use tool-based access for internal analytics. Avoid raw data dumps.",
                    "Only share aggregated metrics externally; redact identifiers where needed.",
                    "Maintain audit logs for queries and document retrieval traces.",
                ],
            )
        ],
    )

    print(f"Wrote demo PDFs to: {out_dir}")


if __name__ == "__main__":
    main()

