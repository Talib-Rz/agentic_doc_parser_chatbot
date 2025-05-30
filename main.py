import streamlit as st
import os
from tempfile import NamedTemporaryFile
from agentic_doc.parse import parse_documents
from collections import defaultdict



from fpdf import FPDF
import io
from bs4 import BeautifulSoup
import os

VISION_AGENT_API_KEY = st.secrets.get("VISION_AGENT_API_KEY")
FONT_PATH = "DejaVuSans.ttf"  # Make sure this file is in the same directory

def add_table_to_pdf(pdf, table_html):
    soup = BeautifulSoup(table_html, "html.parser")
    table = soup.find("table")
    if not table:
        return

    # Extract headers
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    # Extract rows
    rows = []
    for tr in table.find_all("tr"):
        row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if row:
            rows.append(row)

    # Render headers
    if headers:
        pdf.set_font("DejaVu", "B", 8)
        for header in headers:
            pdf.cell(40, 10, header, border=1)
        pdf.ln()
    # Render rows
    pdf.set_font("DejaVu", "", 8)
    for row in rows[1:]:  # skip header row
        for cell in row:
            pdf.cell(40, 10, cell, border=1)
        pdf.ln()
    pdf.ln(2)

def create_pdf_from_chunks(parsed_chunks):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)
    pdf.set_font("DejaVu", size=8)

    for idx, chunk in enumerate(parsed_chunks):
        text = chunk.text
        try:
            page = chunk.grounding[0].page + 1
        except Exception:
            page = "N/A"
        chunk_type = str(chunk.chunk_type.value) if hasattr(chunk.chunk_type, "value") else str(chunk.chunk_type)

        pdf.set_font("DejaVu", "B", 8)
        pdf.cell(0, 10, f"Chunk {idx+1}:", ln=True)
        pdf.set_font("DejaVu", "", 8)
        pdf.cell(0, 10, f"Page: {page}", ln=True)
        pdf.cell(0, 10, f"Type: {chunk_type}", ln=True)

        if chunk_type == "table" and "<table" in text:
            pdf.set_font("DejaVu", "B", 8)
            pdf.cell(0, 8, "Table:", ln=True)
            add_table_to_pdf(pdf, text)
        else:
            pdf.set_font("DejaVu", "", 8)
            pdf.multi_cell(0, 10, f"Text:\n{text}")

        pdf.ln(2)
        pdf.cell(0, 5, "-" * 50, ln=True)
        pdf.ln(5)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

st.set_page_config(page_title="PDF Parser Demo", layout="wide")

# Sidebar - API Key input (optional, depends on your library needs)
st.sidebar.header("Configuration")


# Sidebar - File uploader
uploaded_file = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])

st.title("Agentic PDF Extractor ~Andrew Ng")
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
                st.session_state["parsed_chunks"] = parsed_chunks

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
    

    if "parsed_chunks" in st.session_state and st.session_state["parsed_chunks"]:
        if st.button("Download Modified Chunks as PDF"):
            pdf_file = create_pdf_from_chunks(st.session_state["parsed_chunks"])
            st.download_button(
                label="Click to Download PDF",
                data=pdf_file,
                file_name="parsed_chunks.pdf",
                mime="application/pdf"
            )


else:
    st.info("Upload a PDF file from the sidebar to see extracted content.")


