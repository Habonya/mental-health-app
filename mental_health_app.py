import streamlit as st

# ====================== Page Setup ======================
st.set_page_config(page_title="Mental Health Chatbot", layout="centered")
st.title("🧠 Mental Health Support Chatbot")
st.write(
    "This is an **advisory tool only** and does not replace professional care. "
    "If you're in crisis or feel unsafe, seek immediate help."
)

# ====================== Session State ======================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "slots" not in st.session_state:
    st.session_state.slots = {
        "sleep": None,
        "hours": None,
        "mood": None,
        "interest": None,
        "worry": None,
        "panic": None,
        "workload": None,
        "tired": None,
        "motivation": None,
    }
if "result" not in st.session_state:
    st.session_state.result = None
if "last_diagnosis" not in st.session_state:
    st.session_state.last_diagnosis = None

# ====================== Rule Base (same as before) ======================
def rules(s):
    return [
        {
            "conditions": lambda: s["worry"] == "Yes" and s["panic"] == "Yes",
            "diagnosis": "Anxiety",
            "explanation": "Your answers indicate persistent worry and panic symptoms.",
            "advice": "Practice slow breathing/grounding and consider speaking with a clinician.",
            "specificity": 3,
            "priority": 3,
        },
        {
            "conditions": lambda: s["sleep"] == "Poor" and s["mood"] == "Low" and s["interest"] == "No",
            "diagnosis": "Depression",
            "explanation": "Low mood, loss of interest, and poor sleep suggest depressive symptoms.",
            "advice": "Maintain routine, stay connected, and consider professional help.",
            "specificity": 4,
            "priority": 4,
        },
        {
            "conditions": lambda: s["workload"] == "Yes" and s["tired"] == "Yes" and s["motivation"] == "Yes",
            "diagnosis": "Burnout",
            "explanation": "High workload with fatigue and low motivation suggests burnout.",
            "advice": "Reduce workload if possible, take breaks, and seek support.",
            "specificity": 3,
            "priority": 3,
        },
        {
            "conditions": lambda: s["sleep"] == "Poor" and s["tired"] == "Yes" and (s["hours"] or 0) < 5,
            "diagnosis": "Sleep Deprivation",
            "explanation": "Poor quality sleep under 5 hours is consistent with sleep deprivation.",
            "advice": "Prioritize sleep hygiene and aim for 6–8 hours regularly.",
            "specificity": 4,
            "priority": 4,
        },
        {
            "conditions": lambda: s["worry"] == "Yes" and s["mood"] == "Low" and s["tired"] == "Yes",
            "diagnosis": "Stress Overload",
            "explanation": "Ongoing stress with low mood and fatigue suggests stress overload.",
            "advice": "Try journaling, breaks, and reduce controllable stressors.",
            "specificity": 3,
            "priority": 2,
        },
        {
            "conditions": lambda: s["mood"] == "Low" and s["motivation"] == "Yes" and s["interest"] == "No",
            "diagnosis": "Possible Depression",
            "explanation": "Low mood with loss of interest and reduced motivation is concerning.",
            "advice": "Monitor symptoms and seek professional evaluation.",
            "specificity": 2,
            "priority": 2,
        },
        {
            "conditions": lambda: s["tired"] == "Yes" and s["motivation"] == "Yes" and s["sleep"] == "Good",
            "diagnosis": "Emotional Fatigue",
            "explanation": "Adequate sleep but fatigue and low drive suggest emotional exhaustion.",
            "advice": "Plan pleasant activities and set small goals.",
            "specificity": 2,
            "priority": 1,
        },
        {
            "conditions": lambda: (
                s["worry"] == "Yes" or s["tired"] == "Yes" or s["mood"] == "Low" or s["motivation"] == "Yes"
            ),
            "diagnosis": "Mild Emotional Distress",
            "explanation": "Some emotional strain detected, but no strong pattern.",
            "advice": "Talk to someone you trust and practice self-care.",
            "specificity": 1,
            "priority": 1,
        },
    ]

# ====================== Inference ======================
def infer_diagnosis():
    s = st.session_state.slots
    matching = [r for r in rules(s) if r["conditions"]()]
    if not matching:
        return {
            "diagnosis": "Unclear",
            "explanation": "No clear pattern detected.",
            "advice": "Track your mood/sleep and consult a professional if needed.",
        }
    matching.sort(key=lambda r: (r["specificity"], r["priority"]), reverse=True)
    chosen = matching[0]

    if st.session_state.last_diagnosis == chosen["diagnosis"]:
        return {
            "diagnosis": chosen["diagnosis"],
            "explanation": "Same as last time – answers unchanged.",
            "advice": "Monitor changes and seek professional evaluation.",
        }

    st.session_state.last_diagnosis = chosen["diagnosis"]
    return chosen

# ====================== Question Flow ======================
questions = [
    ("sleep", "How has your sleep quality been (good/poor)?"),
    ("hours", "Roughly how many hours do you sleep per night?"),
    ("mood", "How is your mood (good/low)?"),
    ("interest", "Do you still feel interested in activities (yes/no)?"),
    ("worry", "Are you experiencing persistent worry (yes/no)?"),
    ("panic", "Have you had panic attacks (yes/no)?"),
    ("workload", "Is your workload high (yes/no)?"),
    ("tired", "Do you often feel tired (yes/no)?"),
    ("motivation", "Do you lack motivation (yes/no)?"),
]

def get_next_question():
    for key, text in questions:
        if st.session_state.slots[key] is None:
            return key, text
    return None, None

# ====================== Chat Display ======================
for speaker, msg in st.session_state.chat_history:
    with st.chat_message(speaker):
        st.markdown(msg)

# Ask next question or show result
if st.session_state.result is None:
    slot, qtext = get_next_question()
    if slot:
        with st.chat_message("assistant"):
            st.markdown(qtext)
    else:
        # All questions answered → run inference
        st.session_state.result = infer_diagnosis()
        res = st.session_state.result
        with st.chat_message("assistant"):
            st.markdown(
                f"✅ Assessment complete.\n\n**Diagnosis:** {res['diagnosis']}\n\n**Explanation:** {res['explanation']}\n\n**Advice:** {res['advice']}"
            )

# ====================== Chat Input ======================
if prompt := st.chat_input("Your reply..."):
    st.session_state.chat_history.append(("user", prompt))
    slot, _ = get_next_question()
    if slot:
        response = prompt.lower()
        if slot in ["sleep", "mood"]:
            st.session_state.slots[slot] = "Good" if "good" in response else "Low" if "low" in response else "Poor"
        elif slot == "hours":
            nums = [int(s) for s in response.split() if s.isdigit()]
            st.session_state.slots[slot] = nums[0] if nums else 0
        else:
            st.session_state.slots[slot] = "Yes" if "yes" in response else "No"
    st.experimental_rerun()
