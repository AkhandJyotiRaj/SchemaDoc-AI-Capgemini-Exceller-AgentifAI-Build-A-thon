import streamlit as st
import sys
import json
from pathlib import Path
from decimal import Decimal
from streamlit_agraph import agraph, Node, Edge, Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.config import AppConfig
from src.pipeline.graph import build_pipeline
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="SchemaDoc AI", layout="wide")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

if "pipeline_result" not in st.session_state:
    st.session_state["pipeline_result"] = None

def generate_markdown(schema_data: dict) -> str:
    md = "# Enterprise Data Dictionary\n\n"
    for table, meta in schema_data.items():
        md += f"## Table: `{table}`\n"
        md += f"**Rows:** {meta.get('row_count')} | **Health Score:** {meta.get('health_score')}/100\n\n"
        md += "| Column | Type | Null % | Unique % | Description | Tags |\n"
        md += "|---|---|---|---|---|---|\n"
        for col_name, col_data in meta.get("columns", {}).items():
            stats = col_data.get("stats") or {}
            tags = ", ".join(col_data.get("tags", []))
            desc = col_data.get("description", "N/A").replace("\n", " ")
            md += f"| `{col_name}` | {col_data['original_type']} | {stats.get('null_percentage', 0)}% | {stats.get('unique_percentage', 0)}% | {desc} | {tags} |\n"
        md += "\n---\n"
    return md

def run_pipeline(connection_string):
    with st.spinner("Analyzing database..."):
        initial_state = {
            "connection_string": connection_string,
            "retry_count": 0,
            "errors": [],
            "schema_raw": {},
            "schema_enriched": {}
        }
        app = build_pipeline()
        final_state = app.invoke(initial_state)
        
        if final_state.get("validation_status") == "PASSED":
            st.session_state["pipeline_result"] = final_state["schema_enriched"]
            st.success("Analysis Complete.")
        else:
            st.error(f"Pipeline Failed: {final_state.get('errors')}")

with st.sidebar:
    st.title("Connect")
    mode = st.radio("Database Source", ["Chinook (11 Tables)", "Simple Demo (3 Tables)"])
    if mode == "Chinook (11 Tables)":
        conn_str = f"sqlite:///{AppConfig.DATA_DIR / 'chinook.db'}"
    else:
        conn_str = f"sqlite:///{AppConfig.DATA_DIR / 'demo.db'}"
    
    if st.button("Analyze Database", type="primary"):
        run_pipeline(conn_str)

st.title("SchemaDoc AI")

if st.session_state["pipeline_result"]:
    data = st.session_state["pipeline_result"]
    tab1, tab2, tab3 = st.tabs(["📊 Schema Documentation", "🕸️ Knowledge Graph", "💬 NL2SQL Chat"])
    
    with tab1:
        st.download_button(
            label="Download Markdown Dictionary",
            data=generate_markdown(data),
            file_name="data_dictionary.md",
            mime="text/markdown"
        )
        
        selected_table = st.selectbox("Select Table", list(data.keys()))
        if selected_table:
            table_data = data[selected_table]
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", table_data.get("row_count", 0))
            c2.metric("Health Score", f"{table_data.get('health_score', 100)}/100")
            c3.metric("Columns", len(table_data.get("columns", [])))
            
            for col_name, col_meta in table_data.get("columns", {}).items():
                with st.expander(f"**{col_name}** ({col_meta['original_type']})"):
                    st.markdown(f"**Description:** {col_meta.get('description', 'N/A')}")
                    stats = col_meta.get("stats", {})
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.write(f"**Null %:** {stats.get('null_percentage', 0)}")
                    sc2.write(f"**Unique %:** {stats.get('unique_percentage', 0)}")
                    sc3.write(f"**Mean:** {stats.get('mean_value', 'N/A')}")
                    sc4.write(f"**Min/Max:** {stats.get('min_value', 'N/A')} / {stats.get('max_value', 'N/A')}")

    with tab2:
        nodes, edges = [], []
        for table_name, meta in data.items():
            health = meta.get("health_score", 100)
            color = "#00C853" if health > 90 else "#FFD600" if health > 70 else "#D50000"
            nodes.append(Node(id=table_name, label=table_name, size=25, shape="database", color=color))
            for fk in meta.get("foreign_keys", []):
                if fk["referred_table"] in data:
                    edges.append(Edge(source=table_name, target=fk["referred_table"], label=fk["column"]))
        
        if nodes:
            config = Config(width=800, height=600, directed=True, physics=True, hierarchical=False)
            agraph(nodes=nodes, edges=edges, config=config)

    with tab3:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.write(msg.content)

        user_query = st.chat_input("Ask for SQL queries or schema details...")
        if user_query:
            st.session_state.chat_history.append(HumanMessage(content=user_query))
            with st.chat_message("user"):
                st.write(user_query)
            
            with st.chat_message("assistant"):
                context_json = json.dumps(data, cls=DecimalEncoder)
                system_prompt = f"""
                You are a Senior SQL Developer and Database Architect.
                SCHEMA CONTEXT:
                {context_json}
                
                DIRECTIVES:
                1. If the user asks a natural language question about the data, generate the exact SQL query required to answer it.
                2. Output the SQL query in a markdown ```sql block.
                3. Briefly explain the query logic using the schema descriptions.
                4. Ensure all foreign key joins are strictly accurate based on the provided schema.
                """
                
                llm = ChatGoogleGenerativeAI(
                    model=AppConfig.GEMINI_MODEL,
                    google_api_key=AppConfig.GEMINI_API_KEY,
                    temperature=0
                )
                
                messages = [SystemMessage(content=system_prompt)] + st.session_state.chat_history
                response = llm.invoke(messages)
                st.write(response.content)
                st.session_state.chat_history.append(response)