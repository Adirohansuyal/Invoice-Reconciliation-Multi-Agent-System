import json
import re
from ocr_utils import extract_text
from llm import call_llm

def safe_json_parse(text):
    """
    Tries very hard to extract JSON from LLM output.
    """
    try:
        return json.loads(text)
    except:
        # Try to extract JSON block using regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    return None


def document_agent(state):
    raw_text = extract_text(state["file_path"])

    prompt = f"""
You are a strict JSON generator.

Extract structured JSON from this invoice.

Rules:
- Output ONLY JSON
- No explanation
- No markdown
- No ```json
- No text outside JSON

Format:

{{
  "invoice_no": "",
  "supplier": "",
  "po_number": "",
  "items": [
    {{"description":"","quantity":0,"unit_price":0,"total":0}}
  ],
  "total": 0
}}

Invoice text:
{raw_text}
"""

    result = call_llm(prompt)

    invoice = safe_json_parse(result)

    if invoice is None:
        # HARD FAIL SAFE — system must not crash
        state["invoice"] = {
            "invoice_no": None,
            "supplier": None,
            "po_number": None,
            "items": [],
            "total": 0
        }
        state["confidence_doc"] = 0.1
        state["reasoning"].append(
            "[DocumentAgent] LLM output could not be parsed as JSON. Using empty fallback invoice."
        )

    else:
        state["invoice"] = invoice
        state["confidence_doc"] = 0.9
        state["reasoning"].append(
            f"[DocumentAgent] Extracted invoice. "
            f"InvoiceNo={invoice.get('invoice_no')}, "
            f"PO={invoice.get('po_number')}, "
            f"Items={len(invoice.get('items', []))}"
)


    return state
