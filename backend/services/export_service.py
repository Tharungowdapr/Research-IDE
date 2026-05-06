"""
Document Export Utilities — DOCX and PDF generation for IEEE-format papers.
"""

import io
import re
from typing import Dict, List
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


def generate_docx(report: Dict) -> bytes:
    """Generate IEEE-format DOCX from report dict."""
    doc = Document()

    # --- Page Setup (A4) ---
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.9)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(1.9)
    section.right_margin = Cm(1.9)

    # --- Title ---
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.space_before = Pt(0)
    title_para.space_after = Pt(12)
    title_run = title_para.add_run(report.get("title", "Research Paper"))
    title_run.bold = True
    title_run.font.size = Pt(24)
    title_run.font.name = "Times New Roman"

    # --- Authors ---
    authors = report.get("authors", ["Author"])
    authors_para = doc.add_paragraph()
    authors_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors_para.space_before = Pt(0)
    authors_para.space_after = Pt(12)
    auth_run = authors_para.add_run(", ".join(authors))
    auth_run.italic = True
    auth_run.font.size = Pt(11)
    auth_run.font.name = "Times New Roman"

    # --- Abstract ---
    abs_label = doc.add_paragraph()
    abs_label.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abs_label.space_before = Pt(0)
    abs_label.space_after = Pt(6)
    label_run = abs_label.add_run("Abstract—")
    label_run.italic = True
    label_run.font.size = Pt(9)
    label_run.font.name = "Times New Roman"
    abs_run = abs_label.add_run(report.get("abstract", ""))
    abs_run.font.size = Pt(9)
    abs_run.font.name = "Times New Roman"

    # --- Keywords ---
    kw_para = doc.add_paragraph()
    kw_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    kw_para.space_before = Pt(0)
    kw_para.space_after = Pt(12)
    kw_label = kw_para.add_run("Index Terms—")
    kw_label.italic = True
    kw_label.font.size = Pt(9)
    kw_label.font.name = "Times New Roman"
    kw_text = kw_para.add_run(", ".join(report.get("keywords", [])))
    kw_text.font.size = Pt(9)
    kw_text.font.name = "Times New Roman"

    # --- Switch to two-column section ---
    new_section = doc.add_section(WD_SECTION.CONTINUOUS)
    new_section.page_width = Cm(21)
    new_section.page_height = Cm(29.7)
    new_section.top_margin = Cm(1.9)
    new_section.bottom_margin = Cm(2.54)
    new_section.left_margin = Cm(1.9)
    new_section.right_margin = Cm(1.9)
    # Set two columns via XML
    sect_pr = new_section._sectPr
    cols_xml = f'<w:cols {nsdecls("w")} w:num="2" w:space="720"/>'
    sect_pr.append(parse_xml(cols_xml))

    # --- Body Sections ---
    for sec in report.get("sections", []):
        heading = sec.get("heading", "")
        content = sec.get("content", "")

        # Section heading
        h_para = doc.add_paragraph()
        h_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h_para.space_before = Pt(12)
        h_para.space_after = Pt(6)
        h_run = h_para.add_run(heading.upper())
        h_run.bold = True
        h_run.font.size = Pt(10)
        h_run.font.name = "Times New Roman"

        # Section content — split by double newline into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for para_text in paragraphs:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.space_before = Pt(0)
            p.space_after = Pt(6)
            run = p.add_run(para_text)
            run.font.size = Pt(10)
            run.font.name = "Times New Roman"

    # --- Acknowledgements ---
    ack = report.get("acknowledgements", "")
    if ack:
        ack_h = doc.add_paragraph()
        ack_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ack_h.space_before = Pt(12)
        ack_h.space_after = Pt(6)
        ack_hr = ack_h.add_run("ACKNOWLEDGEMENTS")
        ack_hr.bold = True
        ack_hr.font.size = Pt(10)
        ack_hr.font.name = "Times New Roman"
        ack_p = doc.add_paragraph()
        ack_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ack_p.space_after = Pt(6)
        ack_r = ack_p.add_run(ack)
        ack_r.font.size = Pt(9)
        ack_r.font.name = "Times New Roman"

    # --- References ---
    refs = report.get("references", [])
    if refs:
        ref_h = doc.add_paragraph()
        ref_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ref_h.space_before = Pt(12)
        ref_h.space_after = Pt(6)
        ref_hr = ref_h.add_run("REFERENCES")
        ref_hr.bold = True
        ref_hr.font.size = Pt(10)
        ref_hr.font.name = "Times New Roman"

        for ref in refs:
            ref_p = doc.add_paragraph()
            ref_p.space_before = Pt(0)
            ref_p.space_after = Pt(3)
            if isinstance(ref, dict):
                ref_id = ref.get("id", "")
                authors_str = ref.get("authors", "Unknown")
                title_str = ref.get("title", "")
                venue = ref.get("venue", "")
                year = ref.get("year", "")
                ref_text = f"[{ref_id}] {authors_str}, \"{title_str},\" {venue}, {year}."
            else:
                ref_text = str(ref)
            run = ref_p.add_run(ref_text)
            run.font.size = Pt(8)
            run.font.name = "Times New Roman"

    # Save to bytes
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def generate_pdf_html(report: Dict) -> str:
    """Generate IEEE-format HTML string for PDF conversion."""
    title = _esc(report.get("title", "Research Paper"))
    authors = ", ".join(_esc(a) for a in report.get("authors", ["Author"]))
    abstract = _esc(report.get("abstract", ""))
    keywords = ", ".join(_esc(k) for k in report.get("keywords", []))
    ack = _esc(report.get("acknowledgements", ""))

    sections_html = ""
    for sec in report.get("sections", []):
        heading = _esc(sec.get("heading", ""))
        content = sec.get("content", "")
        paras = [p.strip() for p in content.split("\n\n") if p.strip()]
        paras_html = "".join(f"<p>{_esc(p)}</p>" for p in paras)
        sections_html += f"<h2>{heading}</h2>{paras_html}"

    refs_html = ""
    for ref in report.get("references", []):
        if isinstance(ref, dict):
            rid = ref.get("id", "")
            ref_str = (f'[{rid}] {_esc(ref.get("authors", ""))},'
                       f' "{_esc(ref.get("title", ""))},"'
                       f' {_esc(ref.get("venue", ""))},'
                       f' {_esc(ref.get("year", ""))}.')
        else:
            ref_str = _esc(str(ref))
        refs_html += f"<div class='ref'>{ref_str}</div>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 1.9cm 1.9cm 2.54cm 1.9cm; }}
