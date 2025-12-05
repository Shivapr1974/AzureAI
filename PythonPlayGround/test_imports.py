import langchain
from langchain_openai import ChatOpenAI, OpenAI
from openai import OpenAI
from regex import M
# from langchain_ollama import ChatOllama
print("OK:", langchain.__version__)

# Lang Chain example
# llm = ChatOpenAI(model="gpt-4o-mini")  # needs OPENAI_API_KEY
# output = llm.invoke("Write a one-sentence bedtime story about a unicorn.")
# print(output)

# # OpenAI example
client = OpenAI()
pythonFile = open("python/HelloWorld.py", "r")
pythonArr = pythonFile.readlines();

response = client.completions.create(
    model="gpt-4o-mini",
    prompt="Convert to Java file. Do not include extra text as I will save it as .java Do not add too many blank lines" + str(pythonArr),
    max_tokens=1000
)
javaFile = open("pythontojava/HelloWorld.java", "w")
javaFile.write(response.choices[0].text);
