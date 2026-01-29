def human_review_agent(state):
    issues = state.get("issues", [])
    match_conf = state.get("match_confidence", 0)

    feedback = {
        "human_reviewed": True,
        "human_decision": None,
        "notes": ""
    }

    # Case 1: PO matching confidence too low
    if match_conf < 0.6:
        feedback["human_decision"] = "ESCALATE_TO_HUMAN"
        feedback["notes"] = "PO could not be confidently identified. Manual review required."
        state["decision"] = "ESCALATE_TO_HUMAN"
        state["reasoning"].append(
            f"[HumanReviewAgent] Human confirms escalation due to low PO match confidence ({match_conf:.2f})."
        )

    # Case 2: Price mismatch is always critical
    elif any(issue["type"] == "PRICE_MISMATCH" for issue in issues):
        feedback["human_decision"] = "ESCALATE_TO_HUMAN"
        feedback["notes"] = "Price mismatch confirmed by human reviewer."
        state["decision"] = "ESCALATE_TO_HUMAN"
        state["reasoning"].append(
            "[HumanReviewAgent] Human reviewer confirms escalation due to price mismatch."
        )

    # Case 3: Only minor issues
    elif len(issues) > 0:
        feedback["human_decision"] = "REQUEST_CLARIFICATION"
        feedback["notes"] = "Minor issues found. Vendor clarification required."
        state["decision"] = "REQUEST_CLARIFICATION"
        state["reasoning"].append(
            "[HumanReviewAgent] Human reviewer suggests requesting clarification for minor issues."
        )

    # Case 4: Everything looks good
    else:
        feedback["human_decision"] = "AUTO_APPROVE"
        feedback["notes"] = "Looks good. Approved by human reviewer."
        state["decision"] = "AUTO_APPROVE"
        state["reasoning"].append(
            "[HumanReviewAgent] Human reviewer approves invoice."
        )

    state["human_feedback"] = feedback
    return state
