from rapidfuzz import fuzz

def matching_agent(state):
    invoice = state.get("invoice")
    po_db = state["po_db"]

    # If invoice extraction failed badly
    if not invoice or not invoice.get("items"):
        state["matched_po"] = None
        state["match_confidence"] = 0.0
        state["reasoning"].append(
            "[MatchingAgent] Invoice has no line items. Cannot perform PO matching."
        )

        return state

    # 1️⃣ Try PO number direct match
    if invoice.get("po_number"):
        for po in po_db["purchase_orders"]:
            if po["po_number"] == invoice["po_number"]:
                state["matched_po"] = po
                state["match_confidence"] = 0.99
                state["reasoning"].append(
                    f"[MatchingAgent] Exact PO number match found: {po['po_number']} (confidence=0.99)"
                )
                return state

    # 2️⃣ Fuzzy match on items
    best_score = 0
    best_po = None

    for po in po_db["purchase_orders"]:
        score = 0
        for inv in invoice["items"]:
            for po_item in po["line_items"]:
                score += fuzz.partial_ratio(
                    inv["description"],
                    po_item["description"]
                )

        if score > best_score:
            best_score = score
            best_po = po

    state["matched_po"] = best_po
    state["match_confidence"] = min(1.0, best_score / 300)
    state["reasoning"].append(
        f"[MatchingAgent] No direct PO match. Best fuzzy match = {best_po['po_number']} "
        f"with score={best_score}, confidence={state['match_confidence']:.2f}"
    )

    return state
