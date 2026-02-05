import streamlit as st
import os
import json
import tempfile
import hashlib
import time
from graph import build_graph
from llm import call_llm
from pdf2image import convert_from_path

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Invoice Reconciliation AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #374151;
    }
    
    .upload-section {
        background-color: #1F2937;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #374151;
        margin-bottom: 1.5rem;
    }
    
    .legend-card {
        background-color: #111827;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #374151;
        text-align: center;
    }
    
    .version-card {
        background-color: #1F2937;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #374151;
        border-left: 4px solid #3B82F6;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #059669 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1F2937;
        border-radius: 8px;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #9CA3AF;
        border-radius: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; color: white; font-size: 2.5rem;">Invoice Reconciliation AI</h1>
    <p style="margin: 0.5rem 0 0 0; color: #E5E7EB; font-size: 1.1rem;">
        Real-time Multi-Agent orchestration • Explainable decisions • Human-in-the-loop review
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Load PO DB
# --------------------------------------------------
with open("purchase_orders.json") as f:
    po_db = json.load(f)

agent_app = build_graph()

# --------------------------------------------------
# Main Upload Section
# --------------------------------------------------

# --------------------------------------------------
# Utility: Stable hash for caching
# --------------------------------------------------
def hash_state_for_llm(final_state: dict) -> str:
    relevant = {
        "decision": final_state.get("decision"),
        "issues": final_state.get("issues"),
        "reasoning": final_state.get("reasoning"),
    }
    serialized = json.dumps(relevant, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

# --------------------------------------------------
# UI Helpers
# --------------------------------------------------
def render_message(msg: str):
    if msg.startswith("[DocumentAgent]"):
        color = "#3B82F6"
        icon = "📄"
    elif msg.startswith("[MatchingAgent]"):
        color = "#F59E0B"
        icon = "🔍"
    elif msg.startswith("[DiscrepancyAgent]"):
        color = "#EF4444"
        icon = "⚠️"
    elif msg.startswith("[ResolutionAgent]"):
        color = "#10B981"
        icon = "✅"
    elif msg.startswith("[HumanReviewAgent]"):
        color = "#8B5CF6"
        icon = "👤"
    else:
        color = "#6B7280"
        icon = "🤖"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
            border-left: 4px solid {color};
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 8px;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 14px;
            color: #E5E7EB;
            border: 1px solid {color}30;
        ">
            <span style="color: {color}; font-weight: 600;">{icon}</span> {msg}
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

# --------------------------------------------------
# LLM Explanations (CACHED)
# --------------------------------------------------
def llm_summary(final_state):
    prompt = f"""
You are an AI finance operations assistant.

Write a short, clear 1–2 sentence explanation in natural language
explaining WHY this invoice received the given decision.

Decision: {final_state.get("decision")}
Issues: {final_state.get("issues")}
Reasoning trace: {final_state.get("reasoning")}

Do not mention confidence scores or internal system details.
"""
    return call_llm(prompt)


def llm_human_explain(final_state):
    prompt = f"""
You are an AI accounting assistant.

Write a clear, human-readable explanation (2-3 sentences) in plain English explaining why this invoice requires human review. 
Do not use JSON format or technical jargon. Write as if explaining to a finance manager.

Decision: {final_state.get("decision")}
Issues: {final_state.get("issues")}
Reasoning trace: {final_state.get("reasoning")}

Example format: "This invoice requires manual review because there is a price discrepancy for Ibuprofen BP 200mg. The invoice shows $88.00 but the purchase order indicates $80.00, representing a $8.00 difference that exceeds acceptable tolerance levels."
"""
    return call_llm(prompt)


@st.cache_data(show_spinner=False)
def llm_summary_cached(state_hash: str, final_state: dict) -> str:
    return llm_summary(final_state)


@st.cache_data(show_spinner=False)
def llm_human_explain_cached(state_hash: str, final_state: dict) -> str:
    return llm_human_explain(final_state)

# --------------------------------------------------
# Persistence
# --------------------------------------------------
def save_output_json(file_name, final_state, summary, human_explanation=None):
    os.makedirs("outputs", exist_ok=True)
    payload = {
        "file_name": file_name,
        "decision": final_state.get("decision"),
        "invoice": final_state.get("invoice"),
        "matched_po": final_state.get("matched_po"),
        "issues": final_state.get("issues"),
        "reasoning": final_state.get("reasoning"),
        "summary": summary,
        "human_explanation": human_explanation
    }
    base = os.path.splitext(file_name)[0]
    path = os.path.join("outputs", f"{base}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path

# --------------------------------------------------
# Rendering summary (NO HTML, NO DIV)
# --------------------------------------------------
def render_summary(rec):
    decision = rec["final_state"].get("decision", "UNKNOWN")

    if decision == "AUTO_APPROVE":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #059669 0%, #10B981 100%); 
                    padding: 1rem; border-radius: 8px; color: white; font-weight: 600;">
            ✅ AUTO APPROVED
        </div>
        """, unsafe_allow_html=True)
    elif decision == "REQUEST_CLARIFICATION":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%); 
                    padding: 1rem; border-radius: 8px; color: white; font-weight: 600;">
            ⚠️ NEEDS CLARIFICATION
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%); 
                    padding: 1rem; border-radius: 8px; color: white; font-weight: 600;">
            🚨 HUMAN REVIEW REQUIRED
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background-color: #1F2937; padding: 1rem; border-radius: 8px; 
                margin-top: 1rem; border: 1px solid #374151; color: #E5E7EB;">
        {rec["summary"]}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <p style="color: #9CA3AF; font-size: 0.9rem; margin-top: 0.5rem;">
        📁 Output saved to: <code style="background-color: #374151; padding: 2px 6px; 
        border-radius: 4px;">{rec.get('output_path')}</code>
    </p>
    """, unsafe_allow_html=True)


# Main Flow

# Upload section at the top
st.markdown("""
<div class="upload-section">
    <h3 style="margin-top: 0; color: #F3F4F6;">📤 Upload Invoice PDFs</h3>
    <p style="color: #9CA3AF; margin-bottom: 1rem;">Choose one or more invoice PDF files to process</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Choose files",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key="file_uploader"
)

# Hide the file list in the uploader widget
st.markdown("""
<style>
    div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] div[data-testid="fileDropzoneInstructions"] + div {
        display: none !important;
    }
    div[data-testid="stFileUploader"] ul {
        display: none !important;
    }
    div[data-testid="stFileUploader"] .uploadedFiles {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Decision Legend
st.markdown("### Decision Categories")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="legend-card" style="border-left: 4px solid #10B981;">
        <strong style="color: #10B981;">AUTO_APPROVE</strong>
        <p style="color: #9CA3AF; font-size: 0.9rem; margin: 0.5rem 0 0 0;">Clean matches, ready for payment</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="legend-card" style="border-left: 4px solid #F59E0B;">
        <strong style="color: #F59E0B;">REQUEST_CLARIFICATION</strong>
        <p style="color: #9CA3AF; font-size: 0.9rem; margin: 0.5rem 0 0 0;">Minor issues, needs follow-up</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="legend-card" style="border-left: 4px solid #EF4444;">
        <strong style="color: #EF4444;">ESCALATE_TO_HUMAN</strong>
        <p style="color: #9CA3AF; font-size: 0.9rem; margin: 0.5rem 0 0 0;">Critical issues, manual review</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

main_col, events_col = st.columns([2, 1])

with events_col:
    st.subheader("Version History")
    st.markdown(
        """
        <style>
            @keyframes attention-border {
                0%, 100% {
                    border-color: #800000;
                }
                50% {
                    border-color: #ff4d4d; /* A brighter, more attention-grabbing red */
                }
            }
        </style>
        
        <div style="background-color: #1C4E38 ; color: white; padding: 1em; border-radius: 10px; border: 3px solid #800000; animation: attention-border 2s ease-in-out infinite;">
        
        **v1.3 - Feb 05, 2026**
        - Improved the User Exeperience with better UI feedback.
        - Optimized multi-file upload performance.
        - Enhanced security for file handling.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.info("Check back here for news and updates on the app!")


with main_col:
    if uploaded_files:
        st.markdown("### 📋 Selected Files")
        for f in uploaded_files:
            st.markdown(f"""
            <div style="background-color: #1F2937; padding: 0.75rem; border-radius: 6px; 
                        margin-bottom: 0.5rem; border: 1px solid #374151;">
                📄 <strong style="color: #F3F4F6;">{f.name}</strong>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🚀 Process Invoices", use_container_width=True):

            auto_approved, needs_human = [], []
            
            # Single processing area for all files
            status_container = st.empty()
            progress_container = st.empty()
            status_text_container = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                # Update the single status area
                with status_container.container():
                    st.markdown(f'<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>Processing&nbsp;&nbsp;&nbsp;<strong>{uploaded_file.name}</strong> ({i+1}/{len(uploaded_files)})</div><style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>', unsafe_allow_html=True)
                
                # Individual file progress (0% to 100% for each file)
                progress_bar = progress_container.progress(0)
                status_text = status_text_container.empty()

                state = {
                    "file_path": tmp_path,
                    "po_db": po_db,
                    "reasoning": []
                }

                nodes = ["document", "matching", "discrepancy", "resolution", "human_review"]
                total_steps = len(nodes)
                final_state = None
                current_progress = 0

                for event in agent_app.stream(state):
                    if isinstance(event, dict):
                        # Check if the event is from a node
                        if len(event) == 1 and list(event.keys())[0] in nodes:
                            node_name = list(event.keys())[0]
                            
                            # Update progress
                            step = nodes.index(node_name) + 1
                            target_progress = step / total_steps
                            
                            # Animate the progress bar
                            for p in range(int(current_progress * 100), int(target_progress * 100)):
                                progress_bar.progress(p / 100)
                                time.sleep(0.01)
                            current_progress = target_progress
                            
                            # The output of the node is the new state
                            final_state = list(event.values())[0]
                            
                            # Update status text
                            if final_state.get("reasoning"):
                                latest_msg = final_state["reasoning"][-1]
                                if "[DocumentAgent]" in latest_msg:
                                    status_text.markdown("📄 **Extracting invoice data...**")
                                elif "[MatchingAgent]" in latest_msg:
                                    status_text.markdown("🔍 **Matching purchase orders...**")
                                elif "[DiscrepancyAgent]" in latest_msg:
                                    status_text.markdown("⚠️ **Analyzing discrepancies...**")
                                elif "[ResolutionAgent]" in latest_msg:
                                    status_text.markdown("✅ **Making final decision...**")
                                elif "[HumanReviewAgent]" in latest_msg:
                                    status_text.markdown("👤 **Flagging for human review...**")
                        else:
                            # This is likely the final aggregated state at the end.
                            final_state = event

                # Complete the progress bar for this file
                progress_bar.progress(1.0)
                status_text.markdown(f"✅ **{uploaded_file.name} completed!**")

                # ---- Cached LLM explanations ----
                state_hash = hash_state_for_llm(final_state)
                summary = llm_summary_cached(state_hash, final_state)

                record = {
                    "file_name": uploaded_file.name,
                    "file_path": tmp_path,
                    "final_state": final_state,
                    "summary": summary
                }

                decision = final_state.get("decision")

                if decision == "AUTO_APPROVE":
                    record["output_path"] = save_output_json(
                        uploaded_file.name, final_state, summary
                    )
                    auto_approved.append(record)
                else:
                    explanation = llm_human_explain_cached(state_hash, final_state)
                    record["human_explanation"] = explanation
                    record["output_path"] = save_output_json(
                        uploaded_file.name, final_state, summary, explanation
                    )
                    needs_human.append(record)
            
            # Clear the processing area after all files are done
            status_container.empty()
            progress_container.empty()
            status_text_container.empty()
            
            st.success(f"✅ All {len(uploaded_files)} invoices processed successfully!")

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
                    st.subheader(f"📄 {rec['file_name']}")
                    render_summary(rec)

                    left, right = st.columns([1, 1])
                    with left:
                        show_pdf(rec["file_path"])
                    with right:
                        st.markdown("#### 🧠 Agent Reasoning")
                        st.markdown("""
                        <div style="background-color: #111827; border-radius: 8px; 
                                    border: 1px solid #374151; max-height: 260px; overflow-y: auto; padding: 1rem;">
                        """, unsafe_allow_html=True)
                        for msg in rec["final_state"]["reasoning"]:
                            render_message(msg)
                        st.markdown("</div>", unsafe_allow_html=True)

            with tab2:
                if not needs_human:
                    st.success("No invoices require human review.")
                for rec in needs_human:
                    st.markdown("---")
                    st.subheader(f"📄 {rec['file_name']}")
                    render_summary(rec)

                    left, right = st.columns([1, 1])
                    with left:
                        show_pdf(rec["file_path"])
                    with right:
                        st.markdown("#### 🧠 Agent Reasoning")
                        st.markdown("""
                        <div style="background-color: #111827; border-radius: 8px; 
                                    border: 1px solid #374151; max-height: 220px; overflow-y: auto; padding: 1rem;">
                        """, unsafe_allow_html=True)
                        for msg in rec["final_state"]["reasoning"]:
                            render_message(msg)
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("#### 🤖 Human Review Explanation")
                        st.markdown(f"""
                        <div style="background-color: #1F2937; padding: 1rem; border-radius: 8px; 
                                    border: 1px solid #374151; border-left: 4px solid #60A5FA; color: #E5E7EB;">
                            {rec["human_explanation"]}
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("#### ⚠️ Issues")
                        for issue in rec["final_state"].get("issues", []):
                            st.markdown("""
                            <div style="background-color: #111827; border-radius: 6px; 
                                        border: 1px solid #374151; padding: 1rem; margin-bottom: 0.5rem;">
                            """, unsafe_allow_html=True)
                            st.json(issue)
                            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="background-color: #1F2937; padding: 2rem; border-radius: 12px; 
                    text-align: center; border: 2px dashed #374151;">
            <h3 style="color: #9CA3AF; margin-bottom: 1rem;">📤 Ready to Process Invoices</h3>
            <p style="color: #6B7280; margin: 0;">Upload one or more invoice PDFs above to begin processing.</p>
        </div>
        """, unsafe_allow_html=True)