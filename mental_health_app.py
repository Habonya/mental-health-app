import streamlit as st

# ---------------- Page Setup ----------------
st.set_page_config(page_title="Mental Health Support System", layout="centered")

st.title("🧠 Mental Health Support System")
st.write("This is an **advisory tool only** and does not replace professional care. "
         "If you're in crisis, please seek immediate help.")

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
        "result": None,
        "ranked_rules": []
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

# ---------------- Rule Base ----------------
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

# ---------------- Inference (Conflict Resolution) ----------------
def infer_diagnosis():
    s = st.session_state
    all_rules = rules(s)
    matching = [r for r in all_rules if r["conditions"]()]

    if not matching:
        st.session_state.ranked_rules = []
        return {
            "diagnosis": "Unclear",
            "advice": "Consider consulting a mental health professional.",
            "explanation": "Your answers do not match a specific condition.",
            "strategy_used": "No matching rules"
        }

    # Sort by specificity (highest first)
    matching.sort(key=lambda r: r["specificity"], reverse=True)
    st.session_state.ranked_rules = matching  # keep full ranking for audit

    top_specificity = matching[0]["specificity"]
    most_specific = [r for r in matching if r["specificity"] == top_specificity]

    if len(most_specific) > 1:
        strategy = "Specificity + Priority (Lexical Order)"
    else:
        strategy = "Specificity"

    chosen = most_specific[0]

    # Refactoriness
    if s.last_diagnosis == chosen["diagnosis"]:
        return {
            "diagnosis": chosen["diagnosis"],
            "advice": "You have already received this advice. Please monitor changes in your condition.",
            "explanation": "This diagnosis has already been made earlier based on your symptoms.",
            "strategy_used": "Refactoriness (avoiding repeated diagnosis)"
        }

    # Recency
    s.last_diagnosis = chosen["diagnosis"]
    s.history.append(chosen["diagnosis"])
    if len(s.history) > 20:
        s.history = s.history[-20:]

    chosen["strategy_used"] = strategy + " → Recency applied"
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

    immediate, routine, professional = [], [], []

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
            "Try journaling: *What is one small thing I can improve this week?*"
        ]
        routine += [
            "Set a consistent sleep/wake time for the next 7 days.",
            "Plan micro-breaks during work/study blocks (5 min every hour)."
        ]
    else:
        immediate += ["Do one pleasant activity today (music, nature, call a friend)."]
        routine += ["Notice patterns: what improves or worsens your mood?"]

    # Add personalized factors
    if s.workload == "Yes":
        routine.append("Negotiate workload or set clearer boundaries this week.")
    if s.sleep == "Poor" or s.hours < 6:
        routine.append("Improve sleep hygiene: no screens 1 hr before bed, consistent bedtime.")
    if s.worry == "Yes":
        immediate.append("Try 4-7-8 breathing: inhale 4, hold 7, exhale 8 (x4).")
    if s.panic == "Yes":
        immediate.append("Grounding technique: 5 things see, 4 touch, 3 hear, 2 smell, 1 taste.")
    if s.motivation == "Yes":
        routine.append("Use the 2-minute rule: start with a tiny step of the task.")
    if s.interest == "No":
        routine.append("Schedule a small activity you used to enjoy (15–20 min).")

    return {
        "immediate": list(dict.fromkeys(immediate)),
        "routine": list(dict.fromkeys(routine)),
        "professional": list(dict.fromkeys(professional))
    }

# ---------------- Wizard UI ----------------
st.caption("Answer each step below. Your progress saves as you go.")
progress_bar()

# STEP 1
if st.session_state.step == 1:
    st.subheader("Step 1/3 · Sleep")
    st.radio("How is your sleep quality?", ["Select...", "Good", "Poor"], key="sleep")
    st.number_input("How many hours do you sleep per night?",
                    min_value=0, max_value=24, value=st.session_state.hours, key="hours")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(1)
            if ok: next_step()
            else: st.warning(f"⚠️ {msg}")

# STEP 2
elif st.session_state.step == 2:
    st.subheader("Step 2/3 · Mood & Interest")
    st.radio("How is your mood?", ["Select...", "Good", "Low"], key="mood")
    st.radio("Do you feel interested in things?", ["Select...", "Yes", "No"], key="interest")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: st.button("← Back", on_click=prev_step)
    with c2: st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(2)
            if ok: next_step()
            else: st.warning(f"⚠️ {msg}")

# STEP 3
elif st.session_state.step == 3:
    st.subheader("Step 3/3 · Anxiety & Stress Factors")
    st.radio("Are you experiencing persistent worry?", ["Select...", "Yes", "No"], key="worry")
    st.radio("Have you had panic attacks?", ["Select...", "Yes", "No"], key="panic")
    st.radio("Is your workload high?", ["Select...", "Yes", "No"], key="workload")
    st.radio("Are you feeling tired often?", ["Select...", "Yes", "No"], key="tired")
    st.radio("Do you lack motivation?", ["Select...", "Yes", "No"], key="motivation")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: st.button("← Back", on_click=prev_step)
    with c2: st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Run Assessment ✅"):
            ok, msg = validate_step(3)
            if ok: st.session_state.result = infer_diagnosis()
            else: st.warning(f"⚠️ {msg}")

# ---------------- Results & Advice ----------------
if st.session_state.result:
    res = st.session_state.result
    st.markdown("---")
    st.subheader("📝 Assessment Result")
    st.write(f"**Diagnosis:** {res['diagnosis']}")
    st.write(f"**Explanation:** {res['explanation']}")
    st.write(f"**Conflict Resolution Strategy Used:** {res['strategy_used']}")
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
    with st.expander("🗂️ Reasoning Path (Audit Trail)"):
        st.write("Past diagnoses in this session:")
        for i, diag in enumerate(st.session_state.history, 1):
            st.write(f"{i}. {diag}")
        if st.session_state.ranked_rules:
            st.write("---")
            st.write("Rules considered (ranked by specificity):")
            for r in st.session_state.ranked_rules:
                st.write(f"- {r['diagnosis']} (specificity {r['specificity']})")

    st.button("Start New Assessment", on_click=reset_assessment)
