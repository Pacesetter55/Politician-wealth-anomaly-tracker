import streamlit as st
import pandas as pd

from scraper import search_politician, get_elections_from_url
from analyzer import (
    wealth_growth_chart,
    wealth_growth_pct,
    asset_breakdown_bar,
    asset_breakdown_chart,
    criminal_cases_chart,
    detect_discrepancies,
    generate_summary_stats,
    format_inr,
)
from llm_chat import chat, get_quick_summary

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Know Your Politician 🇮🇳",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Base */
.stApp { background: #f5f7fa; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 3rem !important; max-width: 1200px; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    box-shadow: 2px 0 12px rgba(0,0,0,0.04);
}
.sidebar-brand {
    font-size: 1.35rem; font-weight: 700; color: #1a56db;
    margin-bottom: 2px; letter-spacing: -0.4px;
}
.sidebar-tagline { color: #94a3b8; font-size: 0.78rem; margin-bottom: 20px; }

/* ── Hero */
.hero {
    background: linear-gradient(135deg, #1a56db 0%, #0ea5e9 100%);
    border-radius: 18px; padding: 44px 52px; margin-bottom: 32px;
    position: relative; overflow: hidden; color: #fff;
}
.hero::after {
    content: "🗳️";
    position: absolute; right: 48px; top: 50%; transform: translateY(-50%);
    font-size: 90px; opacity: 0.12;
}
.hero h1 { font-size: 2.3rem; font-weight: 700; margin: 0 0 8px; color: #fff; }
.hero p  { font-size: 1rem; color: rgba(255,255,255,0.78); margin: 0; line-height: 1.6; }

/* ── Feature cards on landing */
.feature-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 24px; height: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.feature-card:hover { box-shadow: 0 4px 16px rgba(26,86,219,0.1); }
.feature-icon { font-size: 1.8rem; margin-bottom: 10px; }
.feature-title { font-weight: 600; color: #1e293b; font-size: 0.95rem; margin-bottom: 6px; }
.feature-desc  { color: #64748b; font-size: 0.84rem; line-height: 1.6; }

/* ── Search result card */
.result-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s, border-color 0.15s;
}
.result-card:hover { box-shadow: 0 4px 14px rgba(26,86,219,0.08); border-color: #93c5fd; }
.result-name { font-size: 1.05rem; font-weight: 600; color: #1e293b; margin: 0 0 8px; }
.result-meta { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

/* ── Badges */
.badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 600;
}
.badge-party    { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-year     { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.badge-criminal { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }
.badge-clean    { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.badge-winner   { background: #fefce8; color: #92400e; border: 1px solid #fde68a; }
.badge-flag     { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }

/* ── Politician header */
.pol-header {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 28px 32px; margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border-top: 4px solid #1a56db;
}
.pol-name { font-size: 1.9rem; font-weight: 700; color: #0f172a; margin: 0 0 12px; }
.pol-meta { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

/* ── KPI cards */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 20px 22px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.kpi-label { font-size: 0.74rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 8px; font-weight: 500; }
.kpi-value { font-size: 1.55rem; font-weight: 700; color: #0f172a; margin-bottom: 4px; line-height: 1.2; }
.kpi-sub   { font-size: 0.76rem; color: #94a3b8; }
.kpi-green { color: #15803d !important; }
.kpi-red   { color: #be123c !important; }
.kpi-blue  { color: #1d4ed8 !important; }

/* ── Section heading */
.sec-head {
    font-size: 0.95rem; font-weight: 600; color: #374151;
    margin: 24px 0 14px; padding-left: 10px;
    border-left: 3px solid #1a56db;
}

/* ── Election history row */
.elec-row {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.elec-year { font-weight: 600; color: #1e293b; font-size: 0.95rem; }
.elec-meta { color: #94a3b8; font-size: 0.82rem; margin-left: 8px; }
.elec-val  { font-weight: 600; color: #1d4ed8; font-size: 0.9rem; }

/* ── Flag cards */
.flag-card {
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
    display: flex; gap: 14px; align-items: flex-start;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.flag-HIGH   { background: #fff1f2; border: 1px solid #fecdd3; }
.flag-MEDIUM { background: #fff7ed; border: 1px solid #fed7aa; }
.flag-LOW    { background: #f0fdf4; border: 1px solid #bbf7d0; }
.flag-icon  { font-size: 1.2rem; flex-shrink: 0; margin-top: 2px; }
.flag-title { font-weight: 600; font-size: 0.88rem; color: #1e293b; margin-bottom: 4px; }
.flag-desc  { font-size: 0.82rem; color: #64748b; line-height: 1.55; }

/* ── Chat */
.chat-area { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.bubble-user {
    align-self: flex-end; max-width: 72%;
    background: #1a56db; border-radius: 16px 16px 4px 16px;
    padding: 12px 16px; color: #fff; font-size: 0.88rem; line-height: 1.5;
}
.bubble-bot {
    align-self: flex-start; max-width: 80%;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 16px 16px 16px 4px;
    padding: 12px 16px; color: #334155; font-size: 0.88rem; line-height: 1.6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-label { font-size: 0.7rem; margin-bottom: 5px; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── AI panel */
.ai-banner {
    background: linear-gradient(135deg, #eff6ff, #f0f9ff);
    border: 1px solid #bfdbfe; border-radius: 12px;
    padding: 14px 20px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 14px;
}
.ai-title { font-weight: 600; color: #1d4ed8; font-size: 0.92rem; }
.ai-sub   { color: #64748b; font-size: 0.78rem; }

/* ── Summary box */
.ai-summary {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 20px 24px; color: #334155; font-size: 0.88rem; line-height: 1.7;
}

/* ── Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #fff; border-bottom: 1px solid #e2e8f0; gap: 4px;
    border-radius: 12px 12px 0 0; padding: 4px 4px 0;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b; font-weight: 500; font-size: 0.88rem;
    padding: 10px 18px; border-radius: 8px 8px 0 0; border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #eff6ff !important; color: #1d4ed8 !important;
    border-bottom: 2px solid #1a56db !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #fff; border: 1px solid #e2e8f0; border-top: none;
    border-radius: 0 0 12px 12px; padding: 24px;
}

/* ── Pass/fail row */
.case-row {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 18px; margin-bottom: 8px;
    display: flex; justify-content: space-between; align-items: center;
}

/* ── Info boxes */
.info-box {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 16px 20px; color: #64748b; font-size: 0.82rem; line-height: 1.6;
}
.success-box {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 14px;
    padding: 28px; text-align: center;
}
.success-icon  { font-size: 2.5rem; margin-bottom: 10px; }
.success-title { font-weight: 600; color: #15803d; font-size: 1.05rem; }
.success-sub   { color: #64748b; font-size: 0.84rem; margin-top: 6px; }

/* ── Streamlit overrides */
[data-testid="stMetricValue"] { color: #0f172a !important; }
.stButton > button[kind="primary"] {
    background: #1a56db !important; border: none !important; border-radius: 8px !important;
    font-weight: 500 !important;
}
.stButton > button[kind="secondary"] {
    border: 1px solid #e2e8f0 !important; color: #334155 !important;
    border-radius: 8px !important; background: #fff !important;
}
.stDataFrame { border-radius: 10px !important; overflow: hidden; border: 1px solid #e2e8f0 !important; }
hr { border-color: #e2e8f0 !important; }
.stSpinner > div { border-top-color: #1a56db !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "profiles": [], "search_results": [], "selected_politician": None,
    "chat_history": [], "ai_summary": "", "search_done": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 20px">
        <div class="sidebar-brand">🗳️ KnowYourNeta</div>
        <div class="sidebar-tagline">Lok Sabha · Election Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        label="search_label",
        placeholder="e.g. Narendra Modi, Varanasi…",
        label_visibility="collapsed",
    )
    search_btn = st.button("🔍  Search", type="primary", use_container_width=True)

    if st.session_state.profiles:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to results", use_container_width=True):
            st.session_state.profiles = []
            st.session_state.ai_summary = ""
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("""
    <hr style="margin:24px 0 16px">
    <div style="font-size:0.78rem;color:#94a3b8;line-height:2">
        📂 &nbsp;Data from <b>myneta.info</b><br>
        🗓️ &nbsp;Lok Sabha <b>1999 – 2024</b><br>
        🤖 &nbsp;AI via <b>Groq llama-3.1-8b-instant</b><br>
        ⚡ &nbsp;Powered by <b>Groq cloud API</b>
    </div>
    """, unsafe_allow_html=True)


# ─── Search logic ─────────────────────────────────────────────────────────────
if search_btn and query.strip():
    with st.spinner(f"Searching for **{query}**…"):
        try:
            results = search_politician(query.strip())
            st.session_state.update({
                "search_results": results, "profiles": [],
                "selected_politician": None, "chat_history": [],
                "ai_summary": "", "search_done": True,
            })
        except Exception as e:
            st.error(f"Search failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.search_done and not st.session_state.profiles:
    st.markdown("""
    <div class="hero">
        <h1>Know Your Politician</h1>
        <p>Transparent wealth tracking · Criminal case history · AI-powered insights<br>
        for every Lok Sabha candidate — powered by official Election Commission affidavit data.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    features = [
        ("💰", "Wealth Tracking", "Track how assets & liabilities evolved across every Lok Sabha election affidavit."),
        ("⚖️", "Criminal Records", "View criminal cases declared in official affidavits — transparency without judgement."),
        ("🚩", "Discrepancy Flags", "Algorithmic detection of suspicious wealth spikes and declaration anomalies."),
        ("🤖", "AI Chat", "Ask anything in plain language. Grounded in real data, running 100% locally."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
        col.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;color:#94a3b8;font-size:0.84rem;margin-top:32px">
        👈 &nbsp;Search for a politician in the sidebar &nbsp;·&nbsp;
        Try: <b style="color:#475569">Narendra Modi</b> &nbsp;·&nbsp;
        <b style="color:#475569">Rahul Gandhi</b> &nbsp;·&nbsp;
        <b style="color:#475569">Varanasi</b>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.search_done and not st.session_state.profiles:
    results = st.session_state.search_results

    st.markdown(f"""
    <div style="margin-bottom:20px;display:flex;align-items:baseline;gap:12px">
        <span style="font-size:1.4rem;font-weight:700;color:#1e293b">Search Results</span>
        <span style="color:#94a3b8;font-size:0.88rem">{len(results)} Lok Sabha candidate(s) found</span>
    </div>
    """, unsafe_allow_html=True)

    if not results:
        st.warning("No Lok Sabha candidates found. Try a different spelling or constituency name.")
    else:
        for i, r in enumerate(results[:25]):
            criminal_badge = (
                '<span class="badge badge-criminal">⚠ Criminal Cases</span>'
                if r.get("has_criminal") else
                '<span class="badge badge-clean">✓ Clean Record</span>'
            )
            col_card, col_btn = st.columns([6, 1])
            with col_card:
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-name">{r['name']}</div>
                    <div class="result-meta">
                        <span class="badge badge-party">{r.get('party', 'N/A')}</span>
                        <span class="badge badge-year">Lok Sabha {r.get('year', '?')}</span>
                        {criminal_badge}
                        <span style="color:#94a3b8;font-size:0.82rem">
                            {r.get('constituency', '')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.markdown("<div style='padding-top:14px'>", unsafe_allow_html=True)
                if st.button("View →", key=f"btn_{i}", type="primary"):
                    with st.spinner(f"Loading full election history…"):
                        try:
                            # Use the profile_url directly — avoids re-searching with no-space name
                            profiles = get_elections_from_url(
                                r["profile_url"], r["name"]
                            )
                            if not profiles:
                                st.warning("Could not load election data. Try another candidate.")
                            else:
                                import re as _re
                                clean_name = _re.sub(r"([A-Z])", r" \1", r["name"]).strip()
                                st.session_state.profiles = profiles
                                st.session_state.selected_politician = clean_name
                                st.session_state.chat_history = []
                                st.session_state.ai_summary = ""
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load profile: {e}")
                st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# POLITICIAN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.profiles:
    profiles = st.session_state.profiles
    latest  = max(profiles, key=lambda x: x.get("year", "0"))
    stats   = generate_summary_stats(profiles)
    flags   = detect_discrepancies(profiles)
    name    = st.session_state.selected_politician or latest.get("name", "Unknown")

    # ── Politician header ────────────────────────────────────────────────────
    flag_count = len(flags)
    high_count = sum(1 for f in flags if f["severity"] == "HIGH")

    extra_badges = ""
    if latest.get("winner"):
        extra_badges += ' <span class="badge badge-winner">🏆 Winner</span>'
    if flag_count:
        extra_badges += f' <span class="badge badge-flag">🚩 {flag_count} flag{"s" if flag_count>1 else ""}</span>'

    st.markdown(f"""
    <div class="pol-header">
        <div class="pol-name">{name}</div>
        <div class="pol-meta">
            <span class="badge badge-party">{stats.get('party','N/A')}</span>
            <span class="badge badge-year">{stats.get('elections_fought',1)} Lok Sabha election(s) tracked</span>
            {extra_badges}
            <span style="color:#94a3b8;font-size:0.84rem">
                {stats.get('constituency','')}
                {('· '+stats.get('state','')) if stats.get('state') else ''}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────────────────────────────────────
    g = stats.get("total_growth_pct")
    g_str   = f"+{g}%" if (g or 0) > 0 else (f"{g}%" if g is not None else "N/A")
    g_color = "kpi-green" if (g or 0) <= 300 else "kpi-red"
    c_color = "kpi-red" if stats.get("total_criminal_cases_ever", 0) > 0 else "kpi-green"

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Latest Total Assets</div>
            <div class="kpi-value kpi-blue">{stats.get('latest_assets','N/A')}</div>
            <div class="kpi-sub">as of {stats.get('latest_year','?')}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Latest Liabilities</div>
            <div class="kpi-value">{stats.get('latest_liabilities','N/A')}</div>
            <div class="kpi-sub">declared in affidavit</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Wealth Growth</div>
            <div class="kpi-value {g_color}">{g_str}</div>
            <div class="kpi-sub">{stats.get('earliest_year','?')} → {stats.get('latest_year','?')}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Criminal Cases (Total)</div>
            <div class="kpi-value {c_color}">{stats.get('total_criminal_cases_ever',0)}</div>
            <div class="kpi-sub">declared across all elections</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊  Overview", "💰  Wealth Analysis",
        "⚖️  Criminal Cases", "🚩  Discrepancies", "🤖  AI Chat",
    ])

    # ── TAB 1: Overview ──────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="sec-head">AI Summary</div>', unsafe_allow_html=True)
        if not st.session_state.ai_summary:
            if st.button("✨ Generate AI Summary", type="secondary"):
                with st.spinner("Analyzing with Groq llama-3.1-8b-instant…"):
                    st.session_state.ai_summary = get_quick_summary(profiles)
        if st.session_state.ai_summary:
            st.markdown(f'<div class="ai-summary">{st.session_state.ai_summary.replace(chr(10),"<br>")}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Election History</div>', unsafe_allow_html=True)
        rows = []
        for p in sorted(profiles, key=lambda x: x.get("year", "0")):
            rows.append({
                "Year": p.get("year", "?"),
                "Party": p.get("party", "N/A"),
                "Constituency": p.get("constituency", "N/A"),
                "Total Assets": format_inr(p.get("total_assets", 0)),
                "Total Liabilities": format_inr(p.get("total_liabilities", 0)),
                "Criminal Cases": p.get("num_criminal_cases", 0),
                "Education": p.get("education", "N/A"),
            })
        if rows:
            st.dataframe(
                pd.DataFrame(rows), use_container_width=True, hide_index=True,
                column_config={"Criminal Cases": st.column_config.NumberColumn(format="%d ⚖️")},
            )

    # ── TAB 2: Wealth ────────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="sec-head">Wealth Growth Across Elections</div>', unsafe_allow_html=True)
        fig = wealth_growth_chart(profiles)
        if fig:
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="#f8fafc",
                              font_color="#334155", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for wealth chart. Need at least 2 elections with declared assets.")

        growth = wealth_growth_pct(profiles)
        if growth:
            st.markdown('<div class="sec-head">Election-to-Election Growth</div>', unsafe_allow_html=True)
            gcols = st.columns(len(growth))
            for col, g in zip(gcols, growth):
                color = "#be123c" if g["growth_pct"] > 200 else "#15803d"
                col.markdown(f"""
                <div class="kpi-card" style="text-align:center">
                    <div class="kpi-label">{g['from_year']} → {g['to_year']}</div>
                    <div class="kpi-value" style="color:{color}">
                        {'+' if g['growth_pct']>0 else ''}{g['growth_pct']}%
                    </div>
                    <div class="kpi-sub">{g['from_assets']} → {g['to_assets']}</div>
                </div>
                """, unsafe_allow_html=True)

        cl, cr = st.columns(2)
        with cl:
            st.markdown('<div class="sec-head">Movable vs Immovable</div>', unsafe_allow_html=True)
            fig_bar = asset_breakdown_bar(profiles)
            if fig_bar:
                fig_bar.update_layout(paper_bgcolor="white", plot_bgcolor="#f8fafc",
                                      font_color="#334155", template="plotly_white")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Breakdown not available — affidavit pages use JavaScript rendering.")
        with cr:
            st.markdown('<div class="sec-head">Latest Year Composition</div>', unsafe_allow_html=True)
            if latest.get("movable_assets", 0) + latest.get("immovable_assets", 0) > 0:
                fig_pie = asset_breakdown_chart(latest)
                if fig_pie:
                    fig_pie.update_layout(paper_bgcolor="white", font_color="#334155")
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Movable/immovable breakdown not available for this candidate.")

    # ── TAB 3: Criminal Cases ─────────────────────────────────────────────────
    with tab3:
        total_ever = stats.get("total_criminal_cases_ever", 0)

        if total_ever == 0:
            st.markdown("""
            <div class="success-box">
                <div class="success-icon">✅</div>
                <div class="success-title">No Criminal Cases Declared</div>
                <div class="success-sub">Across all tracked Lok Sabha elections</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#fff1f2;border:1px solid #fecdd3;border-radius:12px;
                        padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px">
                <span style="font-size:1.5rem">⚠️</span>
                <div>
                    <div style="color:#be123c;font-weight:600;font-size:1rem">{total_ever} criminal case(s) declared</div>
                    <div style="color:#94a3b8;font-size:0.81rem">Declared ≠ Convicted. Presumption of innocence applies.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            fig_c = criminal_cases_chart(profiles)
            if fig_c:
                fig_c.update_layout(paper_bgcolor="white", plot_bgcolor="#f8fafc",
                                    font_color="#334155", template="plotly_white")
                st.plotly_chart(fig_c, use_container_width=True)

        st.markdown('<div class="sec-head">Year-wise Breakdown</div>', unsafe_allow_html=True)
        for p in sorted(profiles, key=lambda x: x.get("year", "0")):
            n = p.get("num_criminal_cases", 0)
            color = "#be123c" if n > 0 else "#15803d"
            icon  = "⚠️" if n > 0 else "✅"
            st.markdown(f"""
            <div class="case-row">
                <span>
                    <span class="elec-year">Lok Sabha {p.get('year','?')}</span>
                    <span class="elec-meta">{p.get('constituency','')}</span>
                </span>
                <span style="color:{color};font-weight:600;font-size:0.88rem">{icon} {n} case(s)</span>
            </div>
            """, unsafe_allow_html=True)
            if p.get("criminal_cases"):
                for case in p["criminal_cases"]:
                    st.json(case, expanded=False)

    # ── TAB 4: Discrepancies ──────────────────────────────────────────────────
    with tab4:
        if not flags:
            st.markdown("""
            <div class="success-box">
                <div class="success-icon">🟢</div>
                <div class="success-title">No Red Flags Detected</div>
                <div class="success-sub">No anomalies found in the declared affidavit data</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            high_c   = sum(1 for f in flags if f["severity"] == "HIGH")
            medium_c = sum(1 for f in flags if f["severity"] == "MEDIUM")
            low_c    = sum(1 for f in flags if f["severity"] == "LOW")

            fc1, fc2, fc3 = st.columns(3)
            for col, label, count, color, bg in [
                (fc1, "HIGH",   high_c,   "#be123c", "#fff1f2"),
                (fc2, "MEDIUM", medium_c, "#c2410c", "#fff7ed"),
                (fc3, "LOW",    low_c,    "#15803d", "#f0fdf4"),
            ]:
                col.markdown(f"""
                <div class="kpi-card" style="background:{bg};border-color:{color}30;text-align:center">
                    <div class="kpi-label">{label} severity</div>
                    <div class="kpi-value" style="color:{color}">{count}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="sec-head">Detailed Flags</div>', unsafe_allow_html=True)
            icons = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}
            for f in flags:
                st.markdown(f"""
                <div class="flag-card flag-{f['severity']}">
                    <div class="flag-icon">{icons.get(f['severity'],'⚪')}</div>
                    <div>
                        <div class="flag-title">[{f['severity']}] {f['type']}</div>
                        <div class="flag-desc">{f['detail']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-box" style="margin-top:20px">
            ⓘ Flags are generated algorithmically from declared affidavit data on myneta.info.
            Always cross-verify with official Election Commission of India records.
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 5: AI Chat ────────────────────────────────────────────────────────
    with tab5:
        st.markdown(f"""
        <div class="ai-banner">
            <span style="font-size:1.6rem">🤖</span>
            <div>
                <div class="ai-title">AI Political Analyst</div>
                <div class="ai-sub">Powered by Groq llama-3.1-8b-instant · Fast cloud inference · Answers grounded in affidavit data</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.chat_history:
            html = '<div class="chat-area">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    html += f'<div class="bubble-user"><div class="bubble-label">You</div>{msg["content"]}</div>'
                else:
                    content = msg["content"].replace("\n", "<br>")
                    html += f'<div class="bubble-bot"><div class="bubble-label">AI Analyst</div>{content}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown('<div style="color:#94a3b8;font-size:0.8rem;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.06em">Suggested questions</div>', unsafe_allow_html=True)
            suggestions = [
                f"How has {name}'s wealth changed across elections?",
                f"Summarise any criminal cases against {name}.",
                f"Are there suspicious patterns in {name}'s declarations?",
                f"Give me a voter-friendly summary of {name}'s profile.",
            ]
            sc1, sc2 = st.columns(2)
            for i, s in enumerate(suggestions):
                col = sc1 if i % 2 == 0 else sc2
                if col.button(s, key=f"sugg_{i}"):
                    with st.spinner("Thinking…"):
                        reply = chat(s, profiles, st.session_state.chat_history)
                    st.session_state.chat_history += [
                        {"role": "user", "content": s},
                        {"role": "assistant", "content": reply},
                    ]
                    st.rerun()

        user_input = st.chat_input(f"Ask about {name}…")
        if user_input:
            with st.spinner("Thinking…"):
                reply = chat(user_input, profiles, st.session_state.chat_history)
            st.session_state.chat_history += [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": reply},
            ]
            st.rerun()

        if st.session_state.chat_history:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑  Clear conversation"):
                st.session_state.chat_history = []
                st.rerun()