body {{ font-family: 'Times New Roman', Times, serif; font-size: 10pt; line-height: 1.3; margin: 0; padding: 0; }}
#header {{ text-align: center; margin-bottom: 12pt; }}
#header h1 {{ font-size: 24pt; margin: 0 0 6pt; }}
#header .authors {{ font-size: 11pt; font-style: italic; }}
#abstract {{ font-size: 9pt; margin-bottom: 12pt; text-align: justify; }}
#abstract .label {{ font-style: italic; }}
#keywords {{ font-size: 9pt; margin-bottom: 12pt; }}
#keywords .label {{ font-style: italic; }}
#body-content {{ column-count: 2; column-gap: 24pt; }}
#body-content h2 {{ font-size: 10pt; font-weight: bold; text-align: center; text-transform: uppercase;
    column-span: none; margin: 12pt 0 6pt; break-after: avoid; }}
#body-content p {{ text-align: justify; margin: 0 0 6pt; break-inside: avoid; }}
.refs {{ font-size: 8pt; }}
.ref {{ margin-bottom: 3pt; }}
</style></head><body>
<div id="header"><h1>{title}</h1><div class="authors">{authors}</div></div>
<div id="abstract"><span class="label">Abstract— </span>{abstract}</div>
<div id="keywords"><span class="label">Index Terms— </span>{keywords}</div>
<div id="body-content">{sections_html}
{f'<h2>ACKNOWLEDGEMENTS</h2><p>{ack}</p>' if ack else ''}
<h2>REFERENCES</h2><div class="refs">{refs_html}</div>
</div></body></html>"""


def _esc(text: str) -> str:
    """Escape HTML entities."""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
