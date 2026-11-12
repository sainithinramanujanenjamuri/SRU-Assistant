"""Master script to compile the complete publication-grade DOCX and PDF technical documentation."""

import os
import sys
from pathlib import Path

# Add current folder to sys.path so chapters can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from pypdf import PdfReader

from chapters_part1 import CHAPTERS_PART1
from chapters_part2 import CHAPTERS_PART2

BASE_DIR = Path("d:/Collage/SRU_Assistant_Capstone_Project/SRU_Assistant_Technical_Documentation")
DIAGRAMS_DIR = BASE_DIR / "architecture_diagrams"
DOCX_OUT = BASE_DIR / "SRU_Assistant_Technical_Documentation.docx"
PDF_OUT = BASE_DIR / "SRU_Assistant_Technical_Documentation.pdf"

# ---------------------------------------------------------------------------
# ReportLab Canvas with Running Header & Footer (Page X of Y)
# ---------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on cover page

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(54, letter[1] - 36, "SRU ASSISTANT — TECHNICAL ARCHITECTURE DOCUMENTATION")
        self.setFont("Helvetica", 8)
        self.drawRightString(letter[0] - 54, letter[1] - 36, "School of CS & AI • SR University")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Running Footer
        self.line(54, 45, letter[0] - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — Internal Capstone Technical Documentation")
        self.drawRightString(letter[0] - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

# ---------------------------------------------------------------------------
# DOCX Helper Functions
# ---------------------------------------------------------------------------
def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_docx_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = RGBColor(15, 23, 42)
    return p

def add_docx_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(37, 99, 235)
    return p

def add_docx_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = RGBColor(71, 85, 105)
    return p

def add_docx_p(doc, text, bold_prefix=None, space_after=5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Arial"
        r_pre.font.size = Pt(9.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_docx_callout(doc, text, title="ARCHITECTURAL PRINCIPLE:"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), '2563EB')
    tcBorders.append(left)
    for b in ['top', 'bottom', 'right']:
        node = OxmlElement(f'w:{b}')
        node.set(qn('w:val'), 'none')
        tcBorders.append(node)
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r_t = p.add_run(title + "\n")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(9)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(37, 99, 235)
    r_b = p.add_run(text)
    r_b.font.name = "Arial"
    r_b.font.size = Pt(9)
    r_b.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_docx_image_with_caption(doc, img_path, caption):
    if Path(img_path).exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(5.8))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(8)
        r_cap = p_cap.add_run(caption)
        r_cap.font.name = "Arial"
        r_cap.font.size = Pt(8)
        r_cap.font.italic = True
        r_cap.font.color.rgb = RGBColor(100, 116, 139)

def add_docx_table_data(doc, headers, rows_data):
    tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1E293B")
        set_cell_margins(hdr_cells[i], top=70, bottom=70, left=90, right=90)
        p = hdr_cells[i].paragraphs[0]
        for r in p.runs:
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            
    for r_idx, row_items in enumerate(rows_data):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_items):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=90, right=90)
            p = row_cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.name = "Arial"
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ---------------------------------------------------------------------------
# DOCX Generation Pipeline
# ---------------------------------------------------------------------------
def generate_docx():
    print("Generating DOCX document...")
    doc = docx.Document()
    
    # 0.75-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
    all_chapters = CHAPTERS_PART1 + CHAPTERS_PART2
    
    for ch in all_chapters:
        if ch["id"] != "cover":
            add_docx_heading_1(doc, ch["title"])
            
        for block in ch["blocks"]:
            b_type = block[0]
            if b_type == "cover_meta":
                data = block[1]
                p_c = doc.add_paragraph()
                p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_c.paragraph_format.space_before = Pt(40)
                p_c.paragraph_format.space_after = Pt(12)
                r_title = p_c.add_run(data["title"] + "\n")
                r_title.font.name = "Arial"
                r_title.font.size = Pt(26)
                r_title.font.bold = True
                r_title.font.color.rgb = RGBColor(37, 99, 235)
                
                r_sub = p_c.add_run(data["subtitle"] + "\n\n")
                r_sub.font.name = "Arial"
                r_sub.font.size = Pt(13)
                r_sub.font.color.rgb = RGBColor(15, 23, 42)
                
                r_type = p_c.add_run(data["doc_type"] + "\n")
                r_type.font.name = "Arial"
                r_type.font.size = Pt(10.5)
                r_type.font.bold = True
                r_type.font.color.rgb = RGBColor(71, 85, 105)
                
                doc.add_paragraph().paragraph_format.space_after = Pt(30)
                
                # Meta Table
                tbl_meta = [
                    ["Institutional Context", data["institution"]],
                    ["Department", data["department"]],
                    ["Author / Architect", data["author"]],
                    ["Release Version", data["version"]],
                    ["Publication Date", data["date"]],
                    ["Security Classification", data["classification"]]
                ]
                add_docx_table_data(doc, ["Document Parameter", "Operational Specification"], tbl_meta)
                
            elif b_type == "heading_2":
                add_docx_heading_2(doc, block[1])
            elif b_type == "heading_3":
                add_docx_heading_3(doc, block[1])
            elif b_type == "p":
                add_docx_p(doc, block[1], bold_prefix=block[2] if len(block) > 2 else None)
            elif b_type == "callout":
                add_docx_callout(doc, block[1], title=block[2])
            elif b_type == "table":
                add_docx_table_data(doc, block[1], block[2])
            elif b_type == "diagram":
                img_path = DIAGRAMS_DIR / block[1]
                add_docx_image_with_caption(doc, img_path, block[2])
            elif b_type == "page_break":
                doc.add_page_break()
                
    doc.save(str(DOCX_OUT))
    print(f"DOCX successfully compiled: {DOCX_OUT} ({os.path.getsize(DOCX_OUT)} bytes)")

