import os
import streamlit as st
import pandas as pd
from groq import Groq
import json

# ---------------- Load Environment Variables ----------------
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    st.write("DEBUG: Loaded API key from Streamlit secrets.")
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    st.write("DEBUG: Loaded API key from OS environment variables.")

st.write("DEBUG: API Key exists =", GROQ_API_KEY is not None)

# ---------------- Initialize Groq Client ----------------
try:
    client = Groq(api_key=GROQ_API_KEY)
    st.write("DEBUG: Groq client initialized successfully.")
except Exception as e:
    st.error(f"DEBUG ERROR: Failed to initialize Groq client: {e}")

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

{pd.DataFrame.from_dict(RUBRIC, orient='index', columns=['Criteria']).to_string()}

Answer: {answer}

For each criterion, provide:
1. A score from 1 to 5
2. A concise explanation of the reasoning, highlighting inaccuracies or gaps.
Format the response as JSON like:
{{"Accuracy": [score, "feedback"], "Completeness": [score, "feedback"], ...}}
"""

    # Debug print: prompt content
    st.write("DEBUG: Prompt sent to model:")
    st.code(prompt)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        st.write("DEBUG: Raw model response:")
        st.code(response)
    except Exception as e:
        st.error(f"DEBUG ERROR: API request failed: {e}")
        return {"error": str(e)}

    content = response.choices[0].message.content
    st.write("DEBUG: Model returned content:")
    st.code(content)

    # Convert JSON-like string to Python dictionary safely
    try:
        parsed = json.loads(content.replace("'", '"'))
        st.write("DEBUG: JSON successfully parsed:", parsed)
        return parsed
    except Exception as e:
        st.error(f"DEBUG ERROR: JSON parsing failed: {e}")
        return {"raw": content}

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Science Answer Evaluator", layout="wide")
st.title("🧪 Science Answer Evaluator Chatbot (Debug Mode)")

subject = st.selectbox("Select Subject", ["Biology", "Physics", "Chemistry"])
topic = st.text_input("Enter Topic")
answer = st.text_area("Paste the Answer to Evaluate")

if st.button("Evaluate Answer"):
    if answer.strip():
        with st.spinner("Evaluating..."):
            evaluation = evaluate_answer(answer, subject, topic)

        st.subheader("📊 Rubric Scores & Feedback")
        if "raw" in evaluation:
            st.text(evaluation["raw"])
        else:
            df = pd.DataFrame({
                "Criterion": list(evaluation.keys()),
                "Score": [v[0] for v in evaluation.values()],
                "Feedback": [v[1] for v in evaluation.values()]
            })

            st.dataframe(df)

            # Bar chart
            st.subheader("📈 Scores Visualization")
            st.bar_chart(df.set_index("Criterion")["Score"])
    else:
        st.warning("Please enter an answer to evaluate.")
