# app.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from src.rag_pipeline import ask_llm_with_search

app = FastAPI()
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Azure RAG Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                background: #f5f5f5;
                display: flex;
                flex-direction: column;                
                min-height: 100vh;        /* safer than strict 100vh */
            }
            #chat-container {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
            }
            .message {
                max-width: 70%;
                padding: 4px 8px;
                border-radius: 10px;
                margin-bottom: 1px;
                line-height: 1.22;
            }
            .user {
                background: #0066ff;
                color: white;
                margin-left: auto;
            }
            .user {
                padding: 6px 10px !important;
            }
            .bot {
                background: #ffffff;
                color: #111;
                border: 1px solid #ddd;
                margin-right: auto;
            }
            .bot {
                padding: 6px 10px !important; 
            }
            #input-area {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ddd;
                background: white;
            }
            #input-area input {
                flex: 1;
                padding: 10px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            #input-area button {
                margin-left: 8px;
                padding: 10px 16px;
                font-size: 14px;
                border-radius: 6px;
                border: none;
                background: #0078d4;
                color: white;
                cursor: pointer;
            }

            #spinner {
                position: fixed;
                bottom: 18%;              /* higher than before – adjust 16–22% as you like */
                left: 50%;
                transform: translateX(-50%);
                z-index: 1000;
                display: none;
                font-size: 30px;
                text-align: center;
                background: #ffffff;       /* white background */
                padding: 8px 16px;
                border-radius: 16px;       /* pill look */
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                # animation: pulse 1.2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 0.3; }
                50% { opacity: 1; }
                100% { opacity: 0.3; }
            }
            /* Reduce heading spacing */
            .message h1, 
            .message h2, 
            .message h3, 
            .message h4 {
                margin-top: 6px;
                margin-bottom: 1px;
            }

            /* Remove giant margins between paragraphs */
            .message p {
                margin: 4px 0;
            }

            /* Reduce bullet list spacing */
            .message ul, 
            .message ol {
                margin-top: 4px !important;
                margin-bottom: 1px !important;
                padding-left: 20px;
            }

            /* Reduce spacing inside nested bullets */
            .message li {
                margin-bottom: 1px !important;
            }

            /* Remove extra gap before nested lists */
            .message li ul {
                margin-top: 2px !important;
            }

            /* Optional: tighten everything slightly */
            .message {
                line-height: 1.25;
            }
            /* Mobile adjustments */
            @media (max-width: 600px) {
                #input-area {
                    position: fixed;
                    bottom: 2%;        /* <-- raise it 10% above bottom */
                    left: 0;
                    right: 0;
                    z-index: 999;
                    background: white;
                    padding: 10px;
                    border-top: 1px solid #ddd;
                    display: flex;
                    gap: 8px;
                    border-radius: 12px 12px 0 0; /* nice rounded top */
                }

                body {
                    padding-bottom: 20%; /* prevent chat messages from hiding behind it */
                }

                #input-area input {
                    font-size: 18px;
                    padding: 12px;
                }

                #input-area button {
                    font-size: 18px;
                    padding: 12px 20px;
                    border-radius: 8px;
                }
            }

        </style>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        
    </head>
    <body>
        <div id="chat-container"></div>

        <div id="spinner">⏳ Thinking...</div>

        <div id="input-area">
            <input id="user-input" type="text" placeholder="Ask something about Azure..." />
            <button id="send-btn" onclick="sendMessage()">Send</button>
        </div>

        <script>
            const chatContainer = document.getElementById("chat-container");
            const spinner = document.getElementById("spinner");
            const userInput = document.getElementById("user-input");
            const sendBtn = document.getElementById("send-btn");

            function appendMessage(text, sender) {
                const div = document.createElement("div");
                div.classList.add("message", sender);
                div.innerHTML = marked.parse(text);
                chatContainer.appendChild(div);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            async function sendMessage() {
                const text = userInput.value.trim();
                if (!text) return;

                appendMessage(text, "user");
                userInput.value = "";
                userInput.focus();

                // Disable inputs + show spinner
                sendBtn.disabled = true;
                userInput.disabled = true;
                spinner.style.display = "block";

                try {
                    const res = await fetch("/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ question: text })
                    });

                    const data = await res.json();
                    appendMessage(data.answer || "No response.", "bot");
                } catch (err) {
                    appendMessage("❌ Error: " + err, "bot");
                } finally {
                    // Re-enable inputs + hide spinner
                    spinner.style.display = "none";
                    sendBtn.disabled = false;
                    userInput.disabled = false;
                }
            }

            // Enter key
            userInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    sendMessage();
                }
            });

            appendMessage("Hi! I'm your Azure Cloud Assistant developed by Sivakumar Ramakrishnan. Ask me anything.", "bot");
        </script>
    </body>
    </html>
    """


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return {"answer": "Please enter a question."}

    answer = ask_llm_with_search(question)
    return {"answer": answer}
