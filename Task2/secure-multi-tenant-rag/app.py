import os
import streamlit as st
from dotenv import load_dotenv

from src.ingestion import extract_pdf_chunks
from src.retrieval import VectorRetriever
from src.reranking import DocumentReranker
from src.query_rewriting import QueryRewriter
from src.rag_pipeline import SecureRAGPipeline

load_dotenv()

st.set_page_config(page_title="Enterprise Secure Multi-Tenant RAG", layout="wide")

st.title("🔒 Enterprise Multi-Tenant RAG with RBAC")
st.markdown("Search enterprise knowledge base strictly bounded by active clearance and tenant permissions.")

# Pipeline Cache / Initialization
@st.cache_resource
def get_pipeline():
    retriever = VectorRetriever()
    reranker = DocumentReranker()
    rewriter = QueryRewriter()
    pipeline = SecureRAGPipeline(retriever=retriever, reranker=reranker, rewriter=rewriter)
    return retriever, pipeline

retriever, pipeline = get_pipeline()

# Sidebar: User Authentication Context Simulation
st.sidebar.header("🔑 Simulated User Identity")
tenant_id = st.sidebar.selectbox("Tenant ID", ["client_a", "client_b"])
department = st.sidebar.selectbox("Department", ["HR", "Finance", "IT"])
clearance_level = st.sidebar.slider("Clearance Level", min_value=1, max_value=5, value=2)
user_id = st.sidebar.text_input("User ID", "user_101")

user_identity = {
    "user_id": user_id,
    "tenant_id": tenant_id,
    "department": department,
    "clearance_level": clearance_level
}

st.sidebar.markdown("---")
st.sidebar.header("📁 Document Ingestion")

# Helper block for quick PDF upload and indexing
uploaded_file = st.sidebar.file_uploader("Ingest Document", type=["pdf"])
if uploaded_file:
    ingest_tenant = st.sidebar.selectbox("Doc Tenant ID", ["client_a", "client_b"], key="ing_tenant")
    ingest_dept = st.sidebar.selectbox("Doc Department", ["HR", "Finance", "IT"], key="ing_dept")
    ingest_clearance = st.sidebar.slider("Doc Security Clearance", 1, 5, 2, key="ing_clear")

    if st.sidebar.button("Process & Index PDF"):
        os.makedirs("temp_uploads", exist_ok=True)
        temp_path = os.path.join("temp_uploads", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        chunks = extract_pdf_chunks(
            pdf_path=temp_path,
            tenant_id=ingest_tenant,
            department=ingest_dept,
            clearance_level=ingest_clearance
        )
        retriever.add_documents(chunks)
        st.sidebar.success(f"Successfully indexed {len(chunks)} chunks into vector store.")

# Main Interface
st.subheader(f"Active Identity: `{tenant_id}` | `{department}` | Clearance Level: `{clearance_level}`")

query = st.text_input("Ask a question about enterprise policies:")

if st.button("Search & Generate Answer"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Rewriting query, enforcing RBAC, retrieving & reranking..."):
            result = pipeline.run(query=query, user=user_identity)

        st.markdown("### Answer")
        st.write(result["answer"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Query Rewriter Output:**")
            st.info(result["rewritten_query"])
        with col2:
            st.markdown("**Verified Source Citations:**")
            if result["citations"]:
                for cite in result["citations"]:
                    st.write(f"- `{cite}`")
            else:
                st.write("No citations available.")