import os
import streamlit as st
import pandas as pd
from groq import Groq
import json
from dotenv import load_dotenv

load_dotenv()

# ---------------- Load Environment Variables ----------------
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------- Initialize Groq Client ----------------
client = Groq(api_key=GROQ_API_KEY)

# ---------------- Rubric Definition ----------------
RUBRIC = {
    "Accuracy": "Scientifically correct information?",
    "Completeness": "Addresses all parts of the question?",
    "Clarity": "Is the answer clearly written and understandable?",
    "Depth": "Demonstrates deep understanding?",
    "Relevance": "Information relevant to the question?"
}

# ---------------- Evaluate Answer Function ----------------
def evaluate_answer(answer, subject, topic):

    prompt = f"""
You are an expert in {subject}. Evaluate the following answer on the topic '{topic}' using the rubric below:

Accuracy: Scientifically correct information?
Completeness: Addresses all parts of the question?
Clarity: Is the answer clearly written and understandable?
Depth: Demonstrates deep understanding?
Relevance: Information relevant to the question?

Answer: {answer}

Only return a valid compact JSON object:
{{
    "Accuracy": [score, "feedback"],
    "Completeness": [score, "feedback"],
    "Clarity": [score, "feedback"],
    "Depth": [score, "feedback"],
    "Relevance": [score, "feedback"]
}}

Do NOT return anything else. No explanation. No introduction. Only JSON.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        return json.loads(content.replace("'", '"'))
    except:
        return {"raw": content}

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Science Answer Evaluator", layout="wide")
st.title("🧪 Science Answer Evaluator Chatbot")

subject = st.selectbox("Select Subject", ["Biology", "Physics", "Chemistry"])
topic = st.text_input("Enter Topic")
answer = st.text_area("Paste the Answer to Evaluate")

if st.button("Evaluate Answer"):
    if answer.strip():
        with st.spinner("Evaluating..."):
            evaluation = evaluate_answer(answer, subject, topic)

        st.subheader("📊 Rubric Scores & Feedback")
        if "raw" in evaluation:
            st.error("⚠ The model returned unexpected output.")
            st.code(evaluation["raw"])
        else:
            df = pd.DataFrame({
                "Criterion": list(evaluation.keys()),
                "Score": [v[0] for v in evaluation.values()],
                "Feedback": [v[1] for v in evaluation.values()]
            })

            st.dataframe(df)

            st.subheader("📈 Scores Visualization")
            st.bar_chart(df.set_index("Criterion")["Score"])

    else:
        st.warning("Please enter an answer to evaluate.")
