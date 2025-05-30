import streamlit as st
import os
from tempfile import NamedTemporaryFile
from agentic_doc.parse import parse_documents
from collections import defaultdict


st.set_page_config(page_title="PDF Parser Demo", layout="wide")

# Sidebar - API Key input (optional, depends on your library needs)
st.sidebar.header("Configuration")

# VISION_AGENT_API_KEY = st.sidebar.text_input("Enter API Key", type="password")  # You can remove this if not needed
VISION_AGENT_API_KEY = st.secrets.get("VISION_AGENT_API_KEY")


# Sidebar - File uploader
uploaded_file = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])

st.title("Agentic PDF Extractor App")
st.markdown("Upload a PDF from the sidebar to extract and view its contents page-wise.")

# If a file is uploaded
if uploaded_file:

    proceed = st.sidebar.button("Proceed")  # Button appears after file upload

    if proceed:

        # Save uploaded file to a temp location
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_pdf_path = tmp_file.name

        # Parse the PDF using agentic_doc
        with st.spinner("Parsing PDF..."):
            try:
                results = parse_documents([tmp_pdf_path])
                parsed_doc = results[0]
                parsed_chunks = parsed_doc.chunks

                with st.expander("Show Original Parsed Chunks"):
                    st.write(parsed_chunks)

                with st.expander("Modified Parsed Chunks (text, page, type)"):
                        for idx, chunk in enumerate(parsed_chunks):
                            text = chunk.text
                            try:
                                page = chunk.grounding[0].page + 1
                            except Exception:
                                page = "N/A"
                            chunk_type = str(chunk.chunk_type.value) if hasattr(chunk.chunk_type, "value") else str(chunk.chunk_type)
                            
                            st.write(f"**Chunk {idx+1}:**")
                            st.write(f"- **Page:** {page}")
                            st.write(f"- **Type:** {chunk_type}")
                            if chunk_type == "table" and "<table" in text:
                                st.markdown(text, unsafe_allow_html=True)
                            else:
                                st.write(f"- **Text:**\n{text}")
                            st.markdown("---")


            except Exception as e:
                st.error(f"Error parsing document: {e}")
                st.stop()
        


        # Group text chunks by page number
        chunks_by_page = defaultdict(list)
        for chunk in parsed_chunks:
            try:
                page_num = chunk.grounding[0].page
            except Exception:
                page_num = 0  # fallback if page info not present
            chunks_by_page[page_num].append(chunk.text)

        # Combine all chunks for each page
        st.markdown("Content of each pages: ")
        merged_chunks = {}

        for page, texts in chunks_by_page.items():
            merged_chunks[page] = "\n\n".join(texts)

        # Show as expandable sections per page
        for page, text in sorted(merged_chunks.items()):
            with st.expander(f"Page {page + 1}"):
                st.write(text)

        # # Optionally, show full Markdown content (from .markdown)
        # with st.expander("Show Raw Markdown Content"):
        #     st.write(parsed_doc.markdown)

        st.write("chatbot, coming soon...")

    else:
        st.info("Click 'Proceed' in the sidebar to parse and display PDF content.")
    
else:
    st.info("Upload a PDF file from the sidebar to see extracted content.")

