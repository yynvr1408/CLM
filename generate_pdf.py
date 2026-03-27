"""Generate professional single-page CLM Platform documentation PDF."""
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


# ── Colors ──────────────────────────────────────────────
PRIMARY = HexColor("#1B2A4A")
ACCENT = HexColor("#2E86DE")
LIGHT_BG = HexColor("#F0F4F8")
WHITE = HexColor("#FFFFFF")
TEXT = HexColor("#2C3E50")
SUBTLE = HexColor("#7F8C8D")
SECTION_BG = HexColor("#E8EEF4")
BORDER = HexColor("#BDC3C7")

# ── Styles ──────────────────────────────────────────────
style_title = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=18, leading=22,
    textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=2,
)
style_subtitle = ParagraphStyle(
    "Subtitle", fontName="Helvetica", fontSize=10, leading=13,
    textColor=ACCENT, alignment=TA_CENTER, spaceAfter=1,
)
style_meta = ParagraphStyle(
    "Meta", fontName="Helvetica", fontSize=8, leading=10,
    textColor=SUBTLE, alignment=TA_CENTER, spaceAfter=6,
)
style_section = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
    textColor=PRIMARY, spaceBefore=6, spaceAfter=3,
)
style_body = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=7.8, leading=10.5,
    textColor=TEXT, alignment=TA_JUSTIFY, spaceAfter=3,
)
style_bullet = ParagraphStyle(
    "Bullet", fontName="Helvetica", fontSize=7.5, leading=10,
    textColor=TEXT, leftIndent=12, bulletIndent=4, spaceAfter=1,
)
style_table_header = ParagraphStyle(
    "TH", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5,
    textColor=WHITE, alignment=TA_CENTER,
)
style_table_cell = ParagraphStyle(
    "TD", fontName="Helvetica", fontSize=7.2, leading=9.5,
    textColor=TEXT, alignment=TA_CENTER,
)
style_footer = ParagraphStyle(
    "Footer", fontName="Helvetica-Oblique", fontSize=6.5, leading=8,
    textColor=SUBTLE, alignment=TA_CENTER,
)


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=14 * mm, bottomMargin=10 * mm,
        leftMargin=16 * mm, rightMargin=16 * mm,
    )
    story = []
    W = doc.width  # usable width

    # ── Decorative top bar ──────────────────────────────
    story.append(HRFlowable(width="100%", thickness=3, color=ACCENT, spaceAfter=8))

    # ── Title Block ─────────────────────────────────────
    story.append(Paragraph("Contract Lifecycle Management (CLM) Platform", style_title))
    story.append(Paragraph("An Enterprise-Grade Solution for End-to-End Contract Governance", style_subtitle))
    story.append(Paragraph(
        "Academic Year 2025-26  |  Department of Information Technology  |  Full-Stack Web Application Project",
        style_meta,
    ))
    story.append(Paragraph(
        "Team Members: YY Nandivardhan Reddy  |  Adhisheshu  |  V Tejaswi Reddy  |  PJ Renu  |  Sisindri Singamsetti",
        style_meta,
    ))
    story.append(HRFlowable(width="60%", thickness=0.8, color=BORDER, spaceAfter=6))

    # ── 1. Abstract ─────────────────────────────────────
    story.append(Paragraph("1. Abstract", style_section))
    story.append(Paragraph(
        "The CLM Platform is a full-stack web application engineered to digitize and streamline the complete "
        "contract lifecycle\u2014from drafting and clause assembly through multi-level approvals, execution tracking, "
        "renewal alerting, and compliance auditing. By replacing manual, spreadsheet-driven processes with a centralized, "
        "role-based system, the platform reduces contract cycle times, eliminates version-control errors, and ensures "
        "regulatory compliance through immutable audit trails.",
        style_body,
    ))

    # ── 2. Problem Statement ────────────────────────────
    story.append(Paragraph("2. Problem Statement", style_section))
    story.append(Paragraph(
        "Organizations managing contracts manually face critical challenges: version conflicts from email-based drafting, "
        "missed renewal deadlines costing up to 9% of annual revenue (IACCM), opaque approval chains lacking accountability, "
        "and compliance risks from absent audit trails. Existing enterprise CLM solutions carry prohibitive licensing costs, "
        "making them inaccessible for mid-size enterprises and academic research environments.",
        style_body,
    ))

    # ── 3. Proposed Solution ────────────────────────────
    story.append(Paragraph("3. Proposed Solution", style_section))
    story.append(Paragraph(
        "A modern, open-source CLM platform built on a decoupled architecture with a React single-page application "
        "communicating via RESTful APIs to a FastAPI backend. The system provides:",
        style_body,
    ))
    features = [
        ("<b>Contract Management</b> \u2013 Full CRUD with automatic version control, status workflow (Draft \u2192 Submitted \u2192 Approved \u2192 Executed), and contract-number generation.",
        ),
        ("<b>Clause Library</b> \u2013 Reusable, versioned clause templates organized by category (Payment, Liability, NDA, IP, etc.) that can be attached to contracts at creation time.",
        ),
        ("<b>Multi-Level Approval Workflows</b> \u2013 Configurable approval chains with mandatory rejection comments, real-time status tracking, and automatic contract-status promotion upon full approval.",
        ),
        ("<b>Renewal &amp; SLA Tracking</b> \u2013 Proactive renewal alerts with configurable look-ahead windows, overdue detection, and notification-sent flags to prevent duplicate alerts.",
        ),
        ("<b>Compliance Audit Logging</b> \u2013 Immutable, filterable audit trail capturing every action (create, update, approve, delete) with before/after change snapshots and IP tracking.",
        ),
        ("<b>Role-Based Access Control</b> \u2013 JWT authentication with bcrypt password hashing, refresh-token rotation, and granular permission enforcement (Admin / User roles).",
        ),
    ]
    for f in features:
        story.append(Paragraph(f"\u2022  {f[0]}", style_bullet))
    story.append(Spacer(1, 3))

    # ── 4. Technology Stack ─────────────────────────────
    story.append(Paragraph("4. Technology Stack", style_section))

    tech_data = [
        [Paragraph("Layer", style_table_header),
         Paragraph("Technologies", style_table_header),
         Paragraph("Purpose", style_table_header)],
        [Paragraph("Frontend", style_table_cell),
         Paragraph("React 19, TypeScript 5.9, Vite 7, Redux Toolkit, Ant Design 6, Recharts", style_table_cell),
         Paragraph("SPA with type safety, state management, charting", style_table_cell)],
        [Paragraph("Backend", style_table_cell),
         Paragraph("Python 3.11, FastAPI, SQLAlchemy ORM, Pydantic v2", style_table_cell),
         Paragraph("Async REST API, ORM, request validation", style_table_cell)],
        [Paragraph("Database", style_table_cell),
         Paragraph("PostgreSQL 16 / SQLite (dev)", style_table_cell),
         Paragraph("Relational store with 9 normalized tables", style_table_cell)],
        [Paragraph("Security", style_table_cell),
         Paragraph("JWT (HS256), bcrypt, CORS, TrustedHost MW", style_table_cell),
         Paragraph("Auth, password hashing, origin protection", style_table_cell)],
        [Paragraph("DevOps", style_table_cell),
         Paragraph("Docker, Docker Compose, GitHub Actions, Nginx", style_table_cell),
         Paragraph("Containerization, CI/CD, reverse proxy", style_table_cell)],
    ]
    tech_table = Table(tech_data, colWidths=[W * 0.14, W * 0.46, W * 0.40])
    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 4))

    # ── 5. System Architecture ──────────────────────────
    story.append(Paragraph("5. System Architecture Overview", style_section))

    arch_data = [
        [Paragraph("<b>React SPA</b><br/>(Port 5173)", style_table_cell),
         Paragraph("\u2192 REST API \u2192", style_table_cell),
         Paragraph("<b>FastAPI Backend</b><br/>(Port 8000)", style_table_cell),
         Paragraph("\u2192 ORM \u2192", style_table_cell),
         Paragraph("<b>PostgreSQL / SQLite</b><br/>(Port 5432)", style_table_cell)],
    ]
    arch_row_2 = [
        [Paragraph("Ant Design UI\nRedux Store\nReact Router v7", style_table_cell),
         Paragraph("", style_table_cell),
         Paragraph("39 Endpoints\n7 Service Classes\nJWT Auth Layer", style_table_cell),
         Paragraph("", style_table_cell),
         Paragraph("9 Tables\nIndexed &amp; Normalized\nAudit Logging", style_table_cell)],
    ]
    arch_table = Table(arch_data + arch_row_2, colWidths=[W * 0.26, W * 0.12, W * 0.26, W * 0.10, W * 0.26])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#E3F2FD")),
        ("BACKGROUND", (2, 0), (2, -1), HexColor("#E8F5E9")),
        ("BACKGROUND", (4, 0), (4, -1), HexColor("#FFF3E0")),
        ("BACKGROUND", (1, 0), (1, -1), WHITE),
        ("BACKGROUND", (3, 0), (3, -1), WHITE),
        ("BOX", (0, 0), (0, -1), 1, ACCENT),
        ("BOX", (2, 0), (2, -1), 1, HexColor("#27AE60")),
        ("BOX", (4, 0), (4, -1), 1, HexColor("#E67E22")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 4))

    # ── 6. Key Advantages ───────────────────────────────
    story.append(Paragraph("6. Key Advantages", style_section))

    adv_left = [
        "\u2022  <b>Zero-Config Development</b> \u2013 SQLite fallback eliminates database setup; single command starts both servers.",
        "\u2022  <b>Type-Safe Full Stack</b> \u2013 TypeScript on the frontend + Pydantic on the backend ensures end-to-end data integrity.",
        "\u2022  <b>Production-Ready Security</b> \u2013 JWT refresh rotation, bcrypt hashing, CORS, and TrustedHost middleware.",
    ]
    adv_right = [
        "\u2022  <b>Immutable Audit Compliance</b> \u2013 Every state change is logged with user, timestamp, IP, and change diff.",
        "\u2022  <b>Modular Architecture</b> \u2013 Service-layer separation enables independent scaling and testing of each domain.",
        "\u2022  <b>CI/CD Pipeline</b> \u2013 GitHub Actions automates linting, testing, Docker builds, and production deployment.",
    ]

    adv_col1 = "<br/>".join(adv_left)
    adv_col2 = "<br/>".join(adv_right)

    adv_table = Table(
        [[Paragraph(adv_col1, style_bullet), Paragraph(adv_col2, style_bullet)]],
        colWidths=[W * 0.50, W * 0.50],
    )
    adv_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(adv_table)
    story.append(Spacer(1, 4))

    # ── 7. Conclusion ───────────────────────────────────
    story.append(Paragraph("7. Conclusion", style_section))
    story.append(Paragraph(
        "The CLM Platform demonstrates a production-grade approach to contract governance by combining modern web technologies "
        "with enterprise design patterns. With 39 fully implemented API endpoints, 9 normalized database tables, a responsive "
        "React dashboard with real-time analytics, and comprehensive audit logging, the system addresses the complete contract "
        "lifecycle. The decoupled architecture, containerized deployment pipeline, and role-based security model make it "
        "suitable for both academic demonstration and real-world enterprise deployment.",
        style_body,
    ))

    # ── Footer ──────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph(
        "CLM Platform v1.0.0  |  Full-Stack Web Application  |  "
        "React 19 + FastAPI + PostgreSQL  |  Academic Year 2025-26",
        style_footer,
    ))

    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_pdf("CLM_Platform_Project_Documentation.pdf")
