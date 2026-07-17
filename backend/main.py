from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import os
import tempfile
import time
from datetime import datetime
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class FIRRequest(BaseModel):
    crimeType: str
    laws: list
    checklist: list
    uploadedFiles: list
    victimName: str = "Complainant"

SYSTEM_PROMPT = """You are CyberAegis, an AI-powered cybercrime first responder assistant for India.
Your job is to help victims who have been scammed, hacked, harassed, or cheated online.
Always:
- Identify the type of cybercrime from what the user describes
- Mention the relevant Indian law section (IT Act 2000/2008 or IPC)
- Give clear step by step instructions on what to do next
- Tell them what evidence to collect and preserve
- Guide them to report at cybercrime.gov.in or call 1930
- Be empathetic, calm, and supportive
- Keep responses clear and easy to understand
- Never ask for personal sensitive information like passwords or OTPs
Respond in English only."""

@app.get("/")
def root():
    return {"status": "CyberAegis backend is running!"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.message}
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Sorry, something went wrong: {str(e)}"}

@app.post("/generate-fir")
async def generate_fir(request: FIRRequest):
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()

        doc = SimpleDocTemplate(
            tmp.name,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        PURPLE = HexColor("#4F6EF7")
        DARK_PURPLE = HexColor("#7C3AED")
        DARK = HexColor("#1A1A2E")
        GRAY = HexColor("#5A6080")
        LIGHT_GRAY = HexColor("#F0F4FF")
        RED = HexColor("#DC2626")
        GREEN = HexColor("#16A34A")

        title_style = ParagraphStyle('title', fontSize=22, textColor=PURPLE,
            fontName='Helvetica-Bold', spaceAfter=4, alignment=1)
        subtitle_style = ParagraphStyle('subtitle', fontSize=11, textColor=GRAY,
            fontName='Helvetica', spaceAfter=2, alignment=1)
        section_style = ParagraphStyle('section', fontSize=13, textColor=PURPLE,
            fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6)
        body_style = ParagraphStyle('body', fontSize=10, textColor=DARK,
            fontName='Helvetica', spaceAfter=4, leading=16)
        label_style = ParagraphStyle('label', fontSize=9, textColor=GRAY,
            fontName='Helvetica-Bold', spaceAfter=2, leading=14)
        check_style = ParagraphStyle('check', fontSize=10, textColor=GREEN,
            fontName='Helvetica', spaceAfter=3, leading=14, leftIndent=10)
        pending_style = ParagraphStyle('pending', fontSize=10, textColor=RED,
            fontName='Helvetica', spaceAfter=3, leading=14, leftIndent=10)

        story = []
        now = datetime.now()

        story.append(Paragraph("CyberAegis", title_style))
        story.append(Paragraph("AI Cybercrime First Responder — India", subtitle_style))
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("FIRST INFORMATION REPORT (FIR) DRAFT",
            ParagraphStyle('firtitle', fontSize=16, textColor=DARK,
            fontName='Helvetica-Bold', alignment=1, spaceAfter=2)))
        story.append(Paragraph(
            "Submit this document to your nearest Police Station or upload on cybercrime.gov.in",
            ParagraphStyle('note', fontSize=9, textColor=GRAY,
            fontName='Helvetica-Oblique', alignment=1, spaceAfter=4)))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#E4E8FF")))
        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("CASE DETAILS", section_style))
        case_data = [
            ["Report Date", now.strftime("%d %B %Y")],
            ["Report Time", now.strftime("%I:%M %p")],
            ["Complainant", request.victimName],
            ["Crime Type", request.crimeType],
            ["Reference No.", f"CYB{now.strftime('%Y%m%d%H%M%S')}"],
        ]
        case_table = Table(case_data, colWidths=[50*mm, 120*mm])
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), LIGHT_GRAY),
            ('TEXTCOLOR', (0,0), (0,-1), PURPLE),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [HexColor("#F8F6FF"), HexColor("#FFFFFF")]),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor("#E4E8FF")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(case_table)
        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("APPLICABLE LAW SECTIONS", section_style))
        for law in request.laws:
            code = law.get('code','') if isinstance(law, dict) else str(law)
            desc = law.get('desc','') if isinstance(law, dict) else ''
            law_data = [[code, desc]]
            law_table = Table(law_data, colWidths=[55*mm, 115*mm])
            law_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0), HexColor("#EEF2FF")),
                ('TEXTCOLOR', (0,0), (0,0), DARK_PURPLE),
                ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
                ('FONTNAME', (1,0), (1,0), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('GRID', (0,0), (-1,-1), 0.5, HexColor("#E4E8FF")),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(law_table)
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 2*mm))

        checked = [i for i in request.checklist if i.get('checked', False)]
        pending = [i for i in request.checklist if not i.get('checked', False)]

        story.append(Paragraph(
            f"EVIDENCE COLLECTED ({len(checked)} of {len(request.checklist)} items)",
            section_style))

        if checked:
            story.append(Paragraph("Collected:", label_style))
            for item in checked:
                text = item.get('text','') if isinstance(item, dict) else str(item)
                story.append(Paragraph(f"✓  {text}", check_style))

        if pending:
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("Still Pending:", label_style))
            for item in pending:
                text = item.get('text','') if isinstance(item, dict) else str(item)
                story.append(Paragraph(f"○  {text}  [PENDING]", pending_style))

        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("EVIDENCE FILES ATTACHED", section_style))
        if request.uploadedFiles:
            for fname in request.uploadedFiles:
                story.append(Paragraph(f"  {fname}", body_style))
        else:
            story.append(Paragraph("No files attached yet.",
                ParagraphStyle('warn', fontSize=10, textColor=RED,
                fontName='Helvetica-Oblique')))
        story.append(Spacer(1, 4*mm))

        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#E4E8FF")))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("RECOMMENDED NEXT STEPS", section_style))
        steps = [
            "1.  Visit cybercrime.gov.in to file your complaint online",
            "2.  Call 1930 — National Cyber Crime Helpline (available 24/7)",
            "3.  Visit your nearest Police Station with this document",
            "4.  Keep all original evidence safe — do NOT delete messages",
            "5.  Follow up with police every 7 days",
        ]
        for step in steps:
            story.append(Paragraph(step, body_style))
        story.append(Spacer(1, 6*mm))

        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "Generated by CyberAegis | cybercrime.gov.in | Helpline: 1930",
            ParagraphStyle('footer', fontSize=8, textColor=GRAY,
            fontName='Helvetica-Oblique', alignment=1)))

        doc.build(story)

        return FileResponse(
            tmp.name,
            media_type="application/pdf",
            filename=f"CyberAegis_FIR_{request.crimeType.replace(' ','_')}_{now.strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        return {"error": str(e)}