import os
import json
import requests
import time
from openai import OpenAI
from pypdf import PdfReader
from bs4 import BeautifulSoup
import gradio as gr
from dotenv import load_dotenv
from bytez import Bytez

# Load .env
load_dotenv()

# ============================
# Utility Functions
# ============================

def push(text):
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            }
        )
    except Exception as e:
        print("Push error:", e)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Unknown question logged: {question}")
    return {"recorded": "ok"}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Record user contact details so Terry can follow up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["email", "name"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Record a question that could not be answered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
            }
        }
    }
]


def get_website_content(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        lines = [t.strip() for t in soup.get_text().splitlines() if t.strip()]
        return "\n".join(lines)
    except:
        return ""


# ============================
# Terry Bot
# ============================

class TerryBot:

    def __init__(self):
        # OpenRouter Client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.name = "Terry Mathew"
        
        # Initialize Bytez SDK (Optional backup)
        self.bytez_key = os.getenv("BYTEZ_KEY")
        if self.bytez_key:
            self.bytez_sdk = Bytez(self.bytez_key)
        else:
            self.bytez_sdk = None

        # Load Summary
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except:
            self.summary = "Summary not available."

        # Load LinkedIn PDF
        try:
            reader = PdfReader("me/linkedin.pdf")
            self.linkedin = "".join(page.extract_text() or "" for page in reader.pages)
        except:
            self.linkedin = "LinkedIn profile not available."

        # Website
        self.website_content = get_website_content("https://www.terrymathew.com")


    # ============================
    # UPDATED SYSTEM PROMPT (CONTACT FLOW)
    # ============================

    def system_prompt(self):
        return f"""
You are acting as {self.name}. Speak naturally, professionally, and in first person.
Use ONLY the Summary, LinkedIn Profile, and Website Content as your information source.
If you do not know something, admit it politely and call `record_unknown_question`.
========================================
CONTACT & FOLLOW-UP RULES
========================================
If a user expresses interest in contacting me for any reason — job prospects, collaboration, questions, networking, etc. — follow this flow:
1. Ask the user to provide:
   - Their **name**
   - Their **email**
   - Their **phone number (optional)**
   - A **short note** about what they want to discuss
2. If the user gives partial details, ask politely for the missing items.
3. Once you have:
   - name
   - email
   - note (with phone if provided)
   Confirm with:
   “Just to confirm:
    • Name: …
    • Email: …
    • Phone: …
    • Note: …
    Would you like me to save this so I can follow up?”
4. ONLY after explicit user confirmation:
   - Use the `record_user_details` tool
   - Combine phone number into the notes field if provided
5. NEVER say “I will email you.”
   Instead say:
   “I can save your details so I can follow up.”
========================================
### Summary
{self.summary}
### LinkedIn Profile
{self.linkedin}
### Website Content
{self.website_content}
"""


    # ============================
    # TOOL HANDLER
    # ============================

    def handle_tool_call(self, calls):
        results = []
        for c in calls:
            fn = c.function.name
            args = json.loads(c.function.arguments)
            if fn == "record_user_details":
                out = record_user_details(**args)
            else:
                out = record_unknown_question(**args)

            results.append({
                "role": "tool",
                "tool_call_id": c.id,
                "content": json.dumps(out)
            })
        return results



    def generate_response_bytez(self, messages):
        """
        Uses Bytez SDK to generate a response.
        Note: This does not currently support the tool calling flow used in the main chat method.
        """
        if not self.bytez_sdk:
            return "Error: Bytez SDK not initialized. Please set BYTEZ_KEY in .env."

        try:
            # choose Qwen3-1.7B
            model = self.bytez_sdk.model("Qwen/Qwen3-1.7B")
            
            output, error = model.run(messages)
            
            if error:
                 return f"Bytez Error: {error}"
            return output
        except Exception as e:
            return f"Bytez Exception: {e}"

    def chat(self, message, history):

        formatted_history = [
            {"role": h["role"], "content": h["content"]} for h in history
        ]

        messages = [
            {"role": "system", "content": self.system_prompt()},
            *formatted_history,
            {"role": "user", "content": message}
        ]

        print("Sending request to OpenRouter...")
        start_time = time.perf_counter()

        # OpenRouter (OpenAI-compatible) loop to resolve tools
        while True:
            try:
                response = self.client.chat.completions.create(
                    model="mistralai/kodestral-2501", # Devstral / Codestral
                    messages=messages,
                    tools=TOOLS,
                )

                end_time = time.perf_counter()
                latency = end_time - start_time
                print(f"OpenRouter Latency: {latency:.4f} seconds")

                choice = response.choices[0]

                if choice.finish_reason == "tool_calls":
                    results = self.handle_tool_call(choice.message.tool_calls)
                    messages.append(choice.message)
                    messages.extend(results)
                    # Reset timer for subsequent calls in the loop if needed, or accumulation
                    continue

                reply = choice.message.content
                return reply
            
            except Exception as e:
                return f"OpenRouter Error: {e}"


# ============================
# Gradio UI
# ============================

bot = TerryBot()

iface = gr.ChatInterface(
    fn=bot.chat,
    title="Chat with Terry's AI",
    description="Ask me anything about Terry's experience, skills, and background."
)

iface.launch()
