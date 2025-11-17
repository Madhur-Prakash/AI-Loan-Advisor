import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import string
from dotenv import load_dotenv
import logging
import io
import uuid
from appwrite.input_file import InputFile
from appwrite.services.storage import Storage
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from services.app_write_service import client
from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

load_dotenv()
BUCKET_ID = os.getenv("BUCKET_ID")
logging.basicConfig(level=logging.INFO)

# create appwrite storage service
storage = Storage(client)

class PDFAgent(BaseAgent):
    def __init__(self):
        super().__init__("PDF Agent")
        os.makedirs("sanction_letters", exist_ok=True)
        # Try to register a Unicode font that includes the rupee symbol (₹)
        self.font_name = "Helvetica"
        self.currency_symbol = "INR "  # Fallback if rupee glyph not available
        # Separate font for the currency symbol to allow mixed-font rendering
        self.symbol_font_name: str | None = None
        self._setup_fonts()
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        # Require name before generating the sanction letter
        if not application.customer.name:
            return AgentResponse(
                agent_name=self.name,
                message=(
                    "Before generating your sanction letter, please provide your full name. "
                    "You can reply: 'My name is <Your Name>'"
                ),
                action_required="collect_name"
            )

        pdf_path = self._generate_sanction_letter(application)
        
        return AgentResponse(
            agent_name=self.name,
            message=f"🎉 Your loan has been approved! Your SYNFIN sanction letter has been generated.\n"
                   f"Document: {pdf_path}\n\n"
                   f"Thank you for choosing SYNFIN. Have a great day!",
            data_updates={
                "status": LoanStatus.COMPLETED.value,
                "sanction_letter_path": pdf_path
            }
        )
    
    def _generate_sanction_letter(self, application: LoanApplication) -> str:
        filename = f"sanction_letters/sanction_letter_{application.application_id}.pdf"
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        def fmt_int(v: float | None) -> str:
            try:
                return f"{int(v)}" if v is not None else "-"
            except Exception:
                return "-"

        margin = 50
        y = height - margin

        # Branding Header
        c.setFillColor(colors.HexColor('#0B5ED7'))
        c.rect(0, y - 30, width, 30, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y - 20, "SYNFIN")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - margin, y - 20, "support@synfin.com | +91-00000-00000")

        y -= 50
        c.setFillColor(colors.black)
        c.setFont(self.font_name, 20)
        c.drawString(margin, y, "Loan Sanction Letter")

        # Meta line
        y -= 18
        c.setFont(self.font_name, 11)
        issued_on = datetime.now()
        valid_until = issued_on + timedelta(days=30)
        sanction_no = f"SAN-{application.application_id}"
        c.drawString(margin, y, f"Sanction No: {sanction_no}")
        c.drawRightString(width - margin, y, f"Date: {issued_on.strftime('%d %b %Y')}")

        # Recipient block
        y -= 28
        c.setLineWidth(0.5)
        c.line(margin, y, width - margin, y)
        y -= 18
        c.setFont(self.font_name, 12)
        c.drawString(margin, y, "Recipient")
        y -= 16
        c.setFont(self.font_name, 11)
        cust = application.customer
        c.drawString(margin + 20, y, f"Name: {self._format_name(cust.name)}")
        y -= 14
        c.drawString(margin + 20, y, f"Customer ID: {cust.customer_id}")
        y -= 14
        c.drawString(margin + 20, y, f"PAN: {cust.pan or '-'}")
        y -= 14
        c.drawString(margin + 20, y, f"Aadhar: {cust.aadhar or '-'}")
        y -= 14
        c.drawString(margin + 20, y, f"Credit Score: {cust.credit_score if cust.credit_score is not None else '-'}")

        # Loan summary box
        y -= 22
        box_top = y
        box_height = 150
        c.setLineWidth(1)
        c.roundRect(margin, box_top - box_height, width - 2*margin, box_height, 8, stroke=True, fill=False)
        c.setFont(self.font_name, 12)
        c.drawString(margin + 10, box_top - 18, "Loan Summary")
        c.setFont(self.font_name, 10)
        left_x = margin + 20
        right_x = width/2 + 10
        row_y = box_top - 36
        # Place long Application ID on its own line to avoid overlap
        c.drawString(left_x, row_y, f"Application ID: {application.application_id}")
        row_y -= 16
        c.drawString(left_x, row_y, f"Validity: until {valid_until.strftime('%d %b %Y')}")
        row_y -= 16
        self._draw_label_and_amount(c, left_x, row_y, "Loan Amount", application.loan_amount)
        c.drawString(right_x, row_y, f"Interest Rate: {application.interest_rate if application.interest_rate is not None else '-'}% p.a.")
        row_y -= 16
        c.drawString(left_x, row_y, f"Tenure: {fmt_int(application.tenure_months)} months")
        self._draw_label_and_amount(c, right_x, row_y, "EMI", application.emi)
        row_y -= 16
        total_payable = (application.emi or 0) * (application.tenure_months or 0)
        self._draw_label_and_amount(c, left_x, row_y, "Total Payable", total_payable)
        self._draw_label_and_amount(c, right_x, row_y, "Pre-approved Limit", application.pre_approved_limit)

        # Notes / Conditions
        y = box_top - box_height - 20
        c.setFont(self.font_name, 12)
        c.drawString(margin, y, "Key Conditions")
        y -= 14
        c.setFont(self.font_name, 10)
        bullets = [
            f"Sanction valid until {valid_until.strftime('%d %b %Y')}.",
            "Processing fee: 2% of loan amount (minimum ₹1,000).",
            "First EMI due date: 30 days from disbursement.",
            "Prepayment allowed after 6 months with 2% charges.",
            "Subject to verification of submitted documents and compliance with KYC norms."
        ]
        for b in bullets:
            c.drawString(margin + 20, y, f"• {b}")
            y -= 13

        # Signatory block
        y -= 8
        c.setLineWidth(0.5)
        c.line(margin, y, width - margin, y)
        y -= 26
        c.setFont(self.font_name, 12)
        c.drawString(margin, y, "Authorized Signatory")
        y -= 16
        c.setFont(self.font_name, 10)
        c.drawString(margin + 20, y, "SYNFIN")
        y -= 12
        c.drawString(margin + 20, y, "Head Office: 123 Finance Street, Mumbai, MH 400001")

        # Footer
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 40, "This is a system-generated document and does not require a physical signature.")

        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # uploading to Appwrite Storage
        appwrite_file = storage.create_file(
            BUCKET_ID,
            str(uuid.uuid4()),
            InputFile.from_bytes(pdf_bytes, filename, "application/pdf")
        )

        logging.info(f"✅File uploaded on Appwrite: {appwrite_file}")

        return {"filename": filename, "appwrite_file": appwrite_file}

    def _draw_label_and_amount(self, c: canvas.Canvas, x: float, y_pos: float, label: str, amount_value: float | None):
        """Draw label and amount using a dedicated symbol font for the rupee sign when available."""
        c.setFont(self.font_name, 10)
        label_text = f"{label}: "
        c.drawString(x, y_pos, label_text)
        # Compute offset for amount rendering
        offset = pdfmetrics.stringWidth(label_text, self.font_name, 10)
        # Render currency symbol with symbol font when available
        amt_num = "-" if amount_value is None else f"{float(amount_value):,.2f}"
        if self.symbol_font_name and self.currency_symbol == "₹":
            c.setFont(self.symbol_font_name, 10)
            c.drawString(x + offset, y_pos, "₹")
            sym_w = pdfmetrics.stringWidth("₹", self.symbol_font_name, 10)
            c.setFont(self.font_name, 10)
            c.drawString(x + offset + sym_w, y_pos, amt_num)
        else:
            # Fallback prints with INR prefix using body font
            c.setFont(self.font_name, 10)
            c.drawString(x + offset, y_pos, f"{self.currency_symbol}{amt_num}")

    def _setup_fonts(self):
        """Register a Unicode-capable font to ensure the rupee symbol renders.
        Falls back to Helvetica if not found, using 'INR ' instead of '₹'.
        """
        candidates: list[tuple[str, str]] = []
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # Prefer macOS Supplemental fonts that reliably include the rupee glyph
        candidates.extend([
            ("NotoSans", "/System/Library/Fonts/Supplemental/NotoSans-Regular.ttf"),
            ("DejaVuSans", "/System/Library/Fonts/Supplemental/DejaVuSans.ttf"),
            ("AppleSymbols", "/System/Library/Fonts/Supplemental/Apple Symbols.ttf"),
        ])
        # Project-local fonts (if user adds them)
        candidates.extend([
            ("DejaVuSans", os.path.join(base_dir, "assets", "fonts", "DejaVuSans.ttf")),
            ("NotoSans", os.path.join(base_dir, "assets", "fonts", "NotoSans-Regular.ttf")),
            ("NotoSans", os.path.join(base_dir, "fonts", "NotoSans-Regular.ttf")),
            ("DejaVuSans", os.path.join(base_dir, "fonts", "DejaVuSans.ttf")),
        ])
        # Common user-installed locations
        candidates.extend([
            ("NotoSans", "/Library/Fonts/NotoSans-Regular.ttf"),
            ("DejaVuSans", "/Library/Fonts/DejaVuSans.ttf"),
            ("ArialUnicodeMS", "/Library/Fonts/Arial Unicode.ttf"),
        ])

        for name, path in candidates:
            try:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont(name, path))
                    # Use the first full text font we find for body text
                    if name != "AppleSymbols" and self.font_name == "Helvetica":
                        self.font_name = name
                    # Use any font that contains the rupee glyph for the symbol
                    if name == "AppleSymbols" or name in ("NotoSans", "DejaVuSans", "ArialUnicodeMS"):
                        self.symbol_font_name = name
                        self.currency_symbol = "₹"
                    # Also attempt to register a bold variant if present to avoid fallback boxes
                    bold_candidates = [
                        (f"{name}-Bold", path.replace("Regular", "Bold")),
                        (f"{name}-Bold", path.replace("Sans.ttf", "Sans-Bold.ttf")),
                        (f"{name}-Bold", path.replace(".ttf", "-Bold.ttf")),
                    ]
                    for bold_name, bold_path in bold_candidates:
                        try:
                            if bold_path != path and os.path.exists(bold_path):
                                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                        except Exception:
                            pass
                    # Continue scanning to pick up both body and symbol fonts if needed
            except Exception:
                continue
        # Fallback already set: Helvetica + 'INR '
        # Helper moved to instance method to avoid local scope issues

    def _format_name(self, name: str | None) -> str:
        """Capitalize each word in the recipient's name. Returns '-' if missing."""
        try:
            n = (name or "").strip()
            if not n:
                return "-"
            # Title-case each word; keeps spacing clean
            return string.capwords(n)
        except Exception:
            return name or "-"