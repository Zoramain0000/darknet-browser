#!/usr/bin/env python3
"""
Robin AI - Main Streamlit Application
Dark web-styled UI for the AI-powered OSINT investigation tool.
Presents the complete pipeline with real-time progress, health monitoring, and reporting.
"""

import os
import sys
import time
import json
import threading
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine import RobinEngine
from backend.tor_proxy import get_proxy
from backend.mistral_client import get_mistral_client
from backend.report_generator import ReportGenerator

# ─── Page Configuration ───────────────────────────────────────────────

st.set_page_config(
    page_title="Robin AI — Dark Web OSINT",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS Injection ─────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    /* Main background - dark cyberpunk */
    .stApp {
        background: #0a0a0f !important;
        background-image: 
            radial-gradient(ellipse at 20% 50%, rgba(0, 240, 255, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 50%, rgba(180, 0, 255, 0.03) 0%, transparent 50%) !important;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Courier New', monospace !important;
        letter-spacing: 0.5px;
    }
    h1 {
        color: #00f0ff !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        border-bottom: 1px solid rgba(0, 240, 255, 0.2);
        padding-bottom: 10px;
    }
    h2 {
        color: #b400ff !important;
        text-shadow: 0 0 15px rgba(180, 0, 255, 0.2);
    }
    h3 {
        color: #00f0ff !important;
    }
    
    /* Cards & containers */
    .css-1r6slb0, .st-bx, .st-cb {
        border-color: rgba(0, 240, 255, 0.15) !important;
    }
    .st-emotion-cache-1r6slb0 {
        border: 1px solid rgba(0, 240, 255, 0.1) !important;
        border-radius: 8px !important;
        background: rgba(10, 10, 15, 0.8) !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0d0d14 !important;
        border-right: 1px solid rgba(0, 240, 255, 0.1) !important;
    }
    section[data-testid="stSidebar"] .st-emotion-cache-1wmy9hl {
        background: #0d0d14 !important;
    }
    
    /* Text inputs */
    input, textarea, .st-bx {
        background: rgba(10, 10, 15, 0.9) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        color: #e0e0e0 !important;
        border-radius: 4px !important;
    }
    input:focus, textarea:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00f0ff, #b400ff) !important;
        color: #0a0a0f !important;
        border: none !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00f0ff, #b400ff) !important;
    }
    
    /* Metric boxes */
    [data-testid="stMetricValue"] {
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.3) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #888 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        border: 1px solid rgba(0, 240, 255, 0.1) !important;
        border-radius: 4px !important;
    }
    .stDataFrame th {
        background: rgba(0, 240, 255, 0.1) !important;
        color: #00f0ff !important;
    }
    .stDataFrame td {
        background: rgba(10, 10, 15, 0.9) !important;
        color: #ccc !important;
    }
    
    /* Alerts */
    .stAlert {
        background: rgba(10, 10, 15, 0.9) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0f;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 240, 255, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 240, 255, 0.5);
    }
    
    /* Status indicators */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-dot.online { background: #00ff00; box-shadow: 0 0 8px rgba(0, 255, 0, 0.5); }
    .status-dot.offline { background: #ff0000; box-shadow: 0 0 8px rgba(255, 0, 0, 0.5); }
    .status-dot.warning { background: #ffaa00; box-shadow: 0 0 8px rgba(255, 170, 0, 0.5); }
    
    /* Pulse animation for live indicator */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .live-indicator {
        animation: pulse 2s infinite;
        color: #00ff00;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #333;
        font-size: 0.8em;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid rgba(0, 240, 255, 0.1);
    }
    .footer a {
        color: #00f0ff;
        text-decoration: none;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="font-size: 48px;">🦉</span>
            <h2 style="color: #00f0ff; margin: 0; text-shadow: 0 0 20px rgba(0,240,255,0.3);">
                ROBIN AI
            </h2>
            <p style="color: #666; font-size: 0.8em; letter-spacing: 3px; text-transform: uppercase;">
                Dark Web OSINT
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚡ System Status")

    # API Key check
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if api_key:
        st.markdown(
            '<span class="status-dot online"></span>Mistral AI: <span style="color:#0f0;">Connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-dot offline"></span>Mistral AI: <span style="color:#f00;">No API Key</span>',
            unsafe_allow_html=True,
        )

    # Tor status (lazy check)
    tor_status_placeholder = st.empty()
    tor_status_placeholder.markdown(
        '<span class="status-dot warning"></span>Tor: <span style="color:#fa0;">Checking...</span>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### ⚙️ Configuration")

    model_choice = st.selectbox(
        "Mistral Model",
        options=[
            "mistral-large-latest",
            "mistral-small-latest",
            "mistral-medium-latest",
            "mistral-nemo-latest",
            "codestral-latest",
            "ministral-3b-latest",
        ],
        index=0,
        help="Select the Mistral AI model for analysis",
    )

    max_sources = st.slider(
        "Max Sources per Engine",
        min_value=5,
        max_value=50,
        value=25,
        help="Maximum results per search engine",
    )

    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown("[🌐 Mistral AI](https://mistral.ai)")
    st.markdown("[📖 Help](https://help.hackerai.co)")
    st.markdown("[🔧 Tor Project](https://torproject.org)")

    st.markdown(
        """
        <div class="footer">
            Robin AI v2.0<br>
            <span style="color: #444;">🔒 Authorized Security Testing Only</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Main Content ─────────────────────────────────────────────────────

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 2.5em; margin-bottom: 0;">
            🦉 ROBIN AI
        </h1>
        <p style="color: #888; font-size: 1.1em; letter-spacing: 4px; text-transform: uppercase;">
            AI-Powered Dark Web OSINT Investigation Platform
        </p>
        <p style="color: #555; font-size: 0.9em; max-width: 600px; margin: 10px auto;">
            Queries 16 dark web search engines in parallel through Tor,
            scrapes discovered .onion sites, and analyzes results with Mistral AI.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Tor Connection Check ─────────────────────────────────────────────

def check_tor():
    """Check Tor proxy in background thread."""
    try:
        proxy = get_proxy()
        ok, ip = proxy.check_connection()
        st.session_state["tor_status"] = "online" if ok else "offline"
        st.session_state["tor_ip"] = ip
    except Exception:
        st.session_state["tor_status"] = "offline"
        st.session_state["tor_ip"] = "unknown"

if "tor_status" not in st.session_state:
    st.session_state["tor_status"] = "checking"
    st.session_state["tor_ip"] = ""
    threading.Thread(target=check_tor, daemon=True).start()

tor_status = st.session_state.get("tor_status", "checking")
tor_ip = st.session_state.get("tor_ip", "")

status_color = {"online": "0f0", "offline": "f00", "checking": "fa0"}.get(tor_status, "fa0")
status_dot = {"online": "online", "offline": "offline", "checking": "warning"}.get(tor_status, "warning")
status_label = {"online": "Connected", "offline": "Disconnected", "checking": "Checking..."}.get(tor_status, "Checking...")

tor_status_placeholder.markdown(
    f'<span class="status-dot {status_dot}"></span>Tor: <span style="color:#{status_color};">{status_label}</span>'
    + (f' <span style="color:#666;font-size:0.8em;">({tor_ip})</span>' if tor_ip else ''),
    unsafe_allow_html=True,
)

# ─── Pipeline Visualization ───────────────────────────────────────────

with st.expander("📊 Investigation Pipeline", expanded=False):
    st.markdown(
        """
        <div style="padding: 20px; text-align: center;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">👤</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">User Query</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">🤖</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">LLM Refine</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">🧅</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">Tor Proxy</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">🔍</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">16× Search</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">🕷️</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">Scrape</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">🧠</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">LLM Analyze</div>
                </div>
                <div style="color: #b400ff; font-size: 20px;">→</div>
                <div style="flex: 1; min-width: 100px; padding: 10px; border: 1px solid rgba(0,240,255,0.2); border-radius: 5px; background: rgba(0,240,255,0.05);">
                    <div style="font-size: 24px;">📄</div>
                    <div style="color: #00f0ff; font-size: 0.8em;">Report</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Search Interface ─────────────────────────────────────────────────

st.markdown("## 🔎 Dark Web Investigation")

col1, col2 = st.columns([4, 1])
with col1:
    search_query = st.text_input(
        "### Enter search query",
        placeholder="e.g., company credentials leak, email database, ransomware group activity...",
        label_visibility="collapsed",
        key="search_input",
    )
with col2:
    search_button = st.button("🚀 INVESTIGATE", use_container_width=True, type="primary")

# ─── Investigation Execution ──────────────────────────────────────────

if search_button and search_query:
    if not api_key:
        st.error(
            "❌ **MISTRAL_API_KEY not configured.**\n\n"
            "Set it in `.env` file:\n"
            "```\nMISTRAL_API_KEY=your_key_here\n```\n"
            "Get a key at [console.mistral.ai](https://console.mistral.ai)"
        )
        st.stop()

    # Initialize engine
    engine = RobinEngine(
        api_key=api_key,
        model=model_choice,
        max_threads=16,
        timeout=30,
    )

    # Progress tracking
    progress_bar = st.progress(0, text="Initializing...")
    status_text = st.empty()

    result_container = st.container()

    def progress_callback(data):
        """Update UI from pipeline progress."""
        progress_bar.progress(data["progress"], text=data["status"])
        status_text.markdown(
            f"<span style='color: #b400ff;'>⏳ {data['status']}</span>",
            unsafe_allow_html=True,
        )

    engine.set_progress_callback(progress_callback)

    # Run investigation in a thread to keep UI responsive
    result_holder = {"data": None}

    def run_pipeline():
        try:
            result = engine.run_investigation(search_query)
            result_holder["data"] = result
        except Exception as e:
            result_holder["data"] = {"error": str(e)}

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    thread.join(timeout=300)  # 5 min max

    result = result_holder.get("data")

    if result and "error" in result:
        st.error(f"❌ Pipeline failed: {result['error']}")
        st.stop()
    elif not result:
        st.error("❌ Investigation timed out after 5 minutes.")
        st.stop()

    # ─── Results Display ──────────────────────────────────────────

    progress_bar.empty()
    status_text.empty()

    total_time = result.get("total_time", 0)
    total_results = result.get("total_results", 0)
    analysis = result.get("analysis", {})
    search_results = result.get("search_results", [])
    scraped_content = result.get("scraped_content", [])
    tor_ip = result.get("tor_ip", "unknown")
    tor_ok = result.get("tor_ok", False)
    refined_query = result.get("refined_query", search_query)
    report_markdown = result.get("report_markdown", "")
    report_path = result.get("report_path", "")

    # ─── Metrics Row ──────────────────────────────────────────────

    st.markdown("## 📊 Investigation Results")

    severity = analysis.get("severity", "unknown").upper()
    severity_color = {
        "CRITICAL": "#ff0000",
        "HIGH": "#ff4400",
        "MEDIUM": "#ffaa00",
        "LOW": "#00ff00",
        "NONE": "#888888",
    }.get(severity, "#888888")

    metrics_cols = st.columns(5)

    with metrics_cols[0]:
        st.metric("🔍 Total Results", total_results)

    with metrics_cols[1]:
        st.metric("🧠 Sources Scraped", len(scraped_content))

    with metrics_cols[2]:
        st.metric("⏱️ Time Elapsed", f"{total_time:.1f}s")

    with metrics_cols[3]:
        st.metric(
            "🛡️ Severity",
            severity,
            delta=None,
        )

    with metrics_cols[4]:
        threats_count = len(analysis.get("threats_found", [])) + len(analysis.get("key_findings", []))
        st.metric("⚠️ Threats Found", threats_count)

    # ─── Tor & Network Info ───────────────────────────────────────

    with st.expander("🌐 Network & Proxy Information", expanded=False):
        info_cols = st.columns(3)
        with info_cols[0]:
            st.markdown(f"**Tor Proxy:** {'✅ Connected' if tor_ok else '❌ Disconnected'}")
            st.markdown(f"**Tor Exit IP:** `{tor_ip}`")
        with info_cols[1]:
            st.markdown(f"**Model:** `{model_choice}`")
            st.markdown(f"**Original Query:** `{search_query}`")
        with info_cols[2]:
            st.markdown(f"**Refined Query:** `{refined_query}`")
            st.markdown(f"**Unique URLs:** {len(set(r.get('url','') for r in search_results))}")

    # ─── AI Analysis ──────────────────────────────────────────────

    st.markdown("## 🧠 Mistral AI Analysis")

    analysis_tabs = st.tabs(["📋 Summary", "⚠️ Threats", "💡 Recommendations", "🔗 Sources"])

    with analysis_tabs[0]:
        summary = analysis.get("summary", "No summary available.")
        st.markdown(
            f"""
            <div style="
                padding: 20px;
                border: 1px solid rgba(0,240,255,0.2);
                border-radius: 8px;
                background: rgba(0,240,255,0.03);
                color: #ddd;
                line-height: 1.8;
            ">
                {summary}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with analysis_tabs[1]:
        threats = analysis.get("threats_found", [])
        findings = analysis.get("key_findings", [])
        all_threats = threats + findings

        if all_threats:
            for i, threat in enumerate(all_threats[:20], 1):
                text = threat if isinstance(threat, str) else threat.get("description", str(threat))
                st.markdown(
                    f"""
                    <div style="
                        padding: 10px 15px;
                        margin: 5px 0;
                        border-left: 3px solid #ff4400;
                        background: rgba(255, 68, 0, 0.05);
                        border-radius: 0 5px 5px 0;
                        color: #ddd;
                    ">
                        <strong style="color: #ff4400;">#{i}</strong> {text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No specific threats identified in the search results.")

    with analysis_tabs[2]:
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                text = rec if isinstance(rec, str) else rec.get("text", str(rec))
                st.markdown(f"- ✅ {text}")
        else:
            st.info("No specific recommendations generated.")

    with analysis_tabs[3]:
        sources = analysis.get("relevant_sources", [])
        if sources:
            for src in sources[:30]:
                text = src if isinstance(src, str) else src.get("url", str(src))
                st.markdown(f"- 🔗 {text}")
        else:
            st.info("No specific source references in analysis.")

    # ─── Search Results Table ─────────────────────────────────────

    st.markdown("## 📑 Dark Web Search Results")

    if search_results:
        import pandas as pd
        df = pd.DataFrame(search_results[:100])
        display_cols = [c for c in ["title", "source", "url", "snippet"] if c in df.columns]
        if display_cols:
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "title": "Title",
                    "source": "Engine",
                    "url": st.column_config.LinkColumn("URL", max_chars=50),
                    "snippet": "Snippet",
                },
            )

        st.caption(f"Showing {min(len(search_results), 100)} of {total_results} results")
    else:
        st.warning("No search results were found. Try a different query.")

    # ─── Scraped Content ─────────────────────────────────────────

    if scraped_content:
        st.markdown("## 🕷️ Scraped .onion Content")

        for sc in scraped_content[:10]:
            title = sc.get("title", "Untitled")
            url = sc.get("url", "")
            content = sc.get("content", "")[:300]
            emails = sc.get("emails", [])
            btc = sc.get("btc_addresses", [])
            eth = sc.get("eth_addresses", [])

            with st.expander(f"📄 {title[:80]}"):
                st.markdown(f"**URL:** [{url}]({url})")
                st.markdown(f"**Content Length:** {sc.get('content_length', 0):,} chars")

                if emails:
                    st.markdown("**📧 Emails Found:**")
                    st.code("\n".join(emails[:20]))
                if btc:
                    st.markdown("**₿ BTC Addresses:**")
                    st.code("\n".join(btc[:10]))
                if eth:
                    st.markdown("**♦ ETH Addresses:**")
                    st.code("\n".join(eth[:10]))

                st.markdown("**Content Preview:**")
                st.text(content)

    # ─── Pipeline Timing ──────────────────────────────────────────

    timings = result.get("timings", {})
    if timings:
        st.markdown("## ⏱️ Pipeline Performance")
        timing_cols = st.columns(len(timings))
        for i, (stage, duration) in enumerate(timings.items()):
            with timing_cols[i % len(timing_cols)]:
                stage_name = stage.replace("_", " ").title()
                st.metric(stage_name, f"{duration:.2f}s")

    # ─── Report Download ──────────────────────────────────────────

    if report_markdown:
        st.markdown("## 📄 Investigation Report")

        report_tabs = st.tabs(["📝 Preview", "💾 Download"])

        with report_tabs[0]:
            st.markdown(report_markdown)

        with report_tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
label="⬇️ Download Markdown Report",
                    data=report_markdown,
                    file_name=f"robin_report_{search_query[:30].replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col2:
                if report_path:
                    st.success(f"💾 Saved to `{report_path}`")

# ─── Empty State ──────────────────────────────────────────────────────

if not search_button and not search_query:
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 60px 20px;
            margin-top: 30px;
            border: 1px solid rgba(0,240,255,0.1);
            border-radius: 12px;
            background: rgba(0,240,255,0.02);
        ">
            <span style="font-size: 64px;">🦉</span>
            <h2 style="color: #555; margin: 20px 0;">Ready to Investigate</h2>
            <p style="color: #444; max-width: 500px; margin: 0 auto; line-height: 1.8;">
                Enter a search query above and click <strong style="color: #00f0ff;">INVESTIGATE</strong>
                to begin a comprehensive dark web OSINT investigation.
                The system will query 16 dark web search engines in parallel through Tor,
                scrape discovered .onion sites, and analyze everything with Mistral AI.
            </p>
            <div style="margin-top: 30px; display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
                <div style="padding: 10px; border: 1px solid rgba(180,0,255,0.2); border-radius: 8px; background: rgba(180,0,255,0.05); min-width: 120px;">
                    <div style="font-size: 24px;">🔍</div>
                    <div style="color: #b400ff; font-size: 0.8em;">16 Engines</div>
                </div>
                <div style="padding: 10px; border: 1px solid rgba(180,0,255,0.2); border-radius: 8px; background: rgba(180,0,255,0.05); min-width: 120px;">
                    <div style="font-size: 24px;">🧅</div>
                    <div style="color: #b400ff; font-size: 0.8em;">Tor Anonymous</div>
                </div>
                <div style="padding: 10px; border: 1px solid rgba(180,0,255,0.2); border-radius: 8px; background: rgba(180,0,255,0.05); min-width: 120px;">
                    <div style="font-size: 24px;">🤖</div>
                    <div style="color: #b400ff; font-size: 0.8em;">Mistral AI</div>
                </div>
                <div style="padding: 10px; border: 1px solid rgba(180,0,255,0.2); border-radius: 8px; background: rgba(180,0,255,0.05); min-width: 120px;">
                    <div style="font-size: 24px;">📄</div>
                    <div style="color: #b400ff; font-size: 0.8em;">Report</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Footer ───────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="footer">
        <p>
            Robin AI v2.0 — AI-Powered Dark Web OSINT Platform<br>
            <span style="color: #444;">
                🔒 Authorized Security Testing Only · 
                Powered by <a href="https://mistral.ai">Mistral AI</a> · 
                Anonymous via <a href="https://torproject.org">Tor</a>
            </span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)