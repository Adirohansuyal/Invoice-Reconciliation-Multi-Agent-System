def resolution_agent(state):
    invoice = state.get("invoice", {})
    issues = state.get("issues", [])
    match_conf = state.get("match_confidence", 0)

    po_number = invoice.get("po_number")

    # Rule 1: Missing or invalid PO number
    if not po_number or str(po_number).strip().lower() in ["n/a", "na", "none", "null", ""]:
        issues.append({
            "type": "MISSING_PO",
            "po_value": po_number,
            "confidence": 0.95,
            "severity": "CRITICAL"
        })

        state["issues"] = issues
        state["decision"] = "ESCALATE_TO_HUMAN"

        state["reasoning"].append(
            f"[ResolutionAgent] Invoice PO is missing or invalid ('{po_number}'). Escalating."
        )
        return state

    # Rule 2: Low match confidence
    if match_conf < 0.6:
        issues.append({
            "type": "LOW_MATCH_CONFIDENCE",
            "confidence": match_conf,
            "severity": "HIGH"
        })

        state["issues"] = issues
        state["decision"] = "ESCALATE_TO_HUMAN"

        state["reasoning"].append(
            f"[ResolutionAgent] PO match confidence too low ({match_conf:.2f}). Escalating."
        )
        return state

    # Rule 3: Any price mismatch is critical
    for issue in issues:
        if issue["type"] == "PRICE_MISMATCH":
            state["decision"] = "ESCALATE_TO_HUMAN"
            state["reasoning"].append(
                "[ResolutionAgent] Critical issue detected (PRICE_MISMATCH). Escalating to human."
            )
            return state

    # Rule 4: No issues at all
    if len(issues) == 0:
        state["decision"] = "AUTO_APPROVE"
        state["reasoning"].append(
            "[ResolutionAgent] No issues and high confidence. Auto-approving invoice."
        )
        return state

    # Rule 5: Only minor issues
    state["decision"] = "REQUEST_CLARIFICATION"
    state["reasoning"].append(
        f"[ResolutionAgent] Only non-critical issues detected ({[i['type'] for i in issues]}). "
        "Requesting vendor clarification."
    )
    return state
