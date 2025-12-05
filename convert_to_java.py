from openai import OpenAI

client = OpenAI()

with open("python/HelloWorld.py", "r", encoding="utf-8") as f:
    code = f.read()

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": f"""
                Convert the following Python file into Java called HellowWorld.java.
                Do not include extra text as I will save it as .java Do not add too many blank
                Do not add ```java and ``` to the end. Make it pure java code.
                Python code:
                {code}
                """
                        }
                    ],
                    temperature=0,
                    max_tokens=4000
)

javaFile = open("pythontojava/HelloWorld.java", "w")

javaCode = resp.choices[0].message.content
javaFile.write(str(javaCode));
