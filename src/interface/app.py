import streamlit as st
import sys
import json
import math
from pathlib import Path
from decimal import Decimal
from streamlit_agraph import agraph, Node, Edge, Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.config import AppConfig
from src.pipeline.graph import build_pipeline

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="SchemaDoc AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM THEME CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: rgba(14,17,23,0.85);
    backdrop-filter: blur(12px);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c12 0%, #111827 100%) !important;
    border-right: 1px solid rgba(0,212,255,0.08);
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(0,212,255,0.04), rgba(14,17,23,0.7));
    border: 1px solid rgba(0,212,255,0.12);
    border-radius: 12px;
    padding: 18px 22px;
    transition: border-color 0.3s;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(0,212,255,0.3);
}
[data-testid="stMetricValue"] {
    font-weight: 800 !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid rgba(0,212,255,0.08);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 12px 24px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,212,255,0.08) !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(0,212,255,0.08);
    border-radius: 10px;
    margin-bottom: 8px;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0,212,255,0.2);
}

/* ── Custom HTML classes ── */
.sd-brand {display:flex;align-items:center;gap:14px;padding:8px 0 20px;}
.sd-brand .icon {font-size:32px;}
.sd-brand .text .name {
    font-size:24px;font-weight:800;
    background:linear-gradient(135deg,#00d4ff,#00ff88);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    line-height:1.2;
}
.sd-brand .text .sub {
    font-size:11px;color:#4a6077;text-transform:uppercase;
    letter-spacing:0.12em;margin-top:2px;
}

.sd-hero {text-align:center;padding:50px 0 30px;}
.sd-hero h1 {
    font-size:52px;font-weight:800;line-height:1.1;
    background:linear-gradient(135deg,#00d4ff 0%,#b06eff 50%,#00ff88 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    margin-bottom:16px;letter-spacing:-0.03em;
}
.sd-hero p {font-size:17px;color:#4a6077;max-width:640px;margin:0 auto;line-height:1.7;}

.sd-features {display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:40px 0;}
.sd-feat {
    background:rgba(14,20,25,0.5);border:1px solid rgba(0,212,255,0.08);
    border-radius:12px;padding:28px 20px;text-align:center;
    transition:all 0.3s;
}
.sd-feat:hover {border-color:rgba(0,212,255,0.25);transform:translateY(-3px);}
.sd-feat .fi {font-size:30px;margin-bottom:14px;}
.sd-feat .fn {font-size:15px;font-weight:700;color:#fff;margin-bottom:6px;}
.sd-feat .fd {font-size:13px;color:#4a6077;line-height:1.5;}

.sd-sep {border:none;border-top:1px solid rgba(0,212,255,0.08);margin:24px 0;}

.sd-tag {
    display:inline-block;padding:2px 10px;border-radius:12px;
    font-size:11px;font-weight:600;margin:1px 2px;letter-spacing:0.03em;
}
.sd-tag-pk  {background:rgba(0,212,255,0.12);color:#00d4ff;border:1px solid rgba(0,212,255,0.25);}
.sd-tag-fk  {background:rgba(176,110,255,0.12);color:#b06eff;border:1px solid rgba(176,110,255,0.25);}
.sd-tag-pii {background:rgba(255,77,109,0.12);color:#ff4d6d;border:1px solid rgba(255,77,109,0.25);}
.sd-tag-sys {background:rgba(255,184,0,0.12);color:#ffb800;border:1px solid rgba(255,184,0,0.25);}
.sd-tag-def {background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid rgba(0,255,136,0.25);}

.sd-sec-head {
    font-size:12px;font-weight:700;color:#4a6077;text-transform:uppercase;
    letter-spacing:0.1em;margin-bottom:16px;padding-bottom:8px;
    border-bottom:1px solid rgba(0,212,255,0.06);
}

.sd-stat-grid {display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px;}
.sd-stat {
    background:rgba(0,0,0,0.2);border-radius:8px;padding:10px;text-align:center;
}
.sd-stat .v {font-weight:700;font-size:15px;color:#fff;}
.sd-stat .l {font-size:10px;color:#4a6077;text-transform:uppercase;letter-spacing:0.05em;}

.sd-trow {
    display:flex;align-items:center;padding:14px 18px;
    border:1px solid rgba(0,212,255,0.06);border-radius:10px;
    margin-bottom:8px;background:rgba(14,20,25,0.3);transition:border-color 0.2s;
}
.sd-trow:hover {border-color:rgba(0,212,255,0.2);}
.sd-trow .tn {font-weight:700;color:#fff;font-size:15px;flex:1;}
.sd-trow .tm {font-size:12px;color:#4a6077;margin-right:16px;}
.sd-trow .th {width:120px;text-align:right;}

.sd-hbar {width:100%;height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden;margin-top:6px;}
.sd-hbar .fill {height:100%;border-radius:3px;}

.sd-alert {
    background:rgba(255,77,109,0.06);border:1px solid rgba(255,77,109,0.15);
    border-radius:8px;padding:14px 18px;display:flex;align-items:flex-start;
    gap:10px;margin-bottom:10px;font-size:14px;color:#ff4d6d;
}
.sd-alert-warn {
    background:rgba(255,184,0,0.06);border:1px solid rgba(255,184,0,0.15);
    color:#ffb800;
}

.sd-legend {
    display:flex;gap:20px;justify-content:center;margin-top:16px;
    padding:12px;background:rgba(14,20,25,0.5);border-radius:8px;
}
.sd-legend-item {display:flex;align-items:center;gap:6px;font-size:13px;color:#4a6077;}
.sd-legend-dot {width:10px;height:10px;border-radius:50%;}

.sd-ai-overview {
    background:rgba(14,20,25,0.5);border:1px solid rgba(0,212,255,0.10);
    border-radius:12px;padding:22px 24px;margin-bottom:20px;
}
.ov-title {font-size:14px;font-weight:700;color:#00d4ff;margin-bottom:10px;}

/* Pipeline Integrity Log */
.sd-pipeline-summary {
    background:linear-gradient(145deg, rgba(14,20,25,0.6), rgba(0,212,255,0.03));
    border:1px solid rgba(0,212,255,0.12);border-radius:12px;
    padding:20px 24px;margin-bottom:16px;
}
.ps-badge {
    display:inline-block;padding:4px 14px;border-radius:20px;
    font-size:13px;font-weight:700;margin-bottom:10px;
}
.ps-retry {background:rgba(255,184,0,0.12);color:#ffb800;border:1px solid rgba(255,184,0,0.25);}
.ps-clean {background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid rgba(0,255,136,0.25);}
.ps-detail {font-size:14px;color:#a0aec0;line-height:1.6;}
.ps-detail strong {color:#fff;}
.sd-log-entry {
    display:flex;align-items:flex-start;gap:12px;
    padding:12px 16px;border-radius:8px;margin-bottom:6px;
    border:1px solid rgba(255,255,255,0.04);
}
.sd-log-ok {background:rgba(0,255,136,0.03);}
.sd-log-fail {background:rgba(255,77,109,0.04);border-color:rgba(255,77,109,0.12);}
.log-icon {font-size:18px;margin-top:1px;}
.log-msg {font-size:14px;font-weight:600;color:#e0e0e0;}
.log-errors {font-size:12px;color:#ff4d6d;margin-top:6px;line-height:1.7;}
</style>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_null_pct(stats, row_count=0):
    """Get null percentage — computes from raw count if the percentage field is missing."""
    if not stats:
        return 0.0
    if "null_percentage" in stats and stats["null_percentage"] is not None:
        return stats["null_percentage"]
    if row_count and row_count > 0 and "null_count" in stats:
        return round((stats["null_count"] / row_count) * 100, 2)
    return 0.0


def get_unique_pct(stats, row_count=0):
    """Get unique percentage — computes from raw count if the percentage field is missing."""
    if not stats:
        return 0.0
    if "unique_percentage" in stats and stats["unique_percentage"] is not None:
        return stats["unique_percentage"]
    if row_count and row_count > 0 and "unique_count" in stats:
        return round((stats["unique_count"] / row_count) * 100, 2)
    return 0.0


def health_color(score):
    if score >= 90:
        return "#00ff88"
    if score >= 70:
        return "#ffb800"
    return "#ff4d6d"


def health_label(score):
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Good"
    if score >= 70:
        return "Fair"
    return "Poor"


def render_tags(tags):
    tag_map = {"PK": "pk", "FK": "fk", "PII": "pii", "System": "sys"}
    html = ""
    for t in (tags or []):
        cls = tag_map.get(t, "def")
        html += f'<span class="sd-tag sd-tag-{cls}">{t}</span>'
    return html


def generate_markdown(schema_data):
    total_tables = len(schema_data)
    total_cols = sum(len(t.get("columns", {})) for t in schema_data.values())
    total_rows = sum(t.get("row_count", 0) for t in schema_data.values())
    avg_health = sum(t.get("health_score", 100) for t in schema_data.values()) / total_tables if total_tables else 0
    pii_cols = [f"{t}.{c}" for t, tm in schema_data.items() for c, cm in tm.get("columns", {}).items() if "PII" in (cm.get("tags") or [])]

    md = "# Data Dictionary — SchemaDoc AI\n\n"
    md += "*Generated by SchemaDoc AI Pipeline*\n\n"

    # ── Database overview section ──
    md += "## Database Overview\n\n"
    md += f"| Metric | Value |\n|--------|-------|\n"
    md += f"| Tables | {total_tables} |\n"
    md += f"| Total Columns | {total_cols} |\n"
    md += f"| Total Rows | {total_rows:,} |\n"
    md += f"| Avg Health Score | {avg_health:.1f}/100 |\n"
    md += f"| PII Columns Detected | {len(pii_cols)} |\n\n"

    if st.session_state.get("db_overview"):
        md += f"> {st.session_state['db_overview']}\n\n"

    md += "---\n\n"

    # ── Per-table documentation ──
    for table, meta in schema_data.items():
        row_count = meta.get("row_count", 0)
        hs = meta.get("health_score", 100)
        md += f"## Table: `{table}`\n"
        md += f"**Rows:** {row_count:,} | **Health Score:** {hs}/100\n\n"
        fks = meta.get("foreign_keys", [])
        if fks:
            md += "**Foreign Keys:** "
            md += ", ".join(
                [f"`{fk['column']}` → `{fk['referred_table']}.{fk['referred_column']}`" for fk in fks]
            )
            md += "\n\n"
        md += "| Column | Type | Null % | Unique % | Description | Tags |\n"
        md += "|--------|------|--------|----------|-------------|------|\n"
        for col_name, col_data in meta.get("columns", {}).items():
            stats = col_data.get("stats") or {}
            null_pct = get_null_pct(stats, row_count)
            uniq_pct = get_unique_pct(stats, row_count)
            tags_str = ", ".join(col_data.get("tags", []))
            desc = (col_data.get("description") or "—").replace("\n", " ").replace("|", "\\|")
            md += f"| `{col_name}` | `{col_data.get('original_type', 'N/A')}` | {null_pct}% | {uniq_pct}% | {desc} | {tags_str} |\n"
        md += "\n"

        # Per-table quality notes
        alerts = []
        if hs < 95:
            alerts.append(f"Health score below optimal ({hs}/100)")
        for cn, cm in meta.get("columns", {}).items():
            s = cm.get("stats") or {}
            np = get_null_pct(s, row_count)
            if np > 50:
                alerts.append(f"`{cn}` has critical null rate ({np}%)")
            elif np > 20:
                alerts.append(f"`{cn}` has elevated null rate ({np}%)")
        if alerts:
            md += "**⚠ Quality Notes:**\n"
            for a in alerts:
                md += f"- {a}\n"
            md += "\n"
        md += "---\n\n"

    # ── AI Insights & Recommendations section ──
    md += "## AI Insights & Recommendations\n\n"
    insights = generate_ai_insights(schema_data)
    if insights:
        md += insights + "\n\n"
    else:
        md += "*Insights generation unavailable.*\n\n"

    md += "---\n\n*End of Data Dictionary*\n"
    return md


def run_pipeline(connection_string):
    with st.spinner("Running SchemaDoc AI pipeline — extracting, profiling, enriching..."):
        initial_state = {
            "connection_string": connection_string,
            "retry_count": 0,
            "errors": [],
            "schema_raw": {},
            "schema_enriched": {},
        }
        app = build_pipeline()

        pipeline_log = []
        enrich_count = 0
        final_state = dict(initial_state)

        for event in app.stream(initial_state):
            for node_name, node_output in event.items():
                final_state.update(node_output)

                if node_name == "extract":
                    table_count = len(node_output.get("schema_raw", {}))
                    total_cols = sum(
                        len(t.get("columns", {}))
                        for t in node_output.get("schema_raw", {}).values()
                    )
                    pipeline_log.append({
                        "step": "extract",
                        "status": "success",
                        "message": f"Extracted {table_count} tables, {total_cols} columns with statistical profiling",
                        "icon": "🔬",
                    })
                elif node_name == "enrich":
                    enrich_count += 1
                    pipeline_log.append({
                        "step": "enrich",
                        "status": "success",
                        "message": f"AI enrichment pass {enrich_count} — Gemini analysis with ReAct tool-calling",
                        "icon": "🧠",
                    })
                elif node_name == "validate":
                    v_status = node_output.get("validation_status", "PENDING")
                    v_errors = node_output.get("errors", [])
                    if v_status == "PASSED":
                        pipeline_log.append({
                            "step": "validate",
                            "status": "passed",
                            "message": "Validation PASSED — zero hallucinations, zero data loss",
                            "icon": "✅",
                            "errors": [],
                        })
                    else:
                        pipeline_log.append({
                            "step": "validate",
                            "status": "failed",
                            "message": f"Validation FAILED — {len(v_errors)} integrity violation(s) caught",
                            "icon": "🔄",
                            "errors": v_errors,
                        })

        st.session_state["pipeline_log"] = pipeline_log

        if final_state.get("validation_status") == "PASSED":
            st.session_state["pipeline_result"] = final_state["schema_enriched"]
            st.session_state["db_overview"] = None
            st.session_state["chat_history"] = []
            retry_count = sum(1 for e in pipeline_log if e["step"] == "validate" and e["status"] == "failed")
            if retry_count > 0:
                st.toast(f"Analysis complete! Self-corrected {retry_count} issue(s)", icon="🛡️")
            else:
                st.toast("Analysis complete — clean first pass!", icon="⚡")
        else:
            st.error(f"Pipeline failed after max retries: {final_state.get('errors')}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "pipeline_result" not in st.session_state:
    st.session_state["pipeline_result"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "db_overview" not in st.session_state:
    st.session_state["db_overview"] = None
if "pipeline_log" not in st.session_state:
    st.session_state["pipeline_log"] = []


def generate_db_overview(schema_data):
    """Ask AI to generate a concise database overview paragraph on first load."""
    total_tables = len(schema_data)
    total_cols = sum(len(t.get("columns", {})) for t in schema_data.values())
    total_rows = sum(t.get("row_count", 0) for t in schema_data.values())
    table_names = list(schema_data.keys())
    avg_health = sum(t.get("health_score", 100) for t in schema_data.values()) / total_tables if total_tables else 0
    pii_cols = [f"{t}.{c}" for t, tm in schema_data.items() for c, cm in tm.get("columns", {}).items() if "PII" in (cm.get("tags") or [])]
    fk_pairs = [f"{t}.{fk['column']}→{fk['referred_table']}" for t, tm in schema_data.items() for fk in tm.get("foreign_keys", [])]

    prompt = f"""You are a data documentation expert. Write a concise 3-4 sentence overview paragraph about this database.

FACTS:
- {total_tables} tables, {total_cols} columns, {total_rows:,} total rows
- Tables: {', '.join(table_names)}
- Average health score: {avg_health:.1f}/100
- PII columns detected: {len(pii_cols)} ({', '.join(pii_cols[:8])}{'...' if len(pii_cols)>8 else ''})
- Foreign key relationships: {', '.join(fk_pairs[:10])}

RULES:
1. Start with what domain/purpose this database serves (infer from table/column names).
2. Mention the scale (tables, rows) and key entity relationships.
3. Note any data quality observations (health scores, PII presence).
4. Keep it to ONE paragraph, 3-4 sentences max. No bullet points. No markdown headers."""

    try:
        llm = ChatGoogleGenerativeAI(
            model=AppConfig.GEMINI_MODEL,
            google_api_key=AppConfig.GEMINI_API_KEY,
            temperature=0.3,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"Database contains {total_tables} tables with {total_cols} columns and {total_rows:,} rows."


def generate_ai_insights(schema_data):
    """Ask AI to generate actionable insights and suggestions for the documentation."""
    summary_for_ai = {}
    for table, meta in schema_data.items():
        cols_summary = {}
        for cn, cm in meta.get("columns", {}).items():
            stats = cm.get("stats") or {}
            row_count = meta.get("row_count", 0)
            cols_summary[cn] = {
                "type": cm.get("original_type"),
                "tags": cm.get("tags", []),
                "null_pct": get_null_pct(stats, row_count),
                "unique_pct": get_unique_pct(stats, row_count),
                "description": cm.get("description", "")[:80]
            }
        summary_for_ai[table] = {
            "rows": meta.get("row_count", 0),
            "health": meta.get("health_score", 100),
            "fks": [f"{fk['column']}→{fk['referred_table']}" for fk in meta.get("foreign_keys", [])],
            "columns": cols_summary
        }

    prompt = f"""You are a senior data architect reviewing a database schema. Provide actionable insights.

SCHEMA SUMMARY:
{json.dumps(summary_for_ai, indent=1, cls=DecimalEncoder)}

Generate exactly this structure (plain text, no markdown headers):

1. DATABASE PURPOSE: One sentence describing what this database is for.
2. KEY INSIGHTS (3-5 bullet points): Notable patterns, relationships, data quality observations.
3. RECOMMENDATIONS (3-5 bullet points): Actionable suggestions for data governance, quality improvement, schema optimization, or indexing.
4. PII & COMPLIANCE: One sentence about PII exposure risk and any compliance considerations.

Keep each bullet point to 1 sentence. Be specific — reference actual table/column names."""

    try:
        llm = ChatGoogleGenerativeAI(
            model=AppConfig.GEMINI_MODEL,
            google_api_key=AppConfig.GEMINI_API_KEY,
            temperature=0.2,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("""
    <div class="sd-brand">
        <div class="icon">⚡</div>
        <div class="text">
            <div class="name">SchemaDoc AI</div>
            <div class="sub">Intelligent Data Dictionary</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sd-sep">', unsafe_allow_html=True)

    st.markdown("##### Connect Database")
    mode = st.radio(
        "Source",
        ["Chinook Database (11 Tables)", "Demo Database (3 Tables)"],
        label_visibility="collapsed",
    )
    if "Chinook" in mode:
        conn_str = f"sqlite:///{AppConfig.DATA_DIR / 'chinook.db'}"
    else:
        conn_str = f"sqlite:///{AppConfig.DATA_DIR / 'demo.db'}"

    if st.button("⚡ Analyze Database", type="primary", use_container_width=True):
        run_pipeline(conn_str)

    if st.session_state["pipeline_result"]:
        data_sb = st.session_state["pipeline_result"]
        st.markdown('<hr class="sd-sep">', unsafe_allow_html=True)
        st.markdown("##### Pipeline Results")
        total_t = len(data_sb)
        total_c = sum(len(t.get("columns", {})) for t in data_sb.values())
        avg_h = sum(t.get("health_score", 100) for t in data_sb.values()) / total_t if total_t else 0
        st.metric("Tables Analyzed", total_t)
        st.metric("Total Columns", total_c)
        st.metric("Avg Health Score", f"{avg_h:.1f}")

        st.markdown('<hr class="sd-sep">', unsafe_allow_html=True)
        st.markdown("##### Export")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.download_button(
                "📄 MD",
                data=generate_markdown(data_sb),
                file_name="data_dictionary.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with ec2:
            st.download_button(
                "📦 JSON",
                data=json.dumps(data_sb, indent=2, cls=DecimalEncoder),
                file_name="schema_documentation.json",
                mime="application/json",
                use_container_width=True,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN CONTENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if not st.session_state["pipeline_result"]:
    # ─── LANDING PAGE ───
    st.markdown("""
    <div class="sd-hero">
        <h1>SchemaDoc AI</h1>
        <p>Connect any SQL database. Get an AI-enriched data dictionary with quality scoring,
        knowledge graphs, and natural language querying — automatically.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sd-features">
        <div class="sd-feat">
            <div class="fi">🔬</div>
            <div class="fn">Schema Extraction</div>
            <div class="fd">Dialect-agnostic metadata extraction via SQLAlchemy with deep statistical profiling</div>
        </div>
        <div class="sd-feat">
            <div class="fi">🧠</div>
            <div class="fn">AI Enrichment</div>
            <div class="fd">Gemini-powered semantic analysis with forensic log evidence via ReAct tool-calling agents</div>
        </div>
        <div class="sd-feat">
            <div class="fi">🕸️</div>
            <div class="fn">Knowledge Graph</div>
            <div class="fd">Interactive ER visualization with health-coded nodes and foreign key relationship mapping</div>
        </div>
        <div class="sd-feat">
            <div class="fi">💬</div>
            <div class="fn">NL → SQL</div>
            <div class="fd">Ask questions in plain English and get schema-grounded SQL queries generated instantly</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.info("Select a database from the sidebar and click **Analyze Database** to begin.", icon="👈")

else:
    # ─── DASHBOARD ───
    data = st.session_state["pipeline_result"]

    total_tables = len(data)
    total_cols = sum(len(t.get("columns", {})) for t in data.values())
    total_rows = sum(t.get("row_count", 0) for t in data.values())
    avg_health = (
        sum(t.get("health_score", 100) for t in data.values()) / total_tables
        if total_tables
        else 0
    )
    pii_count = sum(
        1
        for t in data.values()
        for c in t.get("columns", {}).values()
        if "PII" in (c.get("tags") or [])
    )
    fk_count = sum(len(t.get("foreign_keys", [])) for t in data.values())

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "📋 Schema Explorer", "🕸️ Knowledge Graph", "💬 NL → SQL"]
    )

    # ═══════════════════════════════════════
    # TAB 1: OVERVIEW
    # ═══════════════════════════════════════
    with tab1:
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Tables", total_tables)
        k2.metric("Total Columns", total_cols)
        k3.metric("Total Rows", f"{total_rows:,}")
        k4.metric("Avg Health", f"{avg_health:.1f}")
        k5.metric("PII Columns", pii_count, delta="flagged" if pii_count > 0 else None, delta_color="inverse")

        # ── Pipeline Integrity Log ──
        p_log = st.session_state.get("pipeline_log", [])
        if p_log:
            st.markdown("")
            st.markdown('<div class="sd-sec-head">Pipeline Integrity Log</div>', unsafe_allow_html=True)
            retry_hits = [e for e in p_log if e["step"] == "validate" and e["status"] == "failed"]
            total_violations = sum(len(e.get("errors", [])) for e in retry_hits)

            if retry_hits:
                st.markdown(
                    f'<div class="sd-pipeline-summary">'
                    f'<div class="ps-badge ps-retry">🛡️ Anti-Hallucination Guard Active</div>'
                    f'<div class="ps-detail">The deterministic validation gate caught '
                    f'<strong>{total_violations}</strong> integrity violation(s) across '
                    f'<strong>{len(retry_hits)}</strong> failed attempt(s). '
                    f'The pipeline automatically self-corrected via retry loops before the schema passed validation.</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="sd-pipeline-summary">'
                    '<div class="ps-badge ps-clean">✅ Clean First Pass</div>'
                    '<div class="ps-detail">Schema validated on the first attempt — '
                    '<strong>zero hallucinations</strong> and <strong>zero data loss</strong> detected. '
                    'All AI-enriched columns match the deterministic source of truth.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with st.expander(f"View full execution trace ({len(p_log)} steps)", expanded=bool(retry_hits)):
                for entry in p_log:
                    if entry["step"] == "validate" and entry["status"] == "failed":
                        error_html = '<br>'.join('• ' + e for e in entry.get('errors', []))
                        st.markdown(
                            f'<div class="sd-log-entry sd-log-fail">'
                            f'<span class="log-icon">{entry["icon"]}</span>'
                            f'<div class="log-body"><div class="log-msg">{entry["message"]}</div>'
                            f'<div class="log-errors">{error_html}</div></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="sd-log-entry sd-log-ok">'
                            f'<span class="log-icon">{entry["icon"]}</span>'
                            f'<div class="log-body"><div class="log-msg">{entry["message"]}</div></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

        # AI-generated database overview
        st.markdown("")
        if st.session_state["db_overview"] is None:
            with st.spinner("Generating database overview..."):
                st.session_state["db_overview"] = generate_db_overview(data)
        overview_text = st.session_state["db_overview"]
        st.markdown(
            f'<div class="sd-ai-overview">'
            f'<div class="ov-title">🧠 AI Database Overview</div>'
            f'{overview_text}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sd-sec-head">Table Health Overview</div>', unsafe_allow_html=True)

        sorted_tables = sorted(data.items(), key=lambda x: x[1].get("health_score", 100))
        for table_name, meta in sorted_tables:
            hs = meta.get("health_score", 100)
            rc = meta.get("row_count", 0)
            cc = len(meta.get("columns", {}))
            color = health_color(hs)
            bar_w = max(0, min(100, hs))

            st.markdown(
                f"""<div class="sd-trow">
                    <div class="tn">{table_name}</div>
                    <div class="tm">{cc} cols &middot; {rc:,} rows</div>
                    <div class="th">
                        <span style="color:{color};font-weight:700;font-size:14px;">{hs}</span>
                        <span style="color:#4a6077;font-size:12px;">/100</span>
                        <div class="sd-hbar"><div class="fill" style="width:{bar_w}%;background:{color};"></div></div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Data quality alerts
        low_health = [(n, m) for n, m in data.items() if m.get("health_score", 100) < 95]
        if low_health:
            st.markdown("")
            st.markdown('<div class="sd-sec-head">Data Quality Alerts</div>', unsafe_allow_html=True)
            for name, meta in low_health:
                hs = meta.get("health_score", 100)
                high_null_cols = []
                for cn, cm in meta.get("columns", {}).items():
                    null_pct = get_null_pct(cm.get("stats"), meta.get("row_count", 0))
                    if null_pct > 30:
                        high_null_cols.append(f"{cn} ({null_pct}%)")
                detail = (
                    f"High null columns: {', '.join(high_null_cols)}"
                    if high_null_cols
                    else "Multiple minor quality issues detected"
                )
                severity = "sd-alert" if hs < 80 else "sd-alert sd-alert-warn"
                st.markdown(
                    f'<div class="{severity}">⚠ <strong>{name}</strong> — Health: {hs}/100 — {detail}</div>',
                    unsafe_allow_html=True,
                )

    # ═══════════════════════════════════════
    # TAB 2: SCHEMA EXPLORER
    # ═══════════════════════════════════════
    with tab2:
        @st.fragment
        def render_schema_explorer():
            explorer_data = st.session_state["pipeline_result"]
            selected_table = st.selectbox("Select Table", list(explorer_data.keys()))

            if selected_table:
                table_data = explorer_data[selected_table]
                row_count = table_data.get("row_count", 0)
                hs = table_data.get("health_score", 100)
                fks = table_data.get("foreign_keys", [])
                cols = table_data.get("columns", {})

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Rows", f"{row_count:,}")
                m2.metric("Health Score", f"{hs}/100")
                m3.metric("Columns", len(cols))
                m4.metric("Foreign Keys", len(fks))

                if fks:
                    fk_text = " · ".join(
                        [
                            f"`{fk['column']}` → `{fk['referred_table']}.{fk['referred_column']}`"
                            for fk in fks
                        ]
                    )
                    st.markdown(f"**Relationships:** {fk_text}")

                st.markdown('<hr class="sd-sep">', unsafe_allow_html=True)
                st.markdown('<div class="sd-sec-head">Column Details</div>', unsafe_allow_html=True)

                for col_name, col_meta in cols.items():
                    stats = col_meta.get("stats") or {}
                    tags = col_meta.get("tags", [])
                    null_pct = get_null_pct(stats, row_count)
                    uniq_pct = get_unique_pct(stats, row_count)
                    mean_val = stats.get("mean_value")
                    min_val = stats.get("min_value")
                    max_val = stats.get("max_value")
                    samples = stats.get("sample_values", [])
                    desc = col_meta.get("description") or "No description available"
                    original_type = col_meta.get("original_type", "N/A")
                    tags_html = render_tags(tags)

                    with st.expander(f"**{col_name}** — `{original_type}`"):
                        if tags_html:
                            st.markdown(tags_html, unsafe_allow_html=True)
                        st.markdown(f"{desc}")

                        display_mean = f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else "—"
                        display_min = f"{min_val}" if min_val is not None else "—"
                        display_max = f"{max_val}" if max_val is not None else "—"

                        st.markdown(
                            f"""<div class="sd-stat-grid">
                                <div class="sd-stat"><div class="v">{null_pct}%</div><div class="l">Null Rate</div></div>
                                <div class="sd-stat"><div class="v">{uniq_pct}%</div><div class="l">Unique</div></div>
                                <div class="sd-stat"><div class="v">{display_mean}</div><div class="l">Mean</div></div>
                                <div class="sd-stat"><div class="v">{display_min} / {display_max}</div><div class="l">Min / Max</div></div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                        if samples:
                            st.markdown(f"**Samples:** `{'`, `'.join(str(s) for s in samples[:5])}`")

        render_schema_explorer()

    # ═══════════════════════════════════════
    # TAB 3: KNOWLEDGE GRAPH
    # ═══════════════════════════════════════
    with tab3:
        @st.fragment
        def render_knowledge_graph():
            st.markdown(
                '<div class="sd-sec-head">Entity-Relationship Graph</div>',
                unsafe_allow_html=True,
            )
            st.caption("Node size scales with row count. Color indicates health score. Edges represent foreign key relationships.")

            nodes, edges = [], []
            graph_data = st.session_state["pipeline_result"]
            for table_name, meta in graph_data.items():
                hs = meta.get("health_score", 100)
                rc = meta.get("row_count", 0)
                color = health_color(hs)
                size = max(18, min(40, 18 + math.log2(max(rc, 1)) * 2))

                nodes.append(
                    Node(
                        id=table_name,
                        label=f"{table_name}\n({rc:,})",
                        size=size,
                        shape="database",
                        color=color,
                        font={"color": "#000000", "size": 12, "bold": True},
                    )
                )

                for fk in meta.get("foreign_keys", []):
                    if fk["referred_table"] in graph_data:
                        edges.append(
                            Edge(
                                source=table_name,
                                target=fk["referred_table"],
                                label=fk["column"],
                                color="#4a6077",
                                width=1.5,
                            )
                        )

            if nodes:
                config = Config(
                    width=1000,
                    height=550,
                    directed=True,
                    physics=True,
                    hierarchical=False,
                )
                agraph(nodes=nodes, edges=edges, config=config)

            st.markdown(
                """<div class="sd-legend">
                    <div class="sd-legend-item"><div class="sd-legend-dot" style="background:#00ff88"></div> Health ≥ 90</div>
                    <div class="sd-legend-item"><div class="sd-legend-dot" style="background:#ffb800"></div> Health 70–89</div>
                    <div class="sd-legend-item"><div class="sd-legend-dot" style="background:#ff4d6d"></div> Health &lt; 70</div>
                    <div class="sd-legend-item"><span style="color:#4a6077">──→</span> Foreign Key</div>
                </div>""",
                unsafe_allow_html=True,
            )

        render_knowledge_graph()

    # ═══════════════════════════════════════
    # TAB 4: NL2SQL CHAT
    # ═══════════════════════════════════════
    with tab4:
        @st.fragment
        def render_chat():
            chat_data = st.session_state["pipeline_result"]

            # Example query suggestion chips (above the chat)
            if not st.session_state.chat_history:
                st.markdown(
                    '<div class="sd-sec-head">Natural Language → SQL</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Ask questions about the database in plain English. Responses are grounded in the AI-enriched schema context."
                )
                st.markdown("**Try asking:**")
                eq1, eq2, eq3 = st.columns(3)
                with eq1:
                    if st.button("Top 5 customers by spending", use_container_width=True):
                        st.session_state["_eq"] = "Show the top 5 customers by total spending"
                        st.rerun(scope="fragment")
                with eq2:
                    if st.button("Which genre has most tracks?", use_container_width=True):
                        st.session_state["_eq"] = "Which genre has the most tracks?"
                        st.rerun(scope="fragment")
                with eq3:
                    if st.button("List all PII columns", use_container_width=True):
                        st.session_state["_eq"] = "List all columns flagged as PII across every table"
                        st.rerun(scope="fragment")

            # Chat message history (scrollable container)
            chat_container = st.container(height=500)
            with chat_container:
                for msg in st.session_state.chat_history:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    with st.chat_message(role):
                        st.markdown(msg.content)

            # Chat input — always at bottom
            user_query = st.chat_input("Ask about your schema or request SQL queries...")
            if not user_query and "_eq" in st.session_state:
                user_query = st.session_state.pop("_eq")

            if user_query:
                # Immediately show user message
                st.session_state.chat_history.append(HumanMessage(content=user_query))
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(user_query)

                    # Show assistant thinking indicator then stream response
                    with st.chat_message("assistant"):
                        context_json = json.dumps(chat_data, cls=DecimalEncoder)
                        system_prompt = f"""You are a Senior Database Architect and SQL Expert.

SCHEMA CONTEXT (AI-enriched data dictionary):
{context_json}

DIRECTIVES:
1. If the user asks a natural language question about the data, generate the EXACT SQL query needed.
2. Output SQL in a ```sql code block.
3. Briefly explain the query logic referencing the schema descriptions and relationships.
4. All JOINs must use the exact foreign key relationships from the schema context.
5. If asked about schema metadata (PII columns, health scores, etc.), answer from context directly.
6. Be concise and precise."""
                        try:
                            llm = ChatGoogleGenerativeAI(
                                model=AppConfig.GEMINI_MODEL,
                                google_api_key=AppConfig.GEMINI_API_KEY,
                                temperature=0,
                            )
                            messages = [SystemMessage(content=system_prompt)] + st.session_state.chat_history
                            with st.spinner("Thinking..."):
                                response = llm.invoke(messages)
                            st.markdown(response.content)
                            st.session_state.chat_history.append(response)
                        except Exception as e:
                            error_msg = f"Error: {e}"
                            st.markdown(error_msg)
                            st.session_state.chat_history.append(AIMessage(content=error_msg))

        render_chat()
