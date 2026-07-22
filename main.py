from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
from dateutil import parser

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Invoice(BaseModel):
    invoice_text: str

@app.get("/")
def home():
    return {"message":"Invoice Extractor API"}

@app.post("/extract")
def extract(data: Invoice):

    text = data.invoice_text

    invoice_no = None
    vendor = None
    date = None
    amount = None
    tax = None
    currency = None

    m = re.search(r'Invoice\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-\/]+)', text, re.I)
    if m:
        invoice_no = m.group(1)

    m = re.search(r'Date[: ]+([^\n]+)', text, re.I)
    if m:
        try:
            date = parser.parse(m.group(1)).strftime("%Y-%m-%d")
        except:
            pass

    m = re.search(r'Vendor[: ]+([^\n]+)', text, re.I)
    if m:
        vendor = m.group(1).strip()

    m = re.search(r'Subtotal[: ]*Rs\.?\s*([\d,]+\.\d+)', text, re.I)
    if m:
        amount = float(m.group(1).replace(",",""))

    m = re.search(r'GST.*?([\d,]+\.\d+)', text, re.I)
    if m:
        tax = float(m.group(1).replace(",",""))

    if "INR" in text.upper() or "RS" in text.upper():
        currency="INR"

    return {
        "invoice_no":invoice_no,
        "date":date,
        "vendor":vendor,
        "amount":amount,
        "tax":tax,
        "currency":currency
    }
