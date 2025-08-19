import streamlit as st

# ---------------- Page Setup ----------------
st.set_page_config(page_title="Mental Health Support System", layout="centered")

st.title("🧠 Mental Health Support System")
st.write("This is an **advisory tool only** and does not replace professional care. If you're in crisis, please seek immediate help.")

# ---------------- Session State Defaults ----------------
def _ensure_defaults():
    defaults = {
        "step": 1,
        "sleep": "Select...",
        "hours": 0,
        "mood": "Select...",
        "interest": "Select...",
        "worry": "Select...",
        "panic": "Select...",
        "workload": "Select...",
        "tired": "Select...",
        "motivation": "Select...",
        "last_diagnosis": None,
        "history": [],
        "result": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_ensure_defaults()

# ---------------- Helpers: Navigation & Validation ----------------
TOTAL_STEPS = 3

def progress_bar():
    st.progress((st.session_state.step - 1) / TOTAL_STEPS)

def next_step():
    if st.session_state.step < TOTAL_STEPS:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 1:
        st.session_state.step -= 1

def reset_assessment():
    keep_keys = ("last_diagnosis", "history")
    last = {k: st.session_state[k] for k in keep_keys if k in st.session_state}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _ensure_defaults()
    for k, v in last.items():
        st.session_state[k] = v
    st.experimental_rerun()

def validate_step(step):
    """Return (ok, msg) for the current step."""
    s = st.session_state
    if step == 1:
        if s.sleep == "Select...":
            return False, "Please select your sleep quality."
        if s.hours == 0:
            return False, "Please enter your average sleep hours (non-zero)."
    elif step == 2:
        if s.mood == "Select...":
            return False, "Please select your current mood."
        if s.interest == "Select...":
            return False, "Please indicate if you feel interested in things."
    elif step == 3:
        for field, label in [
            ("worry", "persistent worry"),
            ("panic", "panic attacks"),
            ("workload", "workload"),
            ("tired", "tiredness"),
            ("motivation", "motivation")
        ]:
            if st.session_state[field] == "Select...":
                return False, f"Please answer the question about {label}."
    return True, ""

# ---------------- Rule Base (with specificity) ----------------
def rules(s):
    return [
        {
            "conditions": lambda: s.worry == "Yes" and s.panic == "Yes",
            "diagnosis": "Anxiety",
            "advice": "Try deep breathing, regular physical activity, and consider professional support.",
            "explanation": "Persistent worry and panic attacks are core indicators of anxiety disorders.",
            "specificity": 3
        },
        {
            "conditions": lambda: s.sleep == "Poor" and s.mood == "Low" and s.interest == "No",
            "diagnosis": "Depression",
            "advice": "Consider therapy, maintain a regular sleep routine, and stay connected with loved ones.",
            "explanation": "Poor sleep, low mood, and loss of interest are hallmark symptoms of depression.",
            "specificity": 4
        },
        {
            "conditions": lambda: s.workload == "Yes" and s.tired == "Yes" and s.motivation == "Yes",
            "diagnosis": "Burnout",
            "advice": "Reduce workload, take breaks, and rest. Seek professional support if symptoms persist.",
            "explanation": "High workload + tiredness + lack of motivation suggests burnout.",
            "specificity": 3
        },
        {
            "conditions": lambda: s.sleep == "Poor" and s.tired == "Yes" and s.hours < 5,
            "diagnosis": "Sleep Deprivation",
            "advice": "Aim for 6–8 hours of quality sleep. Reduce screen time before bed.",
            "explanation": "Poor sleep, tiredness, and <5 hours rest strongly suggest sleep deprivation.",
            "specificity": 4
        },
        {
            "conditions": lambda: s.worry == "Yes" and s.mood == "Low" and s.tired == "Yes",
            "diagnosis": "Stress Overload",
            "advice": "Try journaling, walking, or meditation. Seek help if stress continues.",
            "explanation": "Persistent worry, low mood, and fatigue suggest overwhelming stress.",
            "specificity": 3
        },
        {
            "conditions": lambda: s.mood == "Low" and s.motivation == "Yes" and s.interest == "No",
            "diagnosis": "Possible Depression",
            "advice": "Monitor your symptoms and consider professional consultation.",
            "explanation": "Low mood, loss of interest, and lack of motivation are depressive tendencies.",
            "specificity": 2
        },
        {
            "conditions": lambda: s.tired == "Yes" and s.motivation == "Yes" and s.sleep == "Good",
            "diagnosis": "Emotional Fatigue",
            "advice": "Take breaks, enjoy hobbies, and stay socially connected.",
            "explanation": "Good sleep but tired + unmotivated indicates emotional fatigue.",
            "specificity": 2
        },
        {
            "conditions": lambda: s.worry == "Yes" or s.tired == "Yes" or s.mood == "Low" or s.motivation == "Yes",
            "diagnosis": "Mild Emotional Distress",
            "advice": "Talk to someone, get good sleep, and care for your physical health.",
            "explanation": "Some level of worry, tiredness, or low mood indicates mild distress.",
            "specificity": 1
        }
    ]

# ---------------- Inference (with conflict resolution) ----------------
def infer_diagnosis():
    s = st.session_state
    matching = [r for r in rules(s) if r["conditions"]()]

    if not matching:
        result = {
            "diagnosis": "Unclear",
            "advice": "Consider consulting a mental health professional.",
            "explanation": "Your answers do not match a specific condition."
        }
        return result

    # Strategy 1: Specificity
    matching.sort(key=lambda r: r["specificity"], reverse=True)
    chosen = matching[0]

    # Strategy 2: Lexical order = list order (stable sort)

    # Strategy 3: Refactoriness
    if s.last_diagnosis == chosen["diagnosis"]:
        return {
            "diagnosis": chosen["diagnosis"],
            "advice": "You have already received this advice. Please monitor changes in your condition.",
            "explanation": "This diagnosis has already been made earlier based on your symptoms."
        }

    # Strategy 4: Recency
    s.last_diagnosis = chosen["diagnosis"]
    s.history.append(chosen["diagnosis"])

    return chosen

# ---------------- Personalized Advice Tiers ----------------
SEVERITY = {
    "Depression": 3,
    "Anxiety": 3,
    "Burnout": 2,
    "Stress Overload": 2,
    "Sleep Deprivation": 2,
    "Possible Depression": 2,
    "Emotional Fatigue": 1,
    "Mild Emotional Distress": 1,
    "Unclear": 1
}

def build_personalized_advice(result):
    s = st.session_state
    dx = result["diagnosis"]
    severity = SEVERITY.get(dx, 1)

    # Base tiers
    immediate = []
    routine = []
    professional = []

    # General tiered suggestions
    if severity >= 3:
        immediate += [
            "Consider reaching out to a trusted person today.",
            "Practice a short grounding/breathing exercise (3–5 minutes)."
        ]
        professional += [
            "Book an appointment with a licensed mental health professional.",
            "If you feel unsafe or in crisis, seek immediate help."
        ]
    elif severity == 2:
        immediate += [
            "Schedule a short break or light activity today (walk, stretch).",
            "Try a simple journaling prompt: *What is one small thing I can improve this week?*"
        ]
        routine += [
            "Set a consistent sleep/wake time for the next 7 days.",
            "Plan micro-breaks during work/study blocks (5 min every hour)."
        ]
    else:
        immediate += [
            "Do one pleasant activity today (music, nature, call a friend)."
        ]
        routine += [
            "Keep noticing patterns: what improves or worsens your mood?",
        ]

    # Personalized add-ons from inputs
    if s.workload == "Yes":
        routine.append("Negotiate workload or set clearer boundaries for the next sprint/week.")
    if s.sleep == "Poor" or s.hours < 6:
        routine.append("Follow basic sleep hygiene: limit screens 1 hr before bed, keep the room dark, consistent bedtime.")
    if s.worry == "Yes":
        immediate.append("Try a 4-7-8 breathing cycle (4 in, 7 hold, 8 out) x4 rounds.")
    if s.panic == "Yes":
        immediate.append("Use a grounding technique: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.")
    if s.motivation == "Yes":
        routine.append("Use the 2-minute rule: start with a tiny version of the task to overcome inertia.")
    if s.interest == "No":
        routine.append("Schedule one small activity you used to enjoy (15–20 minutes).")

    # Return sections
    return {
        "immediate": list(dict.fromkeys(immediate)),  # de-duplicate
        "routine": list(dict.fromkeys(routine)),
        "professional": list(dict.fromkeys(professional))
    }

# ---------------- Wizard UI ----------------
st.caption("Answer each step below. Your progress saves as you go.")
progress_bar()

# STEP 1
if st.session_state.step == 1:
    st.subheader("Step 1/3 · Sleep")
    st.radio("How is your sleep quality?",
             ["Select...", "Good", "Poor"],
             key="sleep")
    st.number_input("How many hours do you sleep per night?",
                    min_value=0, max_value=24, value=st.session_state.hours, key="hours")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(1)
            if ok:
                next_step()
            else:
                st.warning(f"⚠️ {msg}")

# STEP 2
elif st.session_state.step == 2:
    st.subheader("Step 2/3 · Mood & Interest")
    st.radio("How is your mood?",
             ["Select...", "Good", "Low"],
             key="mood")
    st.radio("Do you feel interested in things?",
             ["Select...", "Yes", "No"],
             key="interest")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.button("← Back", on_click=prev_step)
    with c2:
        st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(2)
            if ok:
                next_step()
            else:
                st.warning(f"⚠️ {msg}")

# STEP 3
elif st.session_state.step == 3:
    st.subheader("Step 3/3 · Anxiety & Stress Factors")
    st.radio("Are you experiencing persistent worry?", ["Select...", "Yes", "No"], key="worry")
    st.radio("Have you had panic attacks?", ["Select...", "Yes", "No"], key="panic")
    st.radio("Is your workload high?", ["Select...", "Yes", "No"], key="workload")
    st.radio("Are you feeling tired often?", ["Select...", "Yes", "No"], key="tired")
    st.radio("Do you lack motivation?", ["Select...", "Yes", "No"], key="motivation")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.button("← Back", on_click=prev_step)
    with c2:
        st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Run Assessment ✅"):
            ok, msg = validate_step(3)
            if not ok:
                st.warning(f"⚠️ {msg}")
            else:
                st.session_state.result = infer_diagnosis()

# ---------------- Results & Advice ----------------
if st.session_state.result:
    res = st.session_state.result
    st.markdown("---")
    st.subheader("📝 Assessment Result")
    st.write(f"**Diagnosis:** {res['diagnosis']}")
    st.write(f"**Explanation:** {res['explanation']}")
    st.info(f"**Base Advice:** {res['advice']}")

    # Personalized tiers
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

    # Transparency
    with st.expander("🗂️ Reasoning Path (History)"):
        st.write("Past diagnoses in this session:")
        for i, diag in enumerate(st.session_state.history, 1):
            st.write(f"{i}. {diag}")

    # Start again
    st.button("Start New Assessment", on_click=reset_assessment)
