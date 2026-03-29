"""Generate professional investor-ready CLM Platform v2.0 Pitch Deck PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas


# ── Colors: Enterprise-Grade Palette ─────────────────────
PRIMARY = HexColor("#0F172A")  # Slate 900
ACCENT = HexColor("#6366F1")   # Indigo 500
SUCCESS = HexColor("#10B981")  # Emerald 500
LIGHT_BG = HexColor("#F8FAFC") # Slate 50
WHITE = HexColor("#FFFFFF")
TEXT = HexColor("#334155")    # Slate 700
SUBTLE = HexColor("#94A3B8")   # Slate 400
SECTION_BG = HexColor("#F1F5F9") # Slate 100
BORDER = HexColor("#E2E8F0")   # Slate 200

# ── Styles ──────────────────────────────────────────────
style_title = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=22, leading=26,
    textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=2,
)
style_subtitle = ParagraphStyle(
    "Subtitle", fontName="Helvetica", fontSize=12, leading=15,
    textColor=ACCENT, alignment=TA_CENTER, spaceAfter=2,
)
style_meta = ParagraphStyle(
    "Meta", fontName="Helvetica-Bold", fontSize=9, leading=12,
    textColor=TEXT, alignment=TA_CENTER, spaceAfter=8,
)
style_section = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=11, leading=14,
    textColor=PRIMARY, spaceBefore=8, spaceAfter=4,
)
style_body = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=8.5, leading=11.5,
    textColor=TEXT, alignment=TA_JUSTIFY, spaceAfter=4,
)
style_bullet = ParagraphStyle(
    "Bullet", fontName="Helvetica", fontSize=8.2, leading=11,
    textColor=TEXT, leftIndent=14, bulletIndent=4, spaceAfter=2,
)
style_table_header = ParagraphStyle(
    "TH", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5,
    textColor=WHITE, alignment=TA_CENTER,
)
style_table_cell = ParagraphStyle(
    "TD", fontName="Helvetica", fontSize=8, leading=10.5,
    textColor=TEXT, alignment=TA_CENTER,
)
style_footer = ParagraphStyle(
    "Footer", fontName="Helvetica-Bold", fontSize=7, leading=9,
    textColor=SUBTLE, alignment=TA_CENTER,
)


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=15 * mm, bottomMargin=12 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []
    W = doc.width  # usable width

    # ── Decorative Header ──────────────────────────────
    story.append(HRFlowable(width="100%", thickness=5, color=ACCENT, spaceAfter=10))

    # ── Title Block ─────────────────────────────────────
    story.append(Paragraph("Contract Lifecycle Management (CLM) Platform v2.0", style_title))
    story.append(Paragraph("Next-Generation Enterprise Governance & Intelligence", style_subtitle))
    story.append(Paragraph("Strategic Pitch Deck for Scaling and Market Expansion", style_meta))
    story.append(HRFlowable(width="40%", thickness=1, color=BORDER, spaceAfter=8))

    # ── 1. The Market Opportunity ────────────────────────
    story.append(Paragraph("1. Market Need & Opportunity", style_section))
    story.append(Paragraph(
        "Modern enterprises face massive revenue leakage (up to 9% annually) due to unmanaged contracts, missed renewal deadlines, "
        "and opaque approval chains. Existing enterprise CLM solutions are often prohibitive for small-to-midsize organizations. "
        "The CLM Platform v2.0 fills this gap by offering a high-performance, open-source-first approach to contract governance.",
        style_body,
    ))

    # ── 2. The Solution: Six Pillars of Core Value ───────
    story.append(Paragraph("2. Core Product Pillars", style_section))
    features = [
        ("<b>Dynamic Lifecycle Management</b> \u2013 Full CRUD with multi-state workflows (Draft \u2192 Submitted \u2192 Approved \u2192 Executed) and automated version control.",
        ),
        ("<b>Smart Clause Library</b> \u2013 Version-controlled, category-specific clause templates (Liability, NDA, IP) for accelerated assembly.",
        ),
        ("<b>Enterprise Approval Engine</b> \u2013 Unlimited multi-level approval chains with mandatory rejection logging and real-time status promotion.",
        ),
        ("<b>Proactive SLA & Renewal Tracking</b> \u2013 Configurable look-ahead windows with automated notification triggers to prevent contract expiration gaps.",
        ),
        ("<b>Immutable Compliance Logging</b> \u2013 Complete SHA-256 hashed audit trails capturing every system event with IP and user-agent tracking.",
        ),
        ("<b>Granular RBAC Security</b> \u2013 Multi-tenant ready Role-Based Access Control with JWT refresh rotation and secure hashing (bcrypt).",
        ),
    ]
    for f in features:
        story.append(Paragraph(f"\u2022  {f[0]}", style_bullet))
    story.append(Spacer(1, 4))

    # ── 3. Technology Stack (Pin-Point Accuracy v2.0) ───
    story.append(Paragraph("3. Modern Architecture & Technology Stack", style_section))

    tech_data = [
        [Paragraph("Layer", style_table_header),
         Paragraph("Market-Leading Technologies", style_table_header),
         Paragraph("Purpose & Scalability", style_table_header)],
        [Paragraph("Frontend", style_table_cell),
         Paragraph("React 19.2, TypeScript 5.9, Vite 7.3, Ant Design 6.3, Redux Toolkit, Tailwind 4.2", style_table_cell),
         Paragraph("Modular SPA, Type-Safe UI components, High-performance build cycle", style_table_cell)],
        [Paragraph("Backend", style_table_cell),
         Paragraph("Python 3.12, FastAPI 0.104, SQLAlchemy 2.0.23, Pydantic v2", style_table_cell),
         Paragraph("Async High-Concurrency API, Validated Data Layer, ORM flexibility", style_table_cell)],
        [Paragraph("Data Storage", style_table_cell),
         Paragraph("SQLite (Development), PostgreSQL 16 (Production)", style_table_cell),
         Paragraph("18 Normalized Tables, Indexed for high-speed retrieval", style_table_cell)],
        [Paragraph("Security", style_table_cell),
         Paragraph("JWT + Refresh Rotation, bcrypt, CSRF Protection, TrustedHost", style_table_cell),
         Paragraph("Enterprise-Grade Auth, Origin Protection, API Rate-Limiting", style_table_cell)],
    ]
    tech_table = Table(tech_data, colWidths=[W * 0.15, W * 0.45, W * 0.40])
    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 6))

    # ── 4. Strategic Engineering Overview ────────────────
    story.append(Paragraph("4. Strategic Engineering Metrics", style_section))

    metrics_data = [
        [Paragraph("<b>70+</b><br/>RESTful API Endpoints", style_table_cell),
         Paragraph("<b>12</b><br/>Dedicated Service Layers", style_table_cell),
         Paragraph("<b>18</b><br/>Normalized DB Tables", style_table_cell),
         Paragraph("<b>100%</b><br/>Immutable Audit Logs", style_table_cell)],
    ]
    metrics_table = Table(metrics_data, colWidths=[W * 0.25, W * 0.25, W * 0.25, W * 0.25])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 1, ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 6))

    # ── 5. Competitive Edge ────────────────────────────
    story.append(Paragraph("5. Competitive Advantages", style_section))
    advantages = [
        "<b>Zero-Config Deployment:</b> Instant setup with SQLite fallback, ready for quick demonstration and prototyping.",
        "<b>Scale-First Design:</b> Clean separation of concerns between Service Layers and API Handlers for independent horizontal scaling.",
        "<b>Developer Velocity:</b> Type-safe full stack ensures rapid feature iteration without sacrificing data integrity.",
        "<b>Enterprise Ready:</b> Hashed audit compliance, multi-tenancy foundation (Organizations table), and production-grade security.",
    ]
    for adv in advantages:
        story.append(Paragraph(f"\u2022  {adv}", style_bullet))

    # ── 6. Conclusion & Roadmap ─────────────────────────
    story.append(Paragraph("6. Conclusion", style_section))
    story.append(Paragraph(
        "CLM Platform v2.0 represents a significant engineering milestone, offering a robust, secure, and modern alternative "
        "to high-priced contract management software. With its 70+ implemented endpoints, high-concurrency architecture, "
        "and sophisticated frontend ecosystem, it is ready for deployment in academic, research, and production environments.",
        style_body,
    ))

    # ── Footer ──────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph(
        "CLM Platform v2.0  |  Built with React 19 + FastAPI + PostgreSQL  |  Investor Pitch Deck Confidential",
        style_footer,
    ))

    doc.build(story)
    print(f"PINPOINT ACCURATE PDF GENERATED: {output_path}")


if __name__ == "__main__":
    build_pdf("CLM_Platform_Investor_Pitch_v2.pdf")
