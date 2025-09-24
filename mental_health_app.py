import streamlit as st
#from streamlit_chat import message
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
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Main container for the app
main_container = st.container()

with main_container:
    st.title("🧠 Mindful AI")
    st.markdown("##### Your personalized mental health companion.")
    st.write(
        "This is an **advisory tool only** and does not replace professional care. "
        "If you're in crisis or feel unsafe, seek immediate help."
    )

# ====================== Session State Defaults (Unchanged) ======================
def _ensure_defaults():
    defaults = {
        # Keep existing state variables for diagnosis
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
        
        # New variables for the chatbot
        "messages": [{"role": "assistant", "content": "Hello! I'm here to help you with a brief self-assessment. Let's start with the questions."}],
        "chat_index": 0,
        "questions_asked": True # Start asking questions immediately
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_ensure_defaults()

# ====================== Helpers (Unchanged) ======================
def reset_assessment():
    keep = {"last_diagnosis": st.session_state.get("last_diagnosis")}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _ensure_defaults()
    st.session_state.update({k: v for k, v in keep.items() if v is not None})
    st.experimental_rerun()

# ====================== Fuzzy Control System (Unchanged) ======================
# 1. New Antecedent/Input Variables (based on your questionnaire)
hours = ctrl.Antecedent(np.arange(0, 13, 1), 'hours')
sleep = ctrl.Antecedent(np.arange(0, 11, 1), 'sleep') # 0=Poor, 10=Good
mood = ctrl.Antecedent(np.arange(0, 11, 1), 'mood')   # 0=Low, 10=Good
interest = ctrl.Antecedent(np.arange(0, 11, 1), 'interest') # 0=No, 10=Yes
worry = ctrl.Antecedent(np.arange(0, 11, 1), 'worry')   # 0=No, 10=Yes
panic = ctrl.Antecedent(np.arange(0, 11, 1), 'panic')   # 0=No, 10=Yes
workload = ctrl.Antecedent(np.arange(0, 11, 1), 'workload') # 0=No, 10=Yes
tired = ctrl.Antecedent(np.arange(0, 11, 1), 'tired')   # 0=No, 10=Yes
motivation = ctrl.Antecedent(np.arange(0, 11, 1), 'motivation') # 0=Yes, 10=No

# 2. New Consequent/Output Variables (the diagnoses)
diagnosis = ctrl.Consequent(np.arange(0, 11, 1), 'diagnosis')

# 3. Membership Functions for inputs and output
hours['short'] = fuzz.trapmf(hours.universe, [0, 0, 4, 6])
hours['normal'] = fuzz.trapmf(hours.universe, [5, 7, 9, 11])
hours['long'] = fuzz.trapmf(hours.universe, [10, 12, 12, 12])

sleep['poor'] = fuzz.trimf(sleep.universe, [0, 0, 5])
sleep['good'] = fuzz.trimf(sleep.universe, [5, 10, 10])

mood['low'] = fuzz.trimf(mood.universe, [0, 0, 5])
mood['good'] = fuzz.trimf(mood.universe, [5, 10, 10])

interest['low'] = fuzz.trimf(interest.universe, [0, 0, 5])
interest['high'] = fuzz.trimf(interest.universe, [5, 10, 10])

worry['low'] = fuzz.trimf(worry.universe, [0, 0, 5])
worry['high'] = fuzz.trimf(worry.universe, [5, 10, 10])

panic['low'] = fuzz.trimf(panic.universe, [0, 0, 5])
panic['high'] = fuzz.trimf(panic.universe, [5, 10, 10])

workload['low'] = fuzz.trimf(workload.universe, [0, 0, 5])
workload['high'] = fuzz.trimf(workload.universe, [5, 10, 10])

tired['low'] = fuzz.trimf(tired.universe, [0, 0, 5])
tired['high'] = fuzz.trimf(tired.universe, [5, 10, 10])

motivation['low'] = fuzz.trimf(motivation.universe, [0, 0, 5])
motivation['high'] = fuzz.trimf(motivation.universe, [5, 10, 10])

# Diagnosis outputs (These are placeholders for now, we'll map them later)
diagnosis['mild_distress'] = fuzz.trimf(diagnosis.universe, [0, 0, 3])
diagnosis['fatigue'] = fuzz.trimf(diagnosis.universe, [2, 4, 6])
diagnosis['stress_overload'] = fuzz.trimf(diagnosis.universe, [4, 6, 8])
diagnosis['depression'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['anxiety'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['burnout'] = fuzz.trimf(diagnosis.universe, [6, 8, 10])
diagnosis['sleep_deprivation'] = fuzz.trimf(diagnosis.universe, [4, 6, 8])
diagnosis['unclear'] = fuzz.trimf(diagnosis.universe, [0, 2, 4])

# 4. Fuzzy Rules (Updated from your original rules)
rule1 = ctrl.Rule(worry['high'] & panic['high'], diagnosis['anxiety'])
rule2 = ctrl.Rule(sleep['poor'] & mood['low'] & interest['low'], diagnosis['depression'])
rule3 = ctrl.Rule(workload['high'] & tired['high'] & motivation['low'], diagnosis['burnout'])
rule4 = ctrl.Rule(sleep['poor'] & tired['high'] & hours['short'], diagnosis['sleep_deprivation'])
rule5 = ctrl.Rule(worry['high'] & mood['low'] & tired['high'], diagnosis['stress_overload'])
rule6 = ctrl.Rule(mood['low'] & motivation['low'] & interest['low'], diagnosis['depression']) # Reinforce depression
rule7 = ctrl.Rule(tired['high'] & motivation['high'] & sleep['good'], diagnosis['fatigue']) # Use 'high' motivation as opposite of 'low' motivation to indicate lack of interest but not drive
rule8 = ctrl.Rule(worry['high'] | tired['high'] | mood['low'] | motivation['low'], diagnosis['mild_distress'])

# 5. Create a Control System and Simulation
diagnosis_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
diagnosis_sim = ctrl.ControlSystemSimulation(diagnosis_ctrl)

# ====================== Fuzzy Inference Function (Unchanged) ======================
def fuzzy_infer_diagnosis(inputs):
    """
    Fuzzifies inputs, runs fuzzy inference, and returns confidence scores.
    """
    # Map chat answers to fuzzy inputs
    try:
        diagnosis_sim.input['hours'] = inputs.get('hours', 0)
        diagnosis_sim.input['sleep'] = 0 if inputs.get('sleep') == 'Poor' else 10
        diagnosis_sim.input['mood'] = 0 if inputs.get('mood') == 'Low' else 10
        diagnosis_sim.input['interest'] = 0 if inputs.get('interest') == 'No' else 10
        diagnosis_sim.input['worry'] = 10 if inputs.get('worry') == 'Yes' else 0
        diagnosis_sim.input['panic'] = 10 if inputs.get('panic') == 'Yes' else 0
        diagnosis_sim.input['workload'] = 10 if inputs.get('workload') == 'Yes' else 0
        diagnosis_sim.input['tired'] = 10 if inputs.get('tired') == 'Yes' else 0
        diagnosis_sim.input['motivation'] = 10 if inputs.get('motivation') == 'No' else 0
        
    except KeyError:
        return {"diagnosis": "Unclear", "explanation": "A full set of answers was not provided.", "advice": "Please complete the full assessment."}

    # Compute the fuzzy result
    diagnosis_sim.compute()
    
    # Get the confidence scores for each output member
    confidence_scores = {}
    for member, value in diagnosis_sim.output.items():
        confidence_scores[member] = value

    # Sort and return the highest confidence score
    if not confidence_scores or all(v == 0 for v in confidence_scores.values()):
        return {
            "diagnosis": "Unclear",
            "explanation": "Your answers do not match a specific pattern in this tool.",
            "advice": "Keep tracking sleep, mood, and energy; bring notes to your appointment."
        }

    # Simple winner-take-all for now
    best_match = max(confidence_scores, key=confidence_scores.get)
    
    # Map the fuzzy diagnosis back to a human-readable one
    diagnosis_map = {
        'anxiety': 'Anxiety',
        'depression': 'Depression',
        'burnout': 'Burnout',
        'sleep_deprivation': 'Sleep Deprivation',
        'stress_overload': 'Stress Overload',
        'fatigue': 'Emotional Fatigue',
        'mild_distress': 'Mild Emotional Distress',
        'unclear': 'Unclear'
    }

    # Find the corresponding original diagnosis information
    # The original rules() function is no longer used for inference but still holds the text.
    def rules(s):
        # A simplified version just for text lookup
        return [
            {"diagnosis": "Anxiety", "explanation": "Your answers indicate persistent worry and panic symptoms. (Fuzzy logic was applied to determine this.)", "advice": "Practice slow breathing/grounding and consider speaking with a clinician."},
            {"diagnosis": "Depression", "explanation": "Low mood, loss of interest/pleasure, and sleep disturbance align with common features of depressive episodes. (Fuzzy logic was applied to determine this.)", "advice": "Keep routine, stay connected, and arrange an evaluation with a mental health professional."},
            {"diagnosis": "Burnout", "explanation": "High, sustained workload with fatigue and reduced motivation suggests work-related burnout. (Fuzzy logic was applied to determine this.)", "advice": "Reduce load where possible, take restorative breaks, and discuss support options at work/school."},
            {"diagnosis": "Sleep Deprivation", "explanation": "Poor sleep quality with less than ~5 hours is consistent with sleep deprivation. (Fuzzy logic was applied to determine this.)", "advice": "Prioritize sleep hygiene and aim for 6–8 hours consistently."},
            {"diagnosis": "Stress Overload", "explanation": "Persistent stress can present as ongoing worry, lowered mood, and fatigue. (Fuzzy logic was applied to determine this.)", "advice": "Try journaling, light activity, and structured breaks; review stressors you can change."},
            {"diagnosis": "Possible Depression", "explanation": "Low mood with loss of interest and reduced motivation is concerning for depressive patterns. (Fuzzy logic was applied to determine this.)", "advice": "Monitor symptoms and seek a professional assessment."},
            {"diagnosis": "Emotional Fatigue", "explanation": "Even with adequate sleep, persistent tiredness and low drive can reflect emotional exhaustion. (Fuzzy logic was applied to determine this.)", "advice": "Plan pleasant activities, set small goals, and connect with supportive people."},
            {"diagnosis": "Mild Emotional Distress", "explanation": "Your answers suggest some emotional strain. (Fuzzy logic was applied to determine this.)", "advice": "Talk to someone you trust and prioritize rest and routine."}
        ]

    original_rule = next((r for r in rules(st.session_state) if r['diagnosis'] == diagnosis_map.get(best_match)), None)

    if original_rule:
        return {
            "diagnosis": original_rule['diagnosis'],
            "explanation": f"{original_rule['explanation']} (Confidence: {confidence_scores[best_match]:.2f})",
            "advice": original_rule['advice']
        }
    else:
        return {
            "diagnosis": "Unclear",
            "explanation": "A diagnosis was made, but the corresponding rule was not found.",
            "advice": "Please contact a professional for further help."
        }

# ====================== Personalized Advice Tiers (Unchanged) ======================
# ... (Keep your existing SEVERITY dict and build_personalized_advice function) ...
SEVERITY = {
    "Depression": 3,
    "Anxiety": 3,
    "Burnout": 2,
    "Stress Overload": 2,
    "Sleep Deprivation": 2,
    "Possible Depression": 2,
    "Emotional Fatigue": 1,
    "Mild Emotional Distress": 1,
    "Unclear": 1,
}

def build_personalized_advice(result):
    s = st.session_state
    dx = result["diagnosis"]
    severity = SEVERITY.get(dx, 1)

    immediate, routine, professional = [], [], []

    # Core tiers (emphasis increases with severity)
    if severity >= 3:
        immediate += [
            "Reach out to a trusted person today.",
            "Try a brief grounding/breathing exercise (3–5 minutes).",
        ]
        professional += [
            "**Most Important:** Book an appointment with a licensed mental health professional.",
            "If you feel unsafe or in crisis, seek immediate help.",
        ]
    elif severity == 2:
        immediate += [
            "Take a short restorative break today (walk, stretch, hydration).",
            "Try a simple check-in journal: *How am I feeling? What is one small action I can take?*",
        ]
        routine += [
            "Keep a consistent sleep/wake schedule for the next week.",
            "Plan micro-breaks during work/study (5 minutes each hour).",
        ]
        professional += [
            "**Recommended:** Consider a professional consultation if symptoms persist or worsen.",
        ]
    else:
        immediate += ["Do one pleasant activity today (music, nature, call a friend)."]
        routine += ["Notice patterns: what improves or worsens your mood?"]

    # Personalized add-ons from inputs
    if s.get('workload') == "Yes":
        routine.append("Review workload and set boundaries for the coming week.")
    if s.get('sleep') == "Poor" or s.get('hours') is not None and s.get('hours') < 6:
        routine.append("Follow basic sleep hygiene: limit screens 1 hour before bed, keep the room dark, consistent bedtime.")
    if s.get('worry') == "Yes":
        immediate.append("Try a 4-7-8 breathing cycle (inhale 4s, hold 7s, exhale 8s) for 4 rounds.")
    if s.get('panic') == "Yes":
        immediate.append("Use a grounding technique: 5 things you see, 4 touch, 3 hear, 2 smell, 1 taste.")
    if s.get('motivation') == "No":
        routine.append("Use the 2-minute rule: start with a tiny version of the task to overcome inertia.")
    if s.get('interest') == "No":
        routine.append("Schedule one small activity you used to enjoy (15–20 minutes).")

    # De-duplicate while keeping order
    dedup = lambda items: list(dict.fromkeys(items))
    return {
        "immediate": dedup(immediate),
        "routine": dedup(routine),
        "professional": dedup(professional),
    }

# ====================== Chatbot Logic (Unchanged) ======================
QUESTIONS = [
    ("sleep", "How is your sleep quality? (e.g., 'Good' or 'Poor')"),
    ("hours", "How many hours do you sleep per night? (Please provide a number)"),
    ("mood", "How is your mood? (e.g., 'Good' or 'Low')"),
    ("interest", "Do you feel interested in things? (e.g., 'Yes' or 'No')"),
    ("worry", "Are you experiencing persistent worry? (Yes/No)"),
    ("panic", "Have you had panic attacks? (Yes/No)"),
    ("workload", "Is your workload high? (Yes/No)"),
    ("tired", "Are you feeling tired often? (Yes/No)"),
    ("motivation", "Do you lack motivation? (Yes/No)"),
]

def handle_user_input(user_input):
    s = st.session_state
    
    # Get the key for the current question
    key = QUESTIONS[s.chat_index - 1][0]
    
    # Simple parsing logic
    if key == "hours":
        try:
            s[key] = int("".join(c for c in user_input if c.isdigit()))
        except (ValueError, IndexError):
            s.messages.append({"role": "assistant", "content": "That doesn't look like a number. Please enter a number for your sleep hours."})
            s.chat_index -= 1  # Re-ask the same question
    else:
        if "yes" in user_input.lower():
            s[key] = "Yes"
        elif "no" in user_input.lower():
            s[key] = "No"
        elif "good" in user_input.lower() or "well" in user_input.lower():
            s[key] = "Good"
        elif "poor" in user_input.lower() or "bad" in user_input.lower():
            s[key] = "Poor"
        elif "low" in user_input.lower():
            s[key] = "Low"
        else:
            s.messages.append({"role": "assistant", "content": "I'm not sure how to interpret that. Please try to answer with 'Yes', 'No', 'Good', or 'Poor'."})
            s.chat_index -= 1 # Re-ask the same question

def get_bot_response():
    s = st.session_state
    
    if s.result:
        return ""
    
    if s.chat_index < len(QUESTIONS):
        question_text = QUESTIONS[s.chat_index][1]
        s.chat_index += 1
        return question_text
    else:
        s.result = fuzzy_infer_diagnosis(s)
        return "Thank you for completing the assessment. Please see your results below."

# ====================== Chat UI & Main Loop (Unchanged) ======================
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ====================== Results & Advice (Unchanged) ======================
results_container = st.container()

with results_container:
    if st.session_state.result:
        res = st.session_state.result
        st.markdown("---")
        st.subheader("📝 Assessment Result")
        st.write(f"**Diagnosis:** {res['diagnosis']}")
        st.write(f"**Explanation:** {res['explanation']}")
        st.info(f"**Base Advice:** {res['advice']}")

        tiers = build_personalized_advice(res)
        st.markdown("### 🎯 Personalized Advice Tiers")
        if tiers["immediate"]:
            st.markdown("**Immediate (Today):**")
            for tip in tiers["immediate"]:
                st.markdown(f"- {tip}")
        if tiers["routine"]:
            st.markdown("**Routine (This Week):**")
            for tip in tiers["routine"]:
                st.markdown(f"- {tip}")
        if tiers["professional"]:
            st.markdown("**Professional Support:**")
            for tip in tiers["professional"]:
                st.markdown(f"- {tip}")

        st.warning(
            "⚠️ This tool provides guidance only. Please seek evaluation and care from a licensed mental health professional."
        )

        st.button("Start New Assessment", on_click=reset_assessment)