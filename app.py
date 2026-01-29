import streamlit as st
import os
import json
import tempfile
import time
import base64
from graph import build_graph
from llm import call_llm

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Invoice Reconciliation AI",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Multi-Agent Invoice Reconciliation System")
st.caption("Real-time agent orchestration • Explainable decisions • Human-in-the-loop")

# -------------------------------
# Load PO DB
# -------------------------------
with open("purchase_orders.json") as f:
    po_db = json.load(f)

# Build LangGraph app
agent_app = build_graph()

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.header("⚙️ Controls")
uploaded_files = st.sidebar.file_uploader(
    "Upload Invoices (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Decision Legend")
st.sidebar.success("✅ AUTO_APPROVE")
st.sidebar.warning("⚠️REQUEST_CLARIFICATION")
st.sidebar.error("🚨 ESCALATE_TO_HUMAN")

# -------------------------------
# Helpers
# -------------------------------
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
        color = "#546E7A"

    st.markdown(
        f"""
        <div style="
            background-color: rgba(255,255,255,0.04);
            border-left: 4px solid {color};
            padding: 8px 10px;
            margin-bottom: 6px;
            border-radius: 6px;
            font-size: 13px;
            font-family: monospace;
        ">
        {msg}
        </div>
        """,
        unsafe_allow_html=True
    )

def show_pdf(path):
    with open(path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

def llm_explain(final_state):
    prompt = f"""
You are an AI accounting assistant.

Invoice decision: {final_state.get("decision")}
Issues: {final_state.get("issues")}
Reasoning trace: {final_state.get("reasoning")}

In 3-5 lines, explain clearly and simply why this invoice requires human review.
"""
    return call_llm(prompt)

# -------------------------------
# Main Logic
# -------------------------------
if uploaded_files:

    st.subheader("Uploaded Files")
    for f in uploaded_files:
        st.write("•", f.name)

    if st.button(" Process All Invoices"):

        auto_approved = []
        needs_human = []

        for uploaded_file in uploaded_files:

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            status = st.empty()
            status.info(f"Processing {uploaded_file.name}...")

            # Initial state
            state = {
                "file_path": tmp_path,
                "po_db": po_db,
                "reasoning": []
            }

            final_state = None
            last_reasoning_len = 0
            chat_history = []

            # -------------------------------
            # STREAM GRAPH
            # -------------------------------
            for event in agent_app.stream(state):

                if not isinstance(event, dict):
                    continue

                current_state = list(event.values())[0]
                reasoning = current_state.get("reasoning", [])

                if len(reasoning) > last_reasoning_len:
                    last_reasoning_len = len(reasoning)

                final_state = current_state

            status.success(f"✅ Finished {uploaded_file.name}")

            # Classify
            decision = final_state.get("decision")

            record = {
                "file_name": uploaded_file.name,
                "file_path": tmp_path,
                "final_state": final_state
            }

            if decision == "AUTO_APPROVE":
                auto_approved.append(record)
            else:
                # Generate LLM explanation
                explanation = llm_explain(final_state)
                record["human_explanation"] = explanation
                needs_human.append(record)

        # -------------------------------
        # DISPLAY RESULTS IN TABS
        # -------------------------------
        tab1, tab2 = st.tabs([
            f"✅ Auto Approved ({len(auto_approved)})",
            f"🧑‍⚖️ Needs Human Review ({len(needs_human)})"
        ])

        # -------------------------------
        # TAB 1: AUTO APPROVED
        # -------------------------------
        with tab1:
            if not auto_approved:
                st.success("No auto-approved invoices.")
            for rec in auto_approved:
                st.markdown("---")
                st.header(f"📄 {rec['file_name']}")

                left, right = st.columns([1, 1])

                with left:
                    st.subheader("📄 PDF Preview")
                    show_pdf(rec["file_path"])

                with right:
                    st.subheader("🧠 Agent Reasoning")
                    for msg in rec["final_state"]["reasoning"]:
                        render_message(msg)

                    st.subheader("Final Extracted Invoice")
                    st.json(rec["final_state"].get("invoice", {}))

        # -------------------------------
        # TAB 2: NEEDS HUMAN
        # -------------------------------
        with tab2:
            if not needs_human:
                st.success("No invoices need human review.")
            for rec in needs_human:
                st.markdown("---")
                st.header(f"📄 {rec['file_name']}")

                left, right = st.columns([1, 1])

                with left:
                    st.subheader("📄 PDF Preview")
                    show_pdf(rec["file_path"])

                with right:
                    st.subheader("🧠 Agent Reasoning")
                    for msg in rec["final_state"]["reasoning"]:
                        render_message(msg)

                    st.subheader("LLM Explanation")
                    st.info(rec["human_explanation"])

                    st.subheader("⚠️ Issues")
                    for issue in rec["final_state"].get("issues", []):
                        st.json(issue)

else:
    st.info("👈 Upload one or more invoice PDFs from the sidebar to begin.")