# ---------------------------------------------------------------------------
# PDF Generation Pipeline (ReportLab)
# ---------------------------------------------------------------------------
def generate_pdf():
    print("Generating PDF document via ReportLab...")
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1e40af"),
        alignment=1, # Center
        spaceAfter=12
    )
    style_cover_sub = ParagraphStyle(
        "CoverSubtitle",
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=16
    )
    style_cover_type = ParagraphStyle(
        "CoverType",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=30
    )
    style_h1 = ParagraphStyle(
        "ReportH1",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        "ReportH2",
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1d4ed8"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    style_h3 = ParagraphStyle(
        "ReportH3",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        "ReportBody",
        fontName="Helvetica",
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )
    style_caption = ParagraphStyle(
        "ReportCaption",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceBefore=3,
        spaceAfter=8
    )
    style_callout_title = ParagraphStyle(
        "ReportCalloutTitle",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1d4ed8"),
        spaceAfter=2
    )
    style_callout_body = ParagraphStyle(
        "ReportCalloutBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    style_th = ParagraphStyle(
        "ReportTH",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    style_td = ParagraphStyle(
        "ReportTD",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b")
    )
    
    story = []
    all_chapters = CHAPTERS_PART1 + CHAPTERS_PART2
    
    for ch in all_chapters:
        if ch["id"] != "cover":
            story.append(Paragraph(ch["title"], style_h1))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=8))
            
        for block in ch["blocks"]:
            b_type = block[0]
            if b_type == "cover_meta":
                data = block[1]
                story.append(Spacer(1, 40))
                story.append(Paragraph(data["title"], style_cover_title))
                story.append(Paragraph(data["subtitle"], style_cover_sub))
                story.append(Paragraph(data["doc_type"], style_cover_type))
                story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#2563eb"), spaceBefore=10, spaceAfter=30))
                
                tbl_meta = [
                    [Paragraph("Document Parameter", style_th), Paragraph("Operational Specification", style_th)],
                    [Paragraph("Institutional Context", style_td), Paragraph(data["institution"], style_td)],
                    [Paragraph("Department", style_td), Paragraph(data["department"], style_td)],
                    [Paragraph("Author / Architect", style_td), Paragraph(data["author"], style_td)],
                    [Paragraph("Release Version", style_td), Paragraph(data["version"], style_td)],
                    [Paragraph("Publication Date", style_td), Paragraph(data["date"], style_td)],
                    [Paragraph("Security Classification", style_td), Paragraph(data["classification"], style_td)]
                ]
                t_m = Table(tbl_meta, colWidths=[2.2 * inch, 4.3 * inch])
                t_m.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                story.append(t_m)
                
            elif b_type == "heading_2":
                story.append(Paragraph(block[1], style_h2))
            elif b_type == "heading_3":
                story.append(Paragraph(block[1], style_h3))
            elif b_type == "p":
                prefix = f"<b>{block[2]}</b> " if len(block) > 2 and block[2] else ""
                story.append(Paragraph(f"{prefix}{block[1]}", style_body))
            elif b_type == "callout":
                c_content = [
                    Paragraph(block[2], style_callout_title),
                    Paragraph(block[1], style_callout_body)
                ]
                t_c = Table([[c_content]], colWidths=[6.5 * inch])
                t_c.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("LINEBEFORE", (0, 0), (0, -1), 3.0, colors.HexColor("#2563eb")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(Spacer(1, 4))
                story.append(t_c)
                story.append(Spacer(1, 6))
            elif b_type == "table":
                headers = [Paragraph(h, style_th) for h in block[1]]
                tbl_rows = [headers]
                for row_data in block[2]:
                    tbl_rows.append([Paragraph(str(val), style_td) for val in row_data])
                    
                col_w = (6.5 / len(block[1])) * inch
                t_data = Table(tbl_rows, colWidths=[col_w] * len(block[1]))
                t_data.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                story.append(Spacer(1, 3))
                story.append(t_data)
                story.append(Spacer(1, 6))
            elif b_type == "diagram":
                img_path = DIAGRAMS_DIR / block[1]
                if img_path.exists():
                    story.append(Spacer(1, 4))
                    story.append(RLImage(str(img_path), width=6.2 * inch, height=3.3 * inch))
                    story.append(Paragraph(block[2], style_caption))
                    story.append(Spacer(1, 6))
            elif b_type == "page_break":
                story.append(PageBreak())
                
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully compiled: {PDF_OUT} ({os.path.getsize(PDF_OUT)} bytes)")

def verify_output_pages():
    reader = PdfReader(str(PDF_OUT))
    print(f"===========================================================")
    print(f"VERIFICATION AUDIT: PDF Total Page Count: {len(reader.pages)} pages")
    print(f"VERIFICATION AUDIT: DOCX Size: {os.path.getsize(DOCX_OUT)} bytes")
    print(f"===========================================================")

def main():
    generate_docx()
    generate_pdf()
    verify_output_pages()

if __name__ == "__main__":
    main()
