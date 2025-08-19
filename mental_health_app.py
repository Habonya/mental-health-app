import streamlit as st

# --- Page Setup ---
st.set_page_config(page_title="Mental Health Support System", layout="centered")

st.title("🧠 Mental Health Support System")
st.write("This is an **advisory tool only**. It does not replace professional care.")

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

# --- Inference Logic ---
if submitted:
    diagnosis, advice, explanation = "", "", ""

    if worry == "Yes" and panic == "Yes":
        diagnosis = "Anxiety"
        advice = "Try deep breathing, regular physical activity, and consider professional support."
        explanation = "Persistent worry and panic attacks are core indicators of anxiety disorders."

    elif sleep == "Poor" and mood == "Low" and interest == "No":
        diagnosis = "Depression"
        advice = "Consider therapy, maintain a regular sleep routine, and stay connected with loved ones."
        explanation = "Poor sleep, low mood, and loss of interest are hallmark symptoms of depression."

    elif workload == "Yes" and tired == "Yes" and motivation == "Yes":
        diagnosis = "Burnout"
        advice = "Reduce workload, take breaks, and rest. Seek professional support if symptoms persist."
        explanation = "High workload + tiredness + lack of motivation suggests burnout."

    elif sleep == "Poor" and tired == "Yes" and hours < 5:
        diagnosis = "Sleep Deprivation"
        advice = "Aim for 6–8 hours of quality sleep. Reduce screen time before bed."
        explanation = "Poor sleep, tiredness, and <5 hours rest strongly suggest sleep deprivation."

    elif worry == "Yes" and mood == "Low" and tired == "Yes":
        diagnosis = "Stress Overload"
        advice = "Try journaling, walking, or meditation. Seek help if stress continues."
        explanation = "Persistent worry, low mood, and fatigue suggest overwhelming stress."

    elif mood == "Low" and motivation == "Yes" and interest == "No":
        diagnosis = "Possible Depression"
        advice = "Monitor your symptoms and consider professional consultation."
        explanation = "Low mood, loss of interest, and lack of motivation are depressive tendencies."

    elif tired == "Yes" and motivation == "Yes" and sleep == "Good":
        diagnosis = "Emotional Fatigue"
        advice = "Take breaks, enjoy hobbies, and stay socially connected."
        explanation = "Good sleep but tired + unmotivated indicates emotional fatigue."

    elif worry == "Yes" or tired == "Yes" or mood == "Low" or motivation == "Yes":
        diagnosis = "Mild Emotional Distress"
        advice = "Talk to someone, get good sleep, and care for your physical health."
        explanation = "Some level of worry, tiredness, or low mood indicates mild distress."

    else:
        diagnosis = "Unclear"
        advice = "Consider consulting a mental health professional."
        explanation = "Your answers do not match a specific condition."

    # --- Show Results ---
    st.subheader("📝 Assessment Result")
    st.write(f"**Diagnosis:** {diagnosis}")
    st.write(f"**Explanation:** {explanation}")
    st.info(f"**Advice:** {advice}")
