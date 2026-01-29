from rapidfuzz import fuzz

def discrepancy_agent(state):
    invoice = state.get("invoice")
    po = state.get("matched_po")

    issues = []

    if not invoice or not invoice.get("items") or not po:
        state["issues"] = [{
            "type": "MISSING_DATA",
            "confidence": 0.9
        }]
        state["reasoning"].append(
            "[DiscrepancyAgent] Missing invoice or PO data. Cannot perform comparison."
        )
        return state

    for inv in invoice["items"]:
        best_match_score = 0
        best_po_item = None

        # Find best matching PO item using fuzzy matching
        for po_item in po["line_items"]:
            score = fuzz.partial_ratio(
                str(inv.get("description", "")).lower(),
                str(po_item.get("description", "")).lower()
            )
            if score > best_match_score:
                best_match_score = score
                best_po_item = po_item

        # If no good match found
        if best_match_score < 70 or best_po_item is None:
            issues.append({
                "type": "ITEM_NOT_IN_PO",
                "item": inv.get("description"),
                "confidence": 0.85
            })
            state["reasoning"].append(
                f"[DiscrepancyAgent] No good PO match for invoice item "
                f"'{inv.get('description')}'. Best fuzzy score={best_match_score}."
            )
            continue

        # Compare unit price
        inv_price = float(inv.get("unit_price", 0))
        po_price = float(best_po_item.get("unit_price", 0))

        state["reasoning"].append(
            f"[DiscrepancyAgent] Comparing prices for '{inv.get('description')}': "
            f"invoice_price={inv_price}, po_price={po_price}"
        )

        if inv_price != po_price:
            issues.append({
                "type": "PRICE_MISMATCH",
                "item": inv.get("description"),
                "invoice_price": inv_price,
                "po_price": po_price,
                "confidence": 0.95
            })
            state["reasoning"].append(
                f"[DiscrepancyAgent] PRICE_MISMATCH detected for "
                f"'{inv.get('description')}'."
            )

        # Compare quantity
        inv_qty = float(inv.get("quantity", 0))
        po_qty = float(best_po_item.get("quantity", 0))

        state["reasoning"].append(
            f"[DiscrepancyAgent] Comparing quantities for '{inv.get('description')}': "
            f"invoice_qty={inv_qty}, po_qty={po_qty}"
        )

        if inv_qty != po_qty:
            issues.append({
                "type": "QTY_MISMATCH",
                "item": inv.get("description"),
                "invoice_qty": inv_qty,
                "po_qty": po_qty,
                "confidence": 0.9
            })
            state["reasoning"].append(
                f"[DiscrepancyAgent] QTY_MISMATCH detected for "
                f"'{inv.get('description')}'."
            )

    # Final summary
    if issues:
        state["reasoning"].append(
            f"[DiscrepancyAgent] Comparison complete. Detected {len(issues)} issues: "
            f"{[i['type'] for i in issues]}"
        )
    else:
        state["reasoning"].append(
            "[DiscrepancyAgent] Comparison complete. No discrepancies found."
        )

    state["issues"] = issues
    return state
