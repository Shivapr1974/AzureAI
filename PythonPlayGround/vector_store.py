from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1) Load CSV (one Document per row)
loader = CSVLoader(file_path="loadfiles/sample.csv", encoding="utf-8")
docs = loader.load()

# (Optional) Split long rows into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# 2) Create embeddings
emb = OpenAIEmbeddings(model="text-embedding-3-small")

# 3) Create / persist Chroma DB on disk
persist_dir = "chroma_store_csv"
vectordb = Chroma.from_documents(
    documents=chunks,
    embedding=emb,
    persist_directory=persist_dir,
)
vectordb.persist()
print(f"Saved {len(chunks)} chunks to Chroma at {persist_dir}")

# 4) Reload later (example)
vectordb = Chroma(
    embedding_function=emb,
    persist_directory=persist_dir,
)

# 5) Do a similarity search
results = vectordb.similarity_search("find rows about Shiva", k=3)
for i, doc in enumerate(results, 1):
    print(f"\nResult {i}:\n", doc.page_content[:300])


# 2️⃣ Create retriever from the vector DB
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# 3️⃣ Query the retriever
query = "Quazi"
relevant_docs = retriever.invoke(query) # LEGACY retriever.get_relevant_documents(query)

# 4️⃣ Display results
for i, doc in enumerate(relevant_docs, 1):
    print(f"\nResult invoke {i}:\n", doc.page_content[:300])