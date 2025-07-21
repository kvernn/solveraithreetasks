import streamlit as st
import json
from workflow_generator import generate_workflow
from streamlit_agraph import agraph, Node, Edge, Config

def create_visual_graph(workflow_json):
    """
    Parses the workflow JSON and creates a visual graph.
    """
    nodes = []
    edges = []

    if "nodes" in workflow_json:
        for node_data in workflow_json["nodes"]:
            nodes.append(Node(id=node_data["name"], label=node_data["name"], shape="box"))

    if "connections" in workflow_json:
        for conn_data in workflow_json["connections"]:
            edges.append(Edge(source=conn_data["source"], target=conn_data["target"]))

    config = Config(width=750, height=300, directed=True, physics=True, hierarchical=False)

    return agraph(nodes=nodes, edges=edges, config=config)

st.set_page_config(page_title="Agentic Flow Builder", page_icon="🤖", layout="wide")

st.title("🤖 Agentic AI Flow Builder")
st.write("Describe the automation you want to build in plain English.")

# --- Initialize Session State ---
if "summary" not in st.session_state:
    st.session_state.summary = None
if "workflow" not in st.session_state:
    st.session_state.workflow = None

user_query = st.text_area("Your Automation Request:", height=100, placeholder="e.g., When a Jotform is submitted, send a WhatsApp to +123 and an email to my admin.")

if st.button("Generate Workflow"):
    if user_query:
        with st.spinner("🤖 The meta-agent is thinking and building..."):
            summary, workflow = generate_workflow(user_query)
            st.session_state.summary = summary
            st.session_state.workflow = workflow
    else:
        st.warning("Please enter a description of the workflow you want to build.")

# --- Display the Outputs ---
if st.session_state.summary:
    st.subheader("✅ Agent's Understanding")
    for step in st.session_state.summary:
        st.write(f"- {step}")

if st.session_state.workflow:
    st.subheader("✨ Visual Workflow")
    create_visual_graph(st.session_state.workflow)

    st.subheader("⚙️ n8n Workflow JSON")
    st.json(st.session_state.workflow)

    st.download_button(
        label="Download as n8n.json",
        data=json.dumps(st.session_state.workflow, indent=2),
        file_name="workflow.n8n.json",
        mime="application/json"
    )