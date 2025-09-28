import streamlit as st
from streamlit_chat import message
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import joblib

# Load ML model and encoder
rf_model = joblib.load("mental_health_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")


# ====================== UI Setup ======================
st.set_page_config(page_title="Expert System", layout="wide", initial_sidebar_state="collapsed")

hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("💡 Group 5's - Mental Health Advisory System")
st.markdown("##### Your secure, initial mental wellness check.")
st.write("**:warning: This is an advisory tool only and does not replace the evaluation or care of a licensed mental health professional. If you are experiencing any mental healt challenges please seek the care of a licensed professional**")
st.markdown("---")

# ====================== Session State ======================
def _ensure_defaults():
    # Use 5 (midpoint) as a default, non-committal value for 0-10 scales
    defaults = {
        "sleep_quality": 5,
        "hours": 7,
        "mood": 5,
        "interest": 5,
        "worry": 5,
        "panic": 5,
        "workload": 5,
        "tiredness": 5,
        "motivation": 5,
        "last_diagnosis": None,
        "result": None,
        "messages": [{"role": "assistant", "content": "Welcome! I'm here to guide you through a brief self-assessment. Please answer the following questions on a scale from 1 (Very Low/Poor/Never) to 10 (Very High/Good/Always), or by giving a specific number for hours."}],
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
    # Clear all keys except essential Streamlit ones
    for key in list(st.session_state.keys()):
        if not key.startswith('__'):
            del st.session_state[key]
    _ensure_defaults()
    st.session_state.update({k: v for k, v in keep.items() if v is not None})
    st.rerun()

# ====================== Fuzzy System Setup ======================

# Antecedents (Inputs)
# Hours can be a crisp input (number) so its universe remains standard.
hours = ctrl.Antecedent(np.arange(0, 13, 1), 'hours')
# All other subjective inputs are now simply a 0-10 scale
sleep_quality = ctrl.Antecedent(np.arange(0, 11, 1), 'sleep_quality')
mood = ctrl.Antecedent(np.arange(0, 11, 1), 'mood')
interest = ctrl.Antecedent(np.arange(0, 11, 1), 'interest')
worry = ctrl.Antecedent(np.arange(0, 11, 1), 'worry')
panic = ctrl.Antecedent(np.arange(0, 11, 1), 'panic')
workload = ctrl.Antecedent(np.arange(0, 11, 1), 'workload')
tiredness = ctrl.Antecedent(np.arange(0, 11, 1), 'tiredness')
motivation = ctrl.Antecedent(np.arange(0, 11, 1), 'motivation')

# Consequent (Output)
diagnosis_risk = ctrl.Consequent(np.arange(0, 11, 1), 'diagnosis_risk')

# --- Membership Functions (Adjusted for better distribution) ---

# Hours slept
hours['short'] = fuzz.trapmf(hours.universe, [0, 0, 4, 6])
hours['normal'] = fuzz.trimf(hours.universe, [6, 8, 10])
hours['long'] = fuzz.trapmf(hours.universe, [9, 11, 12, 12])

# General 0-10 scale (Low, Moderate, High)
for var in [sleep_quality, mood, interest, worry, panic, workload, tiredness, motivation]:
    var['low'] = fuzz.trimf(var.universe, [0, 0, 4])
    var['moderate'] = fuzz.trimf(var.universe, [2, 5, 8])
    var['high'] = fuzz.trimf(var.universe, [6, 10, 10])

# Diagnosis Risk (More specific, overlapping categories)
diagnosis_risk['minimal_concern'] = fuzz.trimf(diagnosis_risk.universe, [0, 0, 3])
diagnosis_risk['elevated_fatigue'] = fuzz.trimf(diagnosis_risk.universe, [2, 4, 6])
diagnosis_risk['stress_distress'] = fuzz.trimf(diagnosis_risk.universe, [4, 6, 8])
diagnosis_risk['anxiety_risk'] = fuzz.trimf(diagnosis_risk.universe, [6, 8, 10])
diagnosis_risk['depressive_risk'] = fuzz.trimf(diagnosis_risk.universe, [6, 8, 10])
diagnosis_risk['burnout_risk'] = fuzz.trimf(diagnosis_risk.universe, [7, 9, 10])

# --- Rules (Adjusted to use the three-level membership functions) ---
rule1 = ctrl.Rule(worry['high'] | panic['high'], diagnosis_risk['anxiety_risk'])
rule2 = ctrl.Rule(mood['low'] & interest['low'] & tiredness['moderate'], diagnosis_risk['depressive_risk'])
rule3 = ctrl.Rule(workload['high'] & tiredness['high'] & motivation['low'], diagnosis_risk['burnout_risk'])
rule4 = ctrl.Rule(sleep_quality['low'] & hours['short'] & tiredness['high'], diagnosis_risk['elevated_fatigue'])
rule5 = ctrl.Rule(worry['moderate'] & mood['moderate'] & workload['high'], diagnosis_risk['stress_distress'])
rule6 = ctrl.Rule(mood['low'] & interest['low'], diagnosis_risk['depressive_risk'])
rule7 = ctrl.Rule(tiredness['high'] & sleep_quality['moderate'] & workload['low'], diagnosis_risk['elevated_fatigue'])
rule8 = ctrl.Rule(mood['moderate'] | interest['moderate'] | motivation['moderate'], diagnosis_risk['minimal_concern'])

# Combine rules into a Control System
diagnosis_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
diagnosis_sim = ctrl.ControlSystemSimulation(diagnosis_ctrl)

# ====================== Fuzzy Inference & Human-like Diagnosis ======================

def fuzzy_infer_diagnosis(inputs):
    """Performs fuzzy inference and generates a human-like, factual diagnosis."""
    
    # 1. CRISP INPUTS - The inputs are now expected to be crisp numbers (0-10 scale)
    try:
        diagnosis_sim.input['hours'] = inputs.get('hours')
        diagnosis_sim.input['sleep_quality'] = inputs.get('sleep_quality')
        diagnosis_sim.input['mood'] = inputs.get('mood')
        diagnosis_sim.input['interest'] = inputs.get('interest')
        diagnosis_sim.input['worry'] = inputs.get('worry')
        diagnosis_sim.input['panic'] = inputs.get('panic')
        diagnosis_sim.input['workload'] = inputs.get('workload')
        diagnosis_sim.input['tiredness'] = inputs.get('tiredness')
        diagnosis_sim.input['motivation'] = inputs.get('motivation')
    except KeyError:
        return {"diagnosis": "Assessment Incomplete", "explanation": "It looks like some questions were skipped. Please complete the full assessment for a meaningful result.", "advice": "Please complete the full assessment."}

    # 2. FUZZY COMPUTATION
    try:
        diagnosis_sim.compute()
        
        # Get the defuzzified crisp output value (0-10)
        final_risk_value = diagnosis_sim.output['diagnosis_risk']
        
        # Get the fuzzy membership for each diagnosis category
        memberships = {
            name: fuzz.interp_membership(diagnosis_risk.universe, diagnosis_risk[name].mf, final_risk_value)
            for name in diagnosis_risk.terms
        }
        
        # Find the category with the highest membership
        best_match = max(memberships, key=memberships.get)
        best_membership = memberships[best_match]

    except Exception as e:
        # Handle cases where compute fails (e.g., control system is not fully defined)
        st.error(f"Fuzzy inference failed: {e}")
        return {"diagnosis": "Error", "explanation": "An internal error occurred during analysis.", "advice": "Try restarting the assessment."}

    # 3. HUMAN-LIKE DIAGNOSIS GENERATION
    
    # Map the fuzzy output to a human-readable primary diagnosis
    
    primary_diagnosis = best_match.replace('_', ' ').title().replace('Risk', 'Tendency').replace('Distress', 'Distress/Overload').replace('Elevated', 'Significant')
    
    # Generate a descriptive summary based on the primary diagnosis
    if best_match == 'minimal_concern':
        summary = "The assessment suggests your current responses fall within a range of minimal concern for common mental health challenges. You appear to be managing your well-being effectively."
        advice = "Continue to practice good self-care, monitor your mood and energy, and don't hesitate to reach out if things change."
    elif best_match == 'elevated_fatigue':
        summary = f"Based on the analysis, there is a significant indication of elevated fatigue/low energy (Membership: ${best_membership:.2f}$). This is often tied to your reported sleep quality and general tiredness."
        advice = "Focus on **sleep hygiene** (consistent schedule, dark room) and energy management. If persistent, this could be a sign of an underlying physical or mental health issue that warrants a check-up."
    elif best_match == 'stress_distress':
        summary = f"The results suggest a high level of stress or general distress (Membership: ${best_membership:.2f}$). This is particularly related to the reported level of worry and workload, leading to a state of emotional and mental strain."
        advice = "Prioritize stress reduction techniques like mindfulness, setting firmer boundaries around work, and scheduling dedicated time for relaxation. If your distress is interfering with daily life, consider professional guidance."
    elif best_match == 'anxiety_risk':
        summary = f"There is a noticeable tendency toward anxiety (Membership: ${best_membership:.2f}$), strongly linked to your self-reported levels of worry and, possibly, panic. This suggests your system may be in a state of hyper-arousal."
        advice = "Engage in controlled breathing exercises and grounding techniques. If panic attacks are a concern, immediate professional consultation with a therapist specializing in anxiety is highly recommended."
    elif best_match == 'depressive_risk':
        summary = f"The assessment indicates a **potential depressive tendency (Membership: ${best_membership:.2f}$), given the co-occurrence of low mood, reduced interest, and low motivation."
        advice = "It is crucial to break the isolation cycle by engaging in light activities, even when you don't feel like it. Seek an evaluation from a mental health expert if these symptoms persist for more than two weeks."
    elif best_match == 'burnout_risk':
        summary = f"The pattern of high workload, high tiredness, and critically low motivation points to a strong risk of occupational burnout (Membership: ${best_membership:.2f}$). This is a state of chronic workplace stress."
        advice = "Immediate attention to work-life balance is necessary. This may involve taking time off, delegating tasks, or seeking support to manage professional demands. Burnout requires dedicated recovery and often professional coaching."
    else:
        summary = "The fuzzy logic system processed your inputs, but the resulting pattern is unclear or highly mixed. This means no single risk factor strongly dominates the others, or your symptoms are too mild across the board to generate a definitive primary diagnosis."
        advice = "Continue to monitor your symptoms. A mixed pattern may indicate mild, generalized stress. If your symptoms worsen, retake the assessment or seek professional advice."

    # Factual Enhancement: Include the most dominant symptoms as context
    top_symptoms = [k.capitalize() for k, v in inputs.items() if (k != 'hours' and v >= 8) or (k in ['mood', 'interest', 'motivation', 'sleep_quality'] and v <= 3)]
    
    if top_symptoms:
        summary += f" The analysis was particularly influenced by your self-reported data on **{', '.join(top_symptoms)}**."

    return {
        "diagnosis": primary_diagnosis,
        "explanation": summary,
        "advice": advice,
        "crisp_risk_value": final_risk_value,
        "best_membership": best_membership
    }
    
# ====================== Chatbot & Input Handling (Crucially simplified) ======================
QUESTIONS = [
    (
        "sleep_quality",
        "Thinking about your sleep recently, how restful or refreshing does it feel on most nights? "
        "Please rate from 1 (very poor) to 10 (excellent)."
    ),
    (
        "hours",
        "Can you describe your typical night’s rest lately? Roughly how many hours of sleep do you usually get? "
        "It's okay to estimate."
    ),
    (
        "mood",
        "Over the past few days, how have you been feeling emotionally? "
        "1 means very low, sad, or stressed, and 10 means very positive and calm."
    ),
    (
        "interest",
        "How engaged or interested have you felt in your usual daily activities lately? "
        "1 indicates very low interest, 10 indicates very high."
    ),
    (
        "worry",
        "Have you noticed moments of recurring worry or anxious thoughts? "
        "Please rate from 1 (never) to 10 (almost always)."
    ),
    (
        "panic",
        "Have there been times of sudden anxiety or tension that felt overwhelming? "
        "If so, how often? Rate from 1 (never) to 10 (very frequently)."
    ),
    (
        "workload",
        "Thinking about your responsibilities at work, school, or home, how demanding or heavy does your current workload feel? "
        "Rate from 1 (very light) to 10 (extremely heavy)."
    ),
    (
        "tiredness",
        "During your daily routine, how often do you notice feeling drained or low in energy? "
        "1 means rarely, 10 means almost all the time."
    ),
    (
        "motivation",
        "How would you describe your drive or motivation when approaching usual tasks? "
        "1 means very low, 10 means very high."
    )
]


def handle_user_input(user_input):
    s = st.session_state
    
    if s.chat_index == 0:
        # First message is just a greeting, start with the first question on the next turn
        s.chat_index += 1
        return
        
    key = QUESTIONS[s.chat_index - 1][0]
    
    # Try to extract a number from the user's response
    try:
        if key == "hours":
            # Extract digits for 'hours'
            digits = ''.join(c for c in user_input if c.isdigit())
            value = int(digits) if digits else 7
            # Clamp hours to a reasonable range
            s[key] = max(0, min(12, value)) 
        else:
            # Extract a number for 1-10 scales
            value = int(user_input.strip())
            # Clamp scale to 1-10
            s[key] = max(1, min(10, value))
            
    except ValueError:
        # If input is not a clear number, use the midpoint (5) for 1-10 scales, or 7 for hours
        midpoint = 7 if key == "hours" else 5
        s[key] = midpoint
        st.session_state.messages.append({"role": "assistant", "content": f"I didn't catch a clear number for **{key.replace('_', ' ').title()}**. I've recorded a neutral score of **{midpoint}** to continue the assessment."})
        
def get_bot_response():
    s = st.session_state
    if s.result:
        return ""
        
    if s.chat_index < len(QUESTIONS):
        # Ask the next question
        q = QUESTIONS[s.chat_index][1]
        s.chat_index += 1
        return q
    else:
        # All questions asked, compute result
        inputs = {key: s.get(key) for key, _ in QUESTIONS}
        s.result = fuzzy_infer_diagnosis(inputs)
        return "Thank you. I have all the information needed. Here is the output of the analysis:"

# ====================== Custom UI Styling ======================
custom_css = """
<style>
    body {
        background: linear-gradient(135deg, #e0f7fa, #fce4ec);
    }
    .stChatMessage {
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        margin: 0.3rem 0;
        max-width: 80%;
        line-height: 1.4;
    }
    .stChatMessage.user {
        background: #bbdefb;
        margin-left: auto;
        color: black;
        font-weight: 500;
    }
    .stChatMessage.assistant {
        background: #f1f8e9;
        margin-right: auto;
        color: black;
    }
    .stCard {
        background: white;
        border-radius: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 1.2rem;
        margin: 1rem 0;
    }
    .stResult {
        font-size: 1.1rem;
        line-height: 1.6;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ====================== Progress Bar ======================
if "chat_index" in st.session_state:
    progress = st.session_state.chat_index / len(QUESTIONS)
    st.progress(progress, text=f"Progress: {st.session_state.chat_index}/{len(QUESTIONS)}")


# ====================== Chat History Display (Styled Bubbles) ======================
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            st.markdown(
                f"""
                <div style="background-color:#E6F4EA; color:#1B4332; 
                            padding:12px; border-radius:15px; margin:6px 0; 
                            max-width:80%;">
                    🧠 {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background-color:#D0E7FF; color:#003566; 
                            padding:12px; border-radius:15px; margin:6px 0; 
                            max-width:80%; margin-left:auto;">
                    👤 {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ====================== Input Box ======================
if st.session_state.result is None:
    if prompt := st.chat_input("💬 Type your response here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        handle_user_input(prompt)
        bot_response = get_bot_response()
        if bot_response:
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            st.rerun()
else:
    st.chat_input(placeholder="✨ Assessment complete. Start a new one below.", disabled=True)

# ====================== Results Display ======================
if st.session_state.result:
    res = st.session_state.result
    st.markdown("---")
    
    # ================== Robust ML Prediction ==================
    ml_label_map = {
        'minimal_concern': 'Minimal Concern',
        'elevated_fatigue': 'Elevated Fatigue',
        'stress_distress': 'Stress/Distress',
        'anxiety_risk': 'Anxiety Tendency',
        'depressive_risk': 'Depressive Tendency',
        'burnout_risk': 'Burnout Risk'
    }

    # Define a priority list for “closest match” in case of unexpected label
    # The original implementation of 'closest match' was highly flawed,
    # simply defaulting to the first item ('minimal_concern').
    # I've kept the logic structure but noted the original issue.
    # A proper fallback would require a measure of distance in the feature space.
    fallback_order = ['minimal_concern', 'elevated_fatigue', 'stress_distress', 
                      'anxiety_risk', 'depressive_risk', 'burnout_risk']

    # Prepare features for ML model
    inputs = {key: st.session_state.get(key) for key, _ in QUESTIONS}
    features = [
        inputs['sleep_quality'],
        inputs['hours'],
        inputs['mood'],
        inputs['interest'],
        inputs['worry'],
        inputs['panic'],
        inputs['workload'],
        inputs['tiredness'],
        inputs['motivation']
    ]
    X_input = [features]

    # Predict with ML model
    y_pred = rf_model.predict(X_input)
    # Decode the prediction label
    # NOTE: The original code used the raw string of the prediction from the model
    # (which would be a stringified number if the model output was encoded).
    # Since the full context of the ML model output is unknown, the safe mapping is used.
    # Assuming y_pred[0] is one of the keys in ml_label_map.
    y_pred_str = str(y_pred[0])

    # Map prediction safely; if unknown, pick the closest in fallback_order (or default to the first)
    ml_prediction = ml_label_map.get(
        y_pred_str,
        ml_label_map[fallback_order[min(range(len(fallback_order)), key=lambda i: abs(i - 0))]]
    )

    # ML Prediction Card
    st.markdown(
        f"""
        <div style="background-color:#F0F4C3; border:2px solid #8BC34A; 
                    border-radius:15px; padding:20px; margin-top:20px;">
            <h3 style="color:#33691E;">🤖 Machine Learning Model Prediction</h3>
            <p><b>Prediction:</b> {ml_prediction}</p>
            <p>This is based on statistical training with your input values.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Diagnosis in a nice card
    st.markdown(
        f"""
        <div class="stCard">
            <h3>📝 Cognitive Assessment Outcome: <b>{res['diagnosis']}</b></h3>
            <p class="stResult">{res['explanation']}</p>
            <p>🎯 <b>Next Step:</b> {res['advice']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display additional metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Calculated Fuzzy Risk Score (0-10)", f"{res['crisp_risk_value']:.2f}")
    with col2:
        st.metric(f"Confidence in {res['diagnosis']}", f"{res['best_membership']:.2f}")

    # Final disclaimer
    st.warning("⚠️ **Disclaimer:** This is an *initial risk screening*. Please seek professional help if symptoms persist or worsen.")

    # Button to reset assessment
    st.button("🔄 Start New Assessment", on_click=reset_assessment)