from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever



# 1️⃣ Connect to Chroma vector DB
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma(embedding_function=embeddings, persist_directory="chroma_store_csv")


# 2️⃣ Base retriever
base_retriever = vectordb.as_retriever(search_kwargs={"k": 2})

# 3️⃣ LLM to generate multiple query variations
llm = ChatOpenAI(model="gpt-4o-mini")

# 4️⃣ Multi-query retriever
retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

# 5️⃣ Query your data
query = "Developers"
docs = retriever.invoke(query)

print(f"Found {len(docs)} relevant chunks\n")
for i, doc in enumerate(docs[:3], 1):
    print(f"Result {i}:\n{doc.page_content[:250]}\n")
