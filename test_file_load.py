from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    Docx2txtLoader
)

# Folder: D:\Langchain\python\loadfiles\
pdf_loader = PyPDFLoader("loadfiles/sample.pdf")
csv_loader = CSVLoader("loadfiles/sample.csv")
docx_loader = Docx2txtLoader("loadfiles/sample.docx")

# Load all files
pdf_docs = pdf_loader.load()
csv_docs = csv_loader.load()
docx_docs = docx_loader.load()

# Combine into one list
all_docs = pdf_docs + csv_docs + docx_docs

print(f"Loaded {len(all_docs)} documents total")
print("First 200 chars:\n", all_docs[0].page_content[:200])
