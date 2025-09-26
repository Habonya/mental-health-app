import streamlit as st
from streamlit_chat import message
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ====================== UI Setup and Styling ======================
st.set_page_config(
    page_title="Mindful AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default hamburger menu and footer
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Mindful AI")
st.markdown("##### Your personalized mental health companion.")
st.write(
    "This is an *advisory tool only* and does not replace professional care. "
    "If you're in crisis or feel unsafe, seek immediate help."
)

# ====================== Session State Defaults ======================
def _ensure_defaults():
    defaults = {
        # Diagnosis inputs
        "sleep": None, "hours": None, "mood": None, "interest": None,
        "worry": None, "panic": None, "workload": None, "tired": None, "motivation": None,
        "last_diagnosis": None, "result": None,
        # Chat state
        "messages": [{
            "role": "assistant",
            "content": "Hello! I'm here to help you with a brief self-assessment. Let's start with the questions."
        }],
        "chat_index": 0,
        "questions_asked": True
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
_ensure_defaults()

def reset_assessment():
    keep = {"last_diagnosis": st.session_state.get("last_diagnosis")}
    st.session_state.clear()
    _ensure_defaults()
    st.session_state.update({k: v for k, v in keep.items() if v is not None})
    st.rerun()

# ====================== Fuzzy Control System ======================
# Inputs
hours = ctrl.Antecedent(np.arange(0, 13, 1), 'hours')
sleep = ctrl.Antecedent(np.arange(0, 11, 1), 'sleep')
mood = ctrl.Antecedent(np.arange(0, 11, 1), 'mood')
interest = ctrl.Antecedent(np.arange(0, 11, 1), 'interest')
worry = ctrl.Antecedent(np.arange(0, 11, 1), 'worry')
panic = ctrl.Antecedent(np.arange(0, 11, 1), 'panic')
workload = ctrl.Antecedent(np.arange(0, 11, 1), 'workload')
tired = ctrl.Antecedent(np.arange(0, 11, 1), 'tired')
motivation = ctrl.Antecedent(np.arange(0, 11, 1), 'motivation')

# Output
diagnosis = ctrl.Consequent(np.arange(0, 11, 1), 'diagnosis')

# Membership Functions
hours['short']  = fuzz.trapmf(hours.universe, [0, 0, 4, 6])
hours['normal'] = fuzz.trapmf(hours.universe, [5, 7, 9, 11])
hours['long']   = fuzz.trapmf(hours.universe, [10, 12, 12, 12])

sleep['poor'], sleep['good'] = fuzz.trimf(sleep.universe, [0,0,5]), fuzz.trimf(sleep.universe, [5,10,10])
mood['low'], mood['good'] = fuzz.trimf(mood.universe, [0,0,5]), fuzz.trimf(mood.universe, [5,10,10])
interest['low'], interest['high'] = fuzz.trimf(interest.universe, [0,0,5]), fuzz.trimf(interest.universe, [5,10,10])
worry['low'], worry['high'] = fuzz.trimf(worry.universe, [0,0,5]), fuzz.trimf(worry.universe, [5,10,10])
panic['low'], panic['high'] = fuzz.trimf(panic.universe, [0,0,5]), fuzz.trimf(panic.universe, [5,10,10])
workload['low'], workload['high'] = fuzz.trimf(workload.universe, [0,0,5]), fuzz.trimf(workload.universe, [5,10,10])
tired['low'], tired['high'] = fuzz.trimf(tired.universe, [0,0,5]), fuzz.trimf(tired.universe, [5,10,10])
motivation['low'], motivation['high'] = fuzz.trimf(motivation.universe, [0,0,5]), fuzz.trimf(motivation.universe, [5,10,10])

# Diagnosis output membership
diagnosis['mild_distress']   = fuzz.trimf(diagnosis.universe, [0,0,3])
diagnosis['fatigue']         = fuzz.trimf(diagnosis.universe, [2,4,6])
diagnosis['stress_overload'] = fuzz.trimf(diagnosis.universe, [4,6,8])
diagnosis['depression']      = fuzz.trimf(diagnosis.universe, [6,8,10])
diagnosis['anxiety']         = fuzz.trimf(diagnosis.universe, [6,8,10])
diagnosis['burnout']         = fuzz.trimf(diagnosis.universe, [6,8,10])
diagnosis['sleep_deprivation']= fuzz.trimf(diagnosis.universe, [4,6,8])
diagnosis['unclear']         = fuzz.trimf(diagnosis.universe, [0,2,4])

# Rules
rules = [
    ctrl.Rule(worry['high'] & panic['high'], diagnosis['anxiety']),
    ctrl.Rule(sleep['poor'] & mood['low'] & interest['low'], diagnosis['depression']),
    ctrl.Rule(workload['high'] & tired['high'] & motivation['low'], diagnosis['burnout']),
    ctrl.Rule(sleep['poor'] & tired['high'] & hours['short'], diagnosis['sleep_deprivation']),
    ctrl.Rule(worry['high'] & mood['low'] & tired['high'], diagnosis['stress_overload']),
    ctrl.Rule(mood['low'] & motivation['low'] & interest['low'], diagnosis['depression']),
    ctrl.Rule(tired['high'] & motivation['high'] & sleep['good'], diagnosis['fatigue']),
    ctrl.Rule(worry['high'] | tired['high'] | mood['low'] | motivation['low'], diagnosis['mild_distress']),
]

diagnosis_ctrl = ctrl.ControlSystem(rules)
diagnosis_sim = ctrl.ControlSystemSimulation(diagnosis_ctrl)

# ====================== Fuzzy Inference Function ======================
def fuzzy_infer_diagnosis(inputs):
    try:
        diagnosis_sim.input['hours']      = inputs.get('hours', 0)
        diagnosis_sim.input['sleep']      = 0 if inputs.get('sleep') == 'Poor' else 10
        diagnosis_sim.input['mood']       = 0 if inputs.get('mood') == 'Low' else 10
        diagnosis_sim.input['interest']   = 0 if inputs.get('interest') == 'No' else 10
        diagnosis_sim.input['worry']      = 10 if inputs.get('worry') == 'Yes' else 0
        diagnosis_sim.input['panic']      = 10 if inputs.get('panic') == 'Yes' else 0
        diagnosis_sim.input['workload']   = 10 if inputs.get('workload') == 'Yes' else 0
        diagnosis_sim.input['tired']      = 10 if inputs.get('tired') == 'Yes' else 0
        diagnosis_sim.input['motivation'] = 10 if inputs.get('motivation') == 'No' else 0
    except KeyError:
        return {"diagnosis": "Unclear", "explanation": "Incomplete answers.", "advice": "Please complete the full assessment."}

    diagnosis_sim.compute()
    scores = {k: v for k, v in diagnosis_sim.output.items()}
    if not scores or all(v == 0 for v in scores.values()):
        return {"diagnosis": "Unclear", "explanation": "No clear pattern.", "advice": "Track your symptoms & seek help if needed."}

    best = max(scores, key=scores.get)
    dx_map = {
        'anxiety': 'Anxiety', 'depression': 'Depression', 'burnout': 'Burnout',
        'sleep_deprivation': 'Sleep Deprivation', 'stress_overload': 'Stress Overload',
        'fatigue': 'Emotional Fatigue', 'mild_distress': 'Mild Emotional Distress', 'unclear': 'Unclear'
    }
    return {"diagnosis": dx_map.get(best, "Unclear"), "explanation": f"Confidence {scores[best]:.2f}", "advice": "Consider professional support."}

# ====================== Chatbot Logic ======================
QUESTIONS = [
    ("sleep", "How is your sleep quality? (Good/Poor)"),
    ("hours", "How many hours do you sleep per night?"),
    ("mood", "How is your mood? (Good/Low)"),
    ("interest", "Do you feel interested in things? (Yes/No)"),
    ("worry", "Are you experiencing persistent worry? (Yes/No)"),
    ("panic", "Have you had panic attacks? (Yes/No)"),
    ("workload", "Is your workload high? (Yes/No)"),
    ("tired", "Are you feeling tired often? (Yes/No)"),
    ("motivation", "Do you lack motivation? (Yes/No)"),
]

def handle_user_input(user_input):
    s = st.session_state
    key = QUESTIONS[s.chat_index - 1][0]

    if key == "hours":
        try:
            s[key] = int("".join(c for c in user_input if c.isdigit()))
        except:
            s.messages.append({"role": "assistant", "content": "Please enter a number for sleep hours."})
            s.chat_index -= 1
    else:
        responses = {"yes": "Yes", "no": "No", "good": "Good", "poor": "Poor", "low": "Low"}
        for k,v in responses.items():
            if k in user_input.lower():
                s[key] = v
                return
        s.messages.append({"role": "assistant", "content": "Please answer with Yes/No/Good/Poor."})
        s.chat_index -= 1

def get_bot_response():
    s = st.session_state
    if s.result: return ""
    if s.chat_index < len(QUESTIONS):
        question_text = QUESTIONS[s.chat_index][1]
        s.chat_index += 1
        return question_text
    s.result = fuzzy_infer_diagnosis(s)
    return "Thank you for completing the assessment. Please see your results below."

# ====================== Chat UI ======================
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=(msg["role"]=="user"), key=str(i))

if prompt := st.chat_input(""):
    st.session_state.messages.append({"role": "user", "content": prompt})
    handle_user_input(prompt)
    if bot_response := get_bot_response():
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.rerun()

# ====================== Results ======================
if st.session_state.result:
    res = st.session_state.result
    st.markdown("---")
    st.subheader("📝 Assessment Result")
    st.write(f"*Diagnosis:* {res['diagnosis']}")
    st.write(f"*Explanation:* {res['explanation']}")
    st.info(f"*Base Advice:* {res['advice']}")
    st.warning("⚠ This tool provides guidance only. Seek professional care.")
    st.button("Start New Assessment", on_click=reset_assessment)
