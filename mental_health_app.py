import streamlit as st
import os
from openai import OpenAI

# Load OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Expanded wellbeing questions (original slots + extras)
QUESTIONS = [
    ("sleep", "Ask about the user’s sleep quality (good/poor)."),
    ("hours", "Ask how many hours per night they typically sleep."),
    ("mood", "Ask about their general mood (good/low)."),
    ("interest", "Ask if they still enjoy activities as before."),
    ("worry", "Ask if they often experience persistent worry."),
    ("panic", "Ask if they have experienced panic attacks."),
    ("workload", "Ask if their workload feels overwhelming."),
    ("tired", "Ask if they often feel tired or exhausted."),
    ("motivation", "Ask if they struggle with motivation."),
]

def reset_assessment():
    st.session_state.chat_history = []
    st.session_state.answers = {}
    st.session_state.current_q = 0
    st.session_state.summary_generated = False

if "chat_history" not in st.session_state:
    reset_assessment()

st.title("🧠 AI Mental Health Chatbot")
st.caption("This is an advisory tool only and does not replace professional care. "
           "If you're in crisis or feel unsafe, seek immediate help.")

# Display chat history
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# Question flow
if st.session_state.current_q < len(QUESTIONS):
    slot, instruction = QUESTIONS[st.session_state.current_q]

    # Ask empathetic question via AI
    if not st.session_state.chat_history or st.session_state.chat_history[-1][0] != "assistant":
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a warm, empathetic mental health assistant conducting a wellbeing check."},
                {"role": "user", "content": f"Please {instruction} in a conversational and supportive way."}
            ]
        )
        ai_msg = completion.choices[0].message.content
        st.session_state.chat_history.append(("assistant", ai_msg))
        st.rerun()

    # Capture user reply
    if prompt := st.chat_input("Your reply..."):
        st.session_state.chat_history.append(("user", prompt))
        st.session_state.answers[slot] = prompt
        st.session_state.current_q += 1
        st.rerun()

# After all questions → generate summary
else:
    if not st.session_state.summary_generated:
        user_answers = "\n".join([f"{k}: {v}" for k, v in st.session_state.answers.items()])
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "You are a compassionate mental health assistant. "
                    "Summarize the wellbeing check based on user answers. "
                    "Highlight possible stressors, patterns, and coping advice in plain, supportive language. "
                    "Do not provide a clinical diagnosis."
                )},
                {"role": "user", "content": f"Here are the user’s responses:\n{user_answers}"}
            ]
        )
        summary = completion.choices[0].message.content
        st.session_state.chat_history.append(("assistant", f"✅ Thank you for completing the check-in.\n\n**Wellbeing Summary:**\n{summary}\n\n⚠️ If you ever feel unsafe, please seek immediate help or talk to a professional."))
        st.session_state.summary_generated = True
        st.rerun()

    st.chat_input(disabled=True)

    if st.button("🔄 Start a new assessment"):
        reset_assessment()
        st.rerun()
