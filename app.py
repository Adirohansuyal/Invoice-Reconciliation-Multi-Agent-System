import streamlit as st
import os
import json
import tempfile
from graph import build_graph
from llm import call_llm
from pdf2image import convert_from_path

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Invoice Reconciliation AI",
    page_icon="📄",
    layout="wide"
)

st.markdown("## 📄 Multi-Agent Invoice Reconciliation System")
st.caption(
    "Real-time agent orchestration • Explainable decisions • Human-in-the-loop review"
)

st.markdown("---")

# --------------------------------------------------
# Load PO DB
# --------------------------------------------------
with open("purchase_orders.json") as f:
    po_db = json.load(f)

agent_app = build_graph()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.markdown("## ⚙️ Controls")

uploaded_files = st.sidebar.file_uploader(
    "Upload invoice PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Decision Legend")
st.sidebar.success("✅ AUTO_APPROVE")
st.sidebar.warning("⚠️ REQUEST_CLARIFICATION")
st.sidebar.error("🚨 ESCALATE_TO_HUMAN")

# --------------------------------------------------
# UI Helpers
# --------------------------------------------------
def render_message(msg: str):
    if msg.startswith("[DocumentAgent]"):
        color = "#1E88E5"
    elif msg.startswith("[MatchingAgent]"):
        color = "#F9A825"
    elif msg.startswith("[DiscrepancyAgent]"):
        color = "#E53935"
    elif msg.startswith("[ResolutionAgent]"):
        color = "#43A047"
    elif msg.startswith("[HumanReviewAgent]"):
        color = "#8E24AA"
    else:
        color = "#607D8B"

    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {color};
            padding: 8px 12px;
            margin-bottom: 6px;
            background-color: rgba(255,255,255,0.03);
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
        ">
            {msg}
        </div>
        """,
        unsafe_allow_html=True
    )


def show_pdf(path):
    try:
        images = convert_from_path(path, dpi=180, first_page=1, last_page=1)
        if images:
            st.image(
                images[0],
                use_container_width=True,
                caption="Invoice preview (page 1)"
            )
        else:
            st.warning("Unable to render PDF preview.")
    except Exception as e:
        st.error(f"PDF preview failed: {e}")


def llm_explain(final_state):
    prompt = f"""
You are an AI accounting assistant.

Invoice decision: {final_state.get("decision")}
Issues: {final_state.get("issues")}
Reasoning trace: {final_state.get("reasoning")}

Explain in 3–5 concise lines why this invoice requires human review.
"""
    return call_llm(prompt)


def save_output_json(file_name, final_state, human_explanation=None):
    os.makedirs("outputs", exist_ok=True)
    payload = {
        "file_name": file_name,
        "decision": final_state.get("decision"),
        "invoice": final_state.get("invoice"),
        "matched_po": final_state.get("matched_po"),
        "match_confidence": final_state.get("match_confidence"),
        "issues": final_state.get("issues"),
        "reasoning": final_state.get("reasoning"),
        "human_explanation": human_explanation
    }
    base = os.path.splitext(file_name)[0]
    path = os.path.join("outputs", f"{base}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path

# --------------------------------------------------
# Main Flow
# --------------------------------------------------
if uploaded_files:

    st.markdown("### 📤 Uploaded Invoices")
    for f in uploaded_files:
        st.markdown(f"- **{f.name}**")

    if st.button("🚀 Process Invoices", use_container_width=True):

        auto_approved, needs_human = [], []

        for uploaded_file in uploaded_files:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            status = st.status(
                f"Processing **{uploaded_file.name}**",
                expanded=False
            )

            state = {
                "file_path": tmp_path,
                "po_db": po_db,
                "reasoning": []
            }

            final_state = None
            for event in agent_app.stream(state):
                if isinstance(event, dict):
                    final_state = list(event.values())[0]

            status.update(label="Processing complete", state="complete")

            record = {
                "file_name": uploaded_file.name,
                "file_path": tmp_path,
                "final_state": final_state
            }

            decision = final_state.get("decision")

            if decision == "AUTO_APPROVE":
                record["output_path"] = save_output_json(
                    uploaded_file.name, final_state
                )
                auto_approved.append(record)
            else:
                explanation = llm_explain(final_state)
                record["human_explanation"] = explanation
                record["output_path"] = save_output_json(
                    uploaded_file.name, final_state, explanation
                )
                needs_human.append(record)

        # --------------------------------------------------
        # Results Tabs
        # --------------------------------------------------
        tab1, tab2 = st.tabs([
            f"✅ Auto Approved ({len(auto_approved)})",
            f"🧑‍⚖️ Needs Human Review ({len(needs_human)})"
        ])

        with tab1:
            if not auto_approved:
                st.success("No invoices were auto-approved.")
            for rec in auto_approved:
                st.markdown("---")
                st.markdown(f"### 📄 {rec['file_name']}")
                left, right = st.columns([1, 1])
                with left:
                    show_pdf(rec["file_path"])
                with right:
                    st.markdown("#### 🧠 Agent Reasoning")
                    with st.container(height=280):
                        for msg in rec["final_state"]["reasoning"]:
                            render_message(msg)
                    st.caption(f"💾 Output saved to `{rec['output_path']}`")

        with tab2:
            if not needs_human:
                st.success("No invoices require human review.")
            for rec in needs_human:
                st.markdown("---")
                st.markdown(f"### 📄 {rec['file_name']}")
                left, right = st.columns([1, 1])
                with left:
                    show_pdf(rec["file_path"])
                with right:
                    st.markdown("#### 🧠 Agent Reasoning")
                    with st.container(height=220):
                        for msg in rec["final_state"]["reasoning"]:
                            render_message(msg)
                    st.markdown("#### 🤖 AI Explanation")
                    st.info(rec["human_explanation"])
                    st.markdown("#### ⚠️ Issues")
                    for issue in rec["final_state"].get("issues", []):
                        st.json(issue)
                    st.caption(f"💾 Output saved to `{rec['output_path']}`")

else:
    st.info("👈 Upload one or more invoice PDFs from the sidebar to begin.")
