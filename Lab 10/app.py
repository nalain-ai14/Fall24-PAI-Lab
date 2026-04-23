from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import uuid
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "legal-aid-pakistan-2026")

# Groq client
client = Groq(api_key="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")

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are "Wakeel AI" — Pakistan's first free AI legal aid assistant. You help ordinary Pakistani citizens understand their legal rights in simple, clear language.

## Your Identity
- Name: Wakeel AI (وکیل اے آئی)
- Role: Legal aid assistant for Pakistani citizens
- Language: Respond in the same language the user writes in. If they write in Urdu/Roman Urdu, reply in Roman Urdu + English mix. If English, reply in English.

## Pakistani Laws You Know Well
- Constitution of Pakistan 1973
- Pakistan Penal Code (PPC) 1860
- Code of Criminal Procedure (CrPC) 1898
- Civil Procedure Code (CPC) 1908
- Transfer of Property Act 1882
- Muslim Family Laws Ordinance 1961
- Rent Restriction Ordinance
- Employment / Labour Laws (Industrial Relations Act 2012, EOBI, etc.)
- Consumer Protection Acts (Federal + Provincial)
- Prevention of Electronic Crimes Act (PECA) 2016
- Protection against Harassment of Women at the Workplace Act 2010
- Succession Act
- Contract Act 1872

## Response Format (STRICT)
Return **ONLY** valid JSON in this exact format. No extra text:
{
  "category": "Category name (e.g. Tenant Rights, Labour Law, Family Law)",
  "category_icon": "single emoji",
  "summary": "2-3 sentence simple summary",
  "rights": ["Right 1", "Right 2", "Right 3"],
  "relevant_law": [
    {"name": "Law name", "section": "Section number", "description": "Simple explanation"}
  ],
  "next_steps": ["Step 1", "Step 2", "Step 3"],
  "case_strength": 75,
  "case_strength_reason": "Why this score",
  "warning": "Important disclaimer or red flag",
  "document_needed": ["Document 1", "Document 2"],
  "authority_to_contact": "Which court/authority to approach",
  "response_language": "urdu or english"
}

## Rules
- ALWAYS return valid JSON only.
- case_strength is 0-100.
- Be empathetic — user cannot afford a lawyer.
- End with: "This is general legal information, not formal legal advice. Consult a licensed lawyer."
- If not a legal issue, use category: "Not a Legal Issue".
- Never make up laws — only real Pakistani laws.
- Specific to Pakistan only.
"""

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        session["history"] = []
    return render_template("index.html")


@app.route("/api/legal-query", methods=["POST"])
def legal_query():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message is empty"}), 400

    if "history" not in session:
        session["history"] = []

    history = session.get("history", [])
    history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1500,
            temperature=0.3,   # lower = more consistent JSON
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *history
            ]
        )

        assistant_message = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": assistant_message})

        # Keep only last 10 messages
        if len(history) > 10:
            history = history[-10:]

        session["history"] = history
        session.modified = True

        # Parse JSON
        try:
            legal_data = json.loads(assistant_message)
        except json.JSONDecodeError:
            # Try to extract JSON block
            json_match = re.search(r'\{.*\}', assistant_message, re.DOTALL)
            if json_match:
                try:
                    legal_data = json.loads(json_match.group())
                except:
                    legal_data = None
            else:
                legal_data = None

        if not legal_data or not isinstance(legal_data, dict):
            legal_data = {
                "category": "General Query",
                "category_icon": "⚖️",
                "summary": assistant_message[:300] + "..." if len(assistant_message) > 300 else assistant_message,
                "rights": [],
                "relevant_law": [],
                "next_steps": [],
                "case_strength": 50,
                "case_strength_reason": "Unable to parse structured response",
                "warning": "This is general legal information, not formal legal advice. Consult a licensed lawyer.",
                "document_needed": [],
                "authority_to_contact": "Local Bar Association or nearest court",
                "response_language": "english"
            }

        legal_data["timestamp"] = datetime.now().strftime("%I:%M %p")
        legal_data["user_query"] = user_message

        return jsonify({"success": True, "data": legal_data})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/draft-document", methods=["POST"])
def draft_document():
    data = request.get_json()
    doc_type = data.get("type", "legal notice")
    context = data.get("context", "")

    prompt = f"""Draft a professional {doc_type} in proper Pakistan legal format based on this situation: {context}

Use formal language suitable for Pakistani courts. Include:
- Date
- To / From sections
- Subject line
- Body with clear paragraphs
- Signature section

Return only the plain text document. Make it ready to print/use."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1000,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        document = response.choices[0].message.content.strip()
        return jsonify({"success": True, "document": document})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/clear-session", methods=["POST"])
def clear_session():
    session["history"] = []
    session.modified = True
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)