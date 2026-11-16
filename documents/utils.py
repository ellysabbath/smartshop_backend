"""
Utility ya kuzalisha PDF documents.
Inatumia reportlab kwa kuunda PDF.
"""
from datetime import datetime
from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ==================================================================
# Rangi
# ==================================================================
BRAND_COLOR = colors.HexColor("#2563eb")
DARK_COLOR = colors.HexColor("#1e293b")
LIGHT_GRAY = colors.HexColor("#f1f5f9")
MID_GRAY = colors.HexColor("#94a3b8")
BORDER_GRAY = colors.HexColor("#e2e8f0")
EMERALD = colors.HexColor("#10b981")
RED = colors.HexColor("#ef4444")
AMBER = colors.HexColor("#f59e0b")


def _fmt_tzs(value) -> str:
    """Format TZS."""
    try:
        n = float(value)
    except (ValueError, TypeError):
        n = 0
    return f"TZS {n:,.0f}"


def _fmt_num(value) -> str:
    try:
        n = float(value)
    except (ValueError, TypeError):
        n = 0
    return f"{n:,.0f}"


def _fmt_date(value) -> str:
    """Format date."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value)


# ==================================================================
# PDF Builder
# ==================================================================
class PDFBuilder:
    """Kujenga PDF kwa document."""

    def __init__(self, buffer=None):
        self.buffer = buffer or BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name="CustomTitle",
            parent=self.styles["Title"],
            fontSize=18,
            textColor=DARK_COLOR,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name="CustomSubtitle",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=self.styles["Heading2"],
            fontSize=12,
            textColor=BRAND_COLOR,
            spaceBefore=12,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name="SmallNormal",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=DARK_COLOR,
        ))
        self.styles.add(ParagraphStyle(
            name="RightAlign",
            parent=self.styles["SmallNormal"],
            alignment=TA_RIGHT,
        ))

    def build(
        self,
        aina: str,
        jina: str,
        store_name: str,
        kipindi: str,
        aliyezalisha: str,
        data: dict,
    ) -> bytes:
        """
        Unda PDF.
        Rudisha bytes.
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=jina,
            author=aliyezalisha,
        )

        story = []

        # ------------------------------------------------------------
        # Header
        # ------------------------------------------------------------
        story.append(Paragraph(
            "SMART HARDWARE", 
            ParagraphStyle(
                name="BrandHeader",
                fontSize=20,
                textColor=BRAND_COLOR,
                alignment=TA_CENTER,
                spaceAfter=4,
                fontName="Helvetica-Bold",
            ),
        ))
        story.append(Paragraph(
            jina,
            self.styles["CustomTitle"],
        ))
        story.append(Paragraph(
            f"{store_name} — {kipindi}",
            self.styles["CustomSubtitle"],
        ))
        story.append(Spacer(1, 8))

        # ------------------------------------------------------------
        # Meta info
        # ------------------------------------------------------------
        meta_data = [
            ["Tarehe:", _fmt_date(datetime.now())],
            ["Aliyezalisha:", aliyezalisha],
            ["Aina ya Ripoti:", aina.upper()],
        ]
        meta_table = Table(meta_data, colWidths=[35 * mm, 130 * mm])
        meta_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), MID_GRAY),
            ("TEXTCOLOR", (1, 0), (1, -1), DARK_COLOR),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # ------------------------------------------------------------
        # Content kulingana na aina
        # ------------------------------------------------------------
        if aina == "mauzo":
            story.extend(self._build_mauzo(data))
        elif aina == "stoki":
            story.extend(self._build_stoki(data))
        elif aina == "wateja":
            story.extend(self._build_wateja(data))
        elif aina == "madeni":
            story.extend(self._build_madeni(data))
        elif aina == "gharama":
            story.extend(self._build_gharama(data))
        elif aina == "jumla":
            story.extend(self._build_jumla(data))
        else:
            story.append(Paragraph(
                f"Hakuna template ya aina '{aina}'",
                self.styles["SmallNormal"],
            ))

        # ------------------------------------------------------------
        # Footer
        # ------------------------------------------------------------
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"<font color='#94a3b8' size='7'>"
            f"Ripoti hii imezalishwa na Smart Hardware POS kwa tarehe "
            f"{_fmt_date(datetime.now())}. "
            f"Data ni snapshot ya wakati wa kuzalisha."
            f"</font>",
            self.styles["SmallNormal"],
        ))

        doc.build(story)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf

    # ==================================================================
    # MAUZO
    # ==================================================================
    def _build_mauzo(self, data: dict):
        story = []
        story.append(Paragraph("Muhtasari wa Mauzo", self.styles["SectionTitle"]))

        stats = [
            ["Mauzo Yote", _fmt_tzs(data.get("mauzo", 0))],
            ["COGS", _fmt_tzs(data.get("cogs", 0))],
            ["Faida Ghafi", _fmt_tzs(data.get("faida", 0))],
            ["Orders", _fmt_num(data.get("orders", 0))],
            ["Wastani/Order", _fmt_tzs(data.get("wastani_kwa_order", 0))],
        ]

        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), DARK_COLOR),
            ("TEXTCOLOR", (1, 0), (1, -1), DARK_COLOR),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white]),
        ]))

        # Faida kijani
        t.setStyle(TableStyle([
            ("TEXTCOLOR", (1, 2), (1, 2), EMERALD),
        ]))

        story.append(t)
        return story

    # ==================================================================
    # STOKI
    # ==================================================================
    def _build_stoki(self, data: dict):
        story = []
        story.append(Paragraph("Muhtasari wa Stoki", self.styles["SectionTitle"]))

        stats = [
            ["Bidhaa Zote", _fmt_num(data.get("bidhaa_zote", 0))],
            ["Stoki Jumla", f"{_fmt_num(data.get('stoki_jumla', 0))} pcs"],
            ["Zimeisha", _fmt_num(data.get("zimeisha", 0))],
            ["Zinaribia", _fmt_num(data.get("zinaribia", 0))],
            ["Thamani", _fmt_tzs(data.get("thamani", 0))],
        ]

        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ]))

        # Zimeisha red, zinaribia amber
        t.setStyle(TableStyle([
            ("TEXTCOLOR", (1, 2), (1, 2), RED),
            ("TEXTCOLOR", (1, 3), (1, 3), AMBER),
            ("TEXTCOLOR", (1, 4), (1, 4), BRAND_COLOR),
        ]))

        story.append(t)
        return story

    # ==================================================================
    # WATEJA
    # ==================================================================
    def _build_wateja(self, data: dict):
        story = []
        story.append(Paragraph("Muhtasari wa Wateja", self.styles["SectionTitle"]))

        stats = [
            ["Wateja Wote", _fmt_num(data.get("wateja_wote", 0))],
            ["Manunuzi Jumla", _fmt_tzs(data.get("manunuzi_jumla", 0))],
            ["Deni Jumla", _fmt_tzs(data.get("deni_jumla", 0))],
        ]

        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (1, 1), (1, 1), EMERALD),
            ("TEXTCOLOR", (1, 2), (1, 2), RED),
        ]))

        story.append(t)
        return story

    # ==================================================================
    # MADENI
    # ==================================================================
    def _build_madeni(self, data: dict):
        story = []
        story.append(Paragraph("Muhtasari wa Madeni", self.styles["SectionTitle"]))

        stats = [
            ["Orders za Deni", _fmt_num(data.get("orders_deni", 0))],
            ["Deni Jumla", _fmt_tzs(data.get("deni_jumla", 0))],
        ]

        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (1, 1), (1, 1), RED),
        ]))

        story.append(t)
        return story

    # ==================================================================
    # GHARAMA
    # ==================================================================
    def _build_gharama(self, data: dict):
        story = []
        story.append(Paragraph("Muhtasari wa Gharama", self.styles["SectionTitle"]))

        stats = [
            ["Opex (bila mishahara)", _fmt_tzs(data.get("opex", 0))],
            ["Mishahara", _fmt_tzs(data.get("mishahara", 0))],
            ["Gharama Zote", _fmt_tzs(data.get("gharama_jumla", 0))],
        ]

        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (1, 0), (1, 0), AMBER),
            ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor("#a855f7")),
            ("TEXTCOLOR", (1, 2), (1, 2), RED),
        ]))

        story.append(t)
        return story

    # ==================================================================
    # JUMLA
    # ==================================================================
    def _build_jumla(self, data: dict):
        story = []

        # Mauzo section
        story.append(Paragraph("Mauzo", self.styles["SectionTitle"]))
        mauzo = data.get("mauzo", {})
        stats = [
            ["Mauzo Yote", _fmt_tzs(mauzo.get("mauzo", 0))],
            ["COGS", _fmt_tzs(mauzo.get("cogs", 0))],
            ["Faida Ghafi", _fmt_tzs(mauzo.get("faida", 0))],
            ["Orders", _fmt_num(mauzo.get("orders", 0))],
        ]
        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

        # Gharama section
        story.append(Paragraph("Gharama", self.styles["SectionTitle"]))
        gharama = data.get("gharama", {})
        stats = [
            ["Opex", _fmt_tzs(gharama.get("opex", 0))],
            ["Mishahara", _fmt_tzs(gharama.get("mishahara", 0))],
            ["Gharama Zote", _fmt_tzs(gharama.get("gharama_jumla", 0))],
        ]
        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

        # Faida
        story.append(Paragraph("Faida", self.styles["SectionTitle"]))
        faida_safi = data.get("faida_safi", 0)
        stats = [
            ["Faida Safi", _fmt_tzs(faida_safi)],
            ["Zaka (10%)", _fmt_tzs(data.get("zaka", 0))],
            ["Sadaka (10%)", _fmt_tzs(data.get("sadaka", 0))],
            ["Inayobaki", _fmt_tzs(data.get("inayobaki", 0))],
        ]
        t = Table(stats, colWidths=[90 * mm, 75 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (1, 0), (1, 0), EMERALD if faida_safi > 0 else RED),
            ("TEXTCOLOR", (1, 3), (1, 3), EMERALD),
        ]))
        story.append(t)

        return story


# ==================================================================
# Convenience function
# ==================================================================
def generate_pdf(
    aina: str,
    jina: str,
    store_name: str,
    kipindi: str,
    aliyezalisha: str,
    data: dict,
) -> bytes:
    """Generate PDF na rudisha bytes."""
    builder = PDFBuilder()
    return builder.build(
        aina=aina,
        jina=jina,
        store_name=store_name,
        kipindi=kipindi,
        aliyezalisha=aliyezalisha,
        data=data,
    )