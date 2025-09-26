import streamlit as st
from streamlit_chat import message
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ====================== UI Setup ======================
st.set_page_config(page_title="Mindful AI", layout="wide", initial_sidebar_state="collapsed")

hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🧠 Mindful AI")
st.markdown("##### Your personalized mental health companion.")
st.write("This is an *advisory tool only*. It does not replace professional care.")

# ====================== Session State ======================
def _ensure_defaults():
    defaults = {
        "sleep": None,
        "hours": None,
        "mood": None,
        "interest": None,
        "worry": None,
        "panic": None,
        "workload": None,
        "tired": None,
        "motivation": None,
        "last_diagnosis": None,
        "result": None,
        "messages": [{"role": "assistant", "content": "Hello! I'm here to help with a brief self-assessment. Let's start."}],
        "chat_index": 0,
        "questions_asked": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_ensure_defaults()

# ====================== Helpers ======================
def reset_assessment():
    keep = {"last_diagnosis": st.session_state.get("last_diagnosis")}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _ensure_defaults()
    st.session_state.update({k: v for k, v in keep.items() if v is not None})
    st.rerun()

# ====================== Fuzzy System ======================
hours = ctrl.Antecedent(np.arange(0, 13, 1), 'hours')
sleep = ctrl.Antecedent(np.arange(0, 11, 1), 'sleep')
mood = ctrl.Antecedent(np.arange(0, 11, 1), 'mood')
interest = ctrl.Antecedent(np.arange(0, 11, 1), 'interest')
worry = ctrl.Antecedent(np.arange(0, 11, 1), 'worry')
panic = ctrl.Antecedent(np.arange(0, 11, 1), 'panic')
workload = ctrl.Antecedent(np.arange(0, 11, 1), 'workload')
tired = ctrl.Antecedent(np.arange(0, 11, 1), 'tired')
motivation = ctrl.Antecedent(np.arange(0, 11, 1), 'motivation')

diagnosis = ctrl.Consequent(np.arange(0, 11, 1), 'diagnosis')

# Membership functions
hours['short'] = fuzz.trapmf(hours.universe, [0, 0, 4, 6])
hours['normal'] = fuzz.trapmf(hours.universe, [5, 7, 9, 11])
hours['long'] = fuzz.trapmf(hours.universe, [10, 12, 12, 12])

for var in [sleep, mood, interest, worry, panic, workload, tired, motivation]:
    var['low'] = fuzz.trimf(var.universe, [0, 0, 5])
    var['high'] = fuzz.trimf(var.universe, [5, 10, 10])

diagnosis['mild_distress'] = fuzz.trimf(diagnosis.universe, [0, 0, 3])
diagnosis['fatigue'] = fuzz.trimf(diagnosis.universe, [2, 4, 6])
diagnosis['stress_overload'] = fuzz.trimf(diagnosis.universe, [4, 6, 8])
diagnosis['depression'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['anxiety'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['burnout'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['sleep_deprivation'] = fuzz.trimf(diagnosis.universe, [4, 6, 8])
diagnosis['unclear'] = fuzz.trimf(diagnosis.universe, [0, 2, 4])

# Rules
rule1 = ctrl.Rule(worry['high'] & panic['high'], diagnosis['anxiety'])
rule2 = ctrl.Rule(sleep['low'] & mood['low'] & interest['low'], diagnosis['depression'])
rule3 = ctrl.Rule(workload['high'] & tired['high'] & motivation['low'], diagnosis['burnout'])
rule4 = ctrl.Rule(sleep['low'] & tired['high'] & hours['short'], diagnosis['sleep_deprivation'])
rule5 = ctrl.Rule(worry['high'] & mood['low'] & tired['high'], diagnosis['stress_overload'])
rule6 = ctrl.Rule(mood['low'] & motivation['low'] & interest['low'], diagnosis['depression'])
rule7 = ctrl.Rule(tired['high'] & motivation['high'] & sleep['high'], diagnosis['fatigue'])
rule8 = ctrl.Rule(worry['high'] | tired['high'] | mood['low'] | motivation['low'], diagnosis['mild_distress'])

diagnosis_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
diagnosis_sim = ctrl.ControlSystemSimulation(diagnosis_ctrl)

# ====================== Input Mapping ======================
def map_to_scale(user_input, var):
    if not user_input:
        return 5
    text = user_input.lower()
    if var == "hours":
        digits = ''.join(c for c in text if c.isdigit())
        return int(digits) if digits else 6
    if any(word in text for word in ["good", "well", "okay", "fine", "great"]):
        return 8
    if any(word in text for word in ["bad", "poor", "low", "terrible", "awful"]):
        return 2
    if any(word in text for word in ["yes", "often", "always"]):
        return 8
    if any(word in text for word in ["no", "never", "rarely"]):
        return 2
    return 5

# ====================== Fuzzy Inference ======================
def fuzzy_infer_diagnosis(inputs):
    try:
        diagnosis_sim.input['hours'] = map_to_scale(inputs.get('hours'), 'hours')
        diagnosis_sim.input['sleep'] = map_to_scale(inputs.get('sleep'), 'sleep')
        diagnosis_sim.input['mood'] = map_to_scale(inputs.get('mood'), 'mood')
        diagnosis_sim.input['interest'] = map_to_scale(inputs.get('interest'), 'interest')
        diagnosis_sim.input['worry'] = map_to_scale(inputs.get('worry'), 'worry')
        diagnosis_sim.input['panic'] = map_to_scale(inputs.get('panic'), 'panic')
        diagnosis_sim.input['workload'] = map_to_scale(inputs.get('workload'), 'workload')
        diagnosis_sim.input['tired'] = map_to_scale(inputs.get('tired'), 'tired')
        diagnosis_sim.input['motivation'] = map_to_scale(inputs.get('motivation'), 'motivation')
    except KeyError:
        return {"diagnosis": "Unclear", "explanation": "Not enough answers.", "advice": "Please complete the full assessment."}

    diagnosis_sim.compute()
    best = max(diagnosis_sim.output, key=lambda k: diagnosis_sim.output[k])
    return {"diagnosis": best.capitalize(), "explanation": f"Based on fuzzy analysis, '{best}' is most likely.", "advice": "Track symptoms and consider professional support."}

# ====================== Chatbot ======================
QUESTIONS = [
    ("sleep", "How is your sleep quality?"),
    ("hours", "How many hours do you usually sleep?"),
    ("mood", "How is your overall mood?"),
    ("interest", "Do you feel interested in daily activities?"),
    ("worry", "Are you experiencing persistent worry?"),
    ("panic", "Have you had panic attacks?"),
    ("workload", "Is your workload high?"),
    ("tired", "Do you often feel tired?"),
    ("motivation", "Do you lack motivation?")
]

def handle_user_input(user_input):
    s = st.session_state
    key = QUESTIONS[s.chat_index - 1][0]
    s[key] = user_input

def get_bot_response():
    s = st.session_state
    if s.result:
        return ""
    if s.chat_index < len(QUESTIONS):
        q = QUESTIONS[s.chat_index][1]
        s.chat_index += 1
        return q
    else:
        s.result = fuzzy_infer_diagnosis(s)
        return "Thank you for completing the assessment. Here are your results."

# ====================== Chat UI ======================
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=(msg["role"] == "user"), key=str(i))

if prompt := st.chat_input(""):
    st.session_state.messages.append({"role": "user", "content": prompt})
    handle_user_input(prompt)
    bot_response = get_bot_response()
    if bot_response:
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.rerun()

# ====================== Results ======================
if st.session_state.result:
    res = st.session_state.result
    st.markdown("---")
    st.subheader("📝 Assessment Result")
    st.write(f"*Diagnosis:* {res['diagnosis']}")
    st.write(f"*Explanation:* {res['explanation']}")
    st.info(f"*Advice:* {res['advice']}")
    st.warning("⚠ This tool provides guidance only. Please seek evaluation and care from a licensed professional.")
    st.button("Start New Assessment", on_click=reset_assessment)
