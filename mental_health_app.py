import streamlit as st

# --- Page Setup ---
st.set_page_config(page_title="Mental Health Support System", layout="centered")

st.title("🧠 Mental Health Support System")
st.write("This is an **advisory tool only**. It does not replace professional care.")

# Track session state for recency and refactoriness
if "last_diagnosis" not in st.session_state:
    st.session_state.last_diagnosis = None
if "history" not in st.session_state:
    st.session_state.history = []

# --- Ask Questions ---
with st.form("assessment_form"):
    sleep = st.radio("How is your sleep quality?", ["Good", "Poor"])
    hours = st.number_input("How many hours do you sleep per night?", min_value=0, max_value=24, value=7)

    mood = st.radio("How is your mood?", ["Good", "Low"])
    interest = st.radio("Do you feel interested in things?", ["Yes", "No"])
    worry = st.radio("Are you experiencing persistent worry?", ["Yes", "No"])
    panic = st.radio("Have you had panic attacks?", ["Yes", "No"])
    workload = st.radio("Is your workload high?", ["Yes", "No"])
    tired = st.radio("Are you feeling tired often?", ["Yes", "No"])
    motivation = st.radio("Do you lack motivation?", ["Yes", "No"])

    submitted = st.form_submit_button("Get Assessment")

# --- Rule Base (with specificity ranking) ---
rules = [
    {
        "conditions": lambda: worry == "Yes" and panic == "Yes",
        "diagnosis": "Anxiety",
        "advice": "Try deep breathing, regular physical activity, and consider professional support.",
        "explanation": "Persistent worry and panic attacks are core indicators of anxiety disorders.",
        "specificity": 3
    },
    {
        "conditions": lambda: sleep == "Poor" and mood == "Low" and interest == "No",
        "diagnosis": "Depression",
        "advice": "Consider therapy, maintain a regular sleep routine, and stay connected with loved ones.",
        "explanation": "Poor sleep, low mood, and loss of interest are hallmark symptoms of depression.",
        "specificity": 4
    },
    {
        "conditions": lambda: workload == "Yes" and tired == "Yes" and motivation == "Yes",
        "diagnosis": "Burnout",
        "advice": "Reduce workload, take breaks, and rest. Seek professional support if symptoms persist.",
        "explanation": "High workload + tiredness + lack of motivation suggests burnout.",
        "specificity": 3
    },
    {
        "conditions": lambda: sleep == "Poor" and tired == "Yes" and hours < 5,
        "diagnosis": "Sleep Deprivation",
        "advice": "Aim for 6–8 hours of quality sleep. Reduce screen time before bed.",
        "explanation": "Poor sleep, tiredness, and <5 hours rest strongly suggest sleep deprivation.",
        "specificity": 4
    },
    {
        "conditions": lambda: worry == "Yes" and mood == "Low" and tired == "Yes",
        "diagnosis": "Stress Overload",
        "advice": "Try journaling, walking, or meditation. Seek help if stress continues.",
        "explanation": "Persistent worry, low mood, and fatigue suggest overwhelming stress.",
        "specificity": 3
    },
    {
        "conditions": lambda: mood == "Low" and motivation == "Yes" and interest == "No",
        "diagnosis": "Possible Depression",
        "advice": "Monitor your symptoms and consider professional consultation.",
        "explanation": "Low mood, loss of interest, and lack of motivation are depressive tendencies.",
        "specificity": 2
    },
    {
        "conditions": lambda: tired == "Yes" and motivation == "Yes" and sleep == "Good",
        "diagnosis": "Emotional Fatigue",
        "advice": "Take breaks, enjoy hobbies, and stay socially connected.",
        "explanation": "Good sleep but tired + unmotivated indicates emotional fatigue.",
        "specificity": 2
    },
    {
        "conditions": lambda: worry == "Yes" or tired == "Yes" or mood == "Low" or motivation == "Yes",
        "diagnosis": "Mild Emotional Distress",
        "advice": "Talk to someone, get good sleep, and care for your physical health.",
        "explanation": "Some level of worry, tiredness, or low mood indicates mild distress.",
        "specificity": 1
    }
]

# --- Inference Engine with Conflict Resolution ---
def infer_diagnosis():
    # Apply rules that match
    matching_rules = [r for r in rules if r["conditions"]()]

    if not matching_rules:
        return {
            "diagnosis": "Unclear",
            "advice": "Consider consulting a mental health professional.",
            "explanation": "Your answers do not match a specific condition."
        }

    # Strategy 1: Rule Specificity (pick the most specific rule)
    matching_rules.sort(key=lambda r: r["specificity"], reverse=True)

    # Strategy 2: Lexical Order (rules are sorted in code order already)

    # Choose top rule
    chosen_rule = matching_rules[0]

    # Strategy 3: Refactoriness (avoid repeating same diagnosis)
    if st.session_state.last_diagnosis == chosen_rule["diagnosis"]:
        return {
            "diagnosis": chosen_rule["diagnosis"],
            "advice": "You have already received this advice. Please monitor changes in your condition.",
            "explanation": "This diagnosis has already been made earlier based on your symptoms."
        }

    # Strategy 4: Recency (update with the latest condition)
    st.session_state.last_diagnosis = chosen_rule["diagnosis"]
    st.session_state.history.append(chosen_rule["diagnosis"])

    return chosen_rule

# --- Run inference when form is submitted ---
if submitted:
    result = infer_diagnosis()

    # --- Show Results ---
    st.subheader("📝 Assessment Result")
    st.write(f"**Diagnosis:** {result['diagnosis']}")
    st.write(f"**Explanation:** {result['explanation']}")
    st.info(f"**Advice:** {result['advice']}")

    # --- Show history for transparency (Means–Ends Analysis) ---
    with st.expander("🗂️ Reasoning Path (History)"):
        st.write("The system considered your symptoms step by step. Here are past diagnoses in this session:")
        for i, diag in enumerate(st.session_state.history, 1):
            st.write(f"{i}. {diag}")
