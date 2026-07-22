from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI(title="Invoice Extractor API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceInput(BaseModel):
    invoice_text: str


@app.get("/")
def root():
    return {"status": "running", "message": "Invoice Extractor API"}


def extract_number(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except:
                pass
    return None


@app.post("/extract")
def extract(data: InvoiceInput):

    text = data.invoice_text

    result = {
        "invoice_no": None,
        "date": None,
        "vendor": None,
        "amount": None,
        "tax": None,
        "currency": None,
    }

    # Invoice Number
    invoice_patterns = [
        r"Invoice\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"INV[- ]?\d[\w\-]*",
    ]

    for p in invoice_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            if len(m.groups()) > 0:
                result["invoice_no"] = m.group(1)
            else:
                result["invoice_no"] = m.group(0)
            break

    # Vendor
    vendor_patterns = [
        r"Vendor[: ]+([^\n]+)",
        r"Supplier[: ]+([^\n]+)",
        r"From[: ]+([^\n]+)",
    ]

    for p in vendor_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            result["vendor"] = m.group(1).strip()
            break

    # Date
    date_patterns = [
        r"Date[: ]+([^\n]+)",
        r"Invoice Date[: ]+([^\n]+)",
    ]

    for p in date_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                result["date"] = parser.parse(m.group(1)).strftime("%Y-%m-%d")
            except:
                pass
            break

    # Amount (subtotal before tax)
    result["amount"] = extract_number(
        [
            r"Subtotal[: ]*Rs\.?\s*([\d,]+\.\d+)",
            r"Subtotal[: ]*\$?\s*([\d,]+\.\d+)",
            r"Subtotal[: ]*([\d,]+\.\d+)",
        ],
        text,
    )

    # Tax
    result["tax"] = extract_number(
        [
            r"GST.*?([\d,]+\.\d+)",
            r"Tax[: ]*([\d,]+\.\d+)",
            r"VAT[: ]*([\d,]+\.\d+)",
        ],
        text,
    )

    # Currency
    if "INR" in text.upper() or "RS." in text.upper() or "RS " in text.upper():
        result["currency"] = "INR"
    elif "USD" in text.upper() or "$" in text:
        result["currency"] = "USD"
    elif "EUR" in text.upper() or "€" in text:
        result["currency"] = "EUR"

    return result
