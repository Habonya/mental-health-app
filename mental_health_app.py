import streamlit as st

# ====================== Page Setup ======================
st.set_page_config(page_title="Mental Health Support System", layout="centered")

st.title("🧠 Mental Health Support System")
st.write(
    "This is an **advisory tool only** and does not replace professional care. "
    "If you're in crisis or feel unsafe, seek immediate help."
)

# ====================== Session State Defaults ======================
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
        "last_diagnosis": None,   # for Refractoriness/Recency
        "result": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_ensure_defaults()

# ====================== Helpers: Navigation & Validation ======================
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
    keep = {"last_diagnosis": st.session_state.get("last_diagnosis")}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _ensure_defaults()
    st.session_state.update({k: v for k, v in keep.items() if v is not None})
    st.experimental_rerun()

def validate_step(step):
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
            ("motivation", "motivation"),
        ]:
            if st.session_state[field] == "Select...":
                return False, f"Please answer the question about {label}."
    return True, ""

# ====================== Rule Base ======================
# Each rule has:
# - conditions: boolean function
# - diagnosis, explanation, advice
# - specificity: more conditions -> higher number
# - priority: used when multiple rules have same specificity (domain importance)
def rules(s):
    return [
        {
            "conditions": lambda: s.worry == "Yes" and s.panic == "Yes",
            "diagnosis": "Anxiety",
            "explanation": (
                "Your answers indicate persistent worry and panic symptoms. "
                "Anxiety disorders are commonly characterized by excessive worry "
                "and physical arousal (e.g., racing heart, shortness of breath), "
                "as described in widely used clinical guidelines (e.g., DSM-5/WHO)."
            ),
            "advice": "Practice slow breathing/grounding and consider speaking with a clinician.",
            "specificity": 3,
            "priority": 3,
        },
        {
            "conditions": lambda: s.sleep == "Poor" and s.mood == "Low" and s.interest == "No",
            "diagnosis": "Depression",
            "explanation": (
                "Low mood, loss of interest/pleasure, and sleep disturbance align with "
                "common features of depressive episodes described in DSM-5/WHO. "
                "These symptoms often last most days for at least two weeks and impact daily functioning."
            ),
            "advice": "Keep routine, stay connected, and arrange an evaluation with a mental health professional.",
            "specificity": 4,
            "priority": 4,
        },
        {
            "conditions": lambda: s.workload == "Yes" and s.tired == "Yes" and s.motivation == "Yes",
            "diagnosis": "Burnout",
            "explanation": (
                "High, sustained workload with fatigue and reduced motivation suggests work-related burnout, "
                "an occupational phenomenon characterized by exhaustion and reduced efficacy."
            ),
            "advice": "Reduce load where possible, take restorative breaks, and discuss support options at work/school.",
            "specificity": 3,
            "priority": 3,
        },
        {
            "conditions": lambda: s.sleep == "Poor" and s.tired == "Yes" and s.hours < 5,
            "diagnosis": "Sleep Deprivation",
            "explanation": (
                "Poor sleep quality with less than ~5 hours is consistent with sleep deprivation, "
                "which commonly leads to fatigue, poor concentration, and mood changes."
            ),
            "advice": "Prioritize sleep hygiene and aim for 6–8 hours consistently.",
            "specificity": 4,
            "priority": 4,
        },
        {
            "conditions": lambda: s.worry == "Yes" and s.mood == "Low" and s.tired == "Yes",
            "diagnosis": "Stress Overload",
            "explanation": (
                "Persistent stress can present as ongoing worry, lowered mood, and fatigue. "
                "Managing stressors and recovery time helps prevent escalation."
            ),
            "advice": "Try journaling, light activity, and structured breaks; review stressors you can change.",
            "specificity": 3,
            "priority": 2,
        },
        {
            "conditions": lambda: s.mood == "Low" and s.motivation == "Yes" and s.interest == "No",
            "diagnosis": "Possible Depression",
            "explanation": (
                "Low mood with loss of interest and reduced motivation is concerning for depressive patterns, "
                "though your answers may not meet full clinical criteria."
            ),
            "advice": "Monitor symptoms and seek a professional assessment.",
            "specificity": 2,
            "priority": 2,
        },
        {
            "conditions": lambda: s.tired == "Yes" and s.motivation == "Yes" and s.sleep == "Good",
            "diagnosis": "Emotional Fatigue",
            "explanation": (
                "Even with adequate sleep, persistent tiredness and low drive can reflect emotional exhaustion "
                "from prolonged strain."
            ),
            "advice": "Plan pleasant activities, set small goals, and connect with supportive people.",
            "specificity": 2,
            "priority": 1,
        },
        {
            "conditions": lambda: (
                s.worry == "Yes" or s.tired == "Yes" or s.mood == "Low" or s.motivation == "Yes"
            ),
            "diagnosis": "Mild Emotional Distress",
            "explanation": (
                "Your answers suggest some emotional strain, but not a specific pattern. "
                "Simple self-care and monitoring can help."
            ),
            "advice": "Talk to someone you trust and prioritize rest and routine.",
            "specificity": 1,
            "priority": 1,
        },
    ]

# ====================== Inference with Conflict Resolution ======================
def infer_diagnosis():
    """
    Conflict resolution:
    1) Specificity: choose rule with highest 'specificity'
    2) Priority: tie-break with domain 'priority'
    3) Lexical order: final tie-break is the code order (stable sort)
    4) Refractoriness: if same as last diagnosis, return a minimal/avoid-repeat message
    5) Recency: store the latest diagnosis in session state
    """
    s = st.session_state
    matching = [r for r in rules(s) if r["conditions"]()]

    if not matching:
        return {
            "diagnosis": "Unclear",
            "explanation": (
                "Your answers do not match a specific pattern in this tool. "
                "Consider discussing your concerns with a licensed professional."
            ),
            "advice": "Keep tracking sleep, mood, and energy; bring notes to your appointment."
        }

    # Sort by specificity then priority (descending). Python's sort is stable, so original order is the last tiebreaker.
    matching.sort(key=lambda r: (r["specificity"], r["priority"]), reverse=True)
    chosen = matching[0]

    # Refractoriness: avoid re-surfacing the same diagnosis immediately
    if s.last_diagnosis == chosen["diagnosis"]:
        return {
            "diagnosis": chosen["diagnosis"],
            "explanation": "This is the same result as your previous assessment with similar answers.",
            "advice": "Monitor changes and consult a licensed clinician for a full evaluation."
        }

    # Recency: remember last diagnosis
    s.last_diagnosis = chosen["diagnosis"]
    return chosen

# ====================== Personalized Advice Tiers ======================
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
    if s.workload == "Yes":
        routine.append("Review workload and set boundaries for the coming week.")
    if s.sleep == "Poor" or s.hours < 6:
        routine.append("Follow basic sleep hygiene: limit screens 1 hour before bed, keep the room dark, consistent bedtime.")
    if s.worry == "Yes":
        immediate.append("Try a 4-7-8 breathing cycle (inhale 4s, hold 7s, exhale 8s) for 4 rounds.")
    if s.panic == "Yes":
        immediate.append("Use a grounding technique: 5 things you see, 4 touch, 3 hear, 2 smell, 1 taste.")
    if s.motivation == "Yes":
        routine.append("Use the 2-minute rule: start with a tiny version of the task to overcome inertia.")
    if s.interest == "No":
        routine.append("Schedule one small activity you used to enjoy (15–20 minutes).")

    # De-duplicate while keeping order
    dedup = lambda items: list(dict.fromkeys(items))
    return {
        "immediate": dedup(immediate),
        "routine": dedup(routine),
        "professional": dedup(professional),
    }

# ====================== Wizard UI ======================
st.caption("Answer each step below. Your progress saves as you go.")
progress_bar()

# STEP 1
if st.session_state.step == 1:
    st.subheader("Step 1/3 · Sleep")
    st.radio("How is your sleep quality?", ["Select...", "Good", "Poor"], key="sleep")
    st.number_input(
        "How many hours do you sleep per night?",
        min_value=0, max_value=24, value=st.session_state.hours, key="hours",
    )
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(1)
            st.warning(f"⚠️ {msg}") if not ok else next_step()

# STEP 2
elif st.session_state.step == 2:
    st.subheader("Step 2/3 · Mood & Interest")
    st.radio("How is your mood?", ["Select...", "Good", "Low"], key="mood")
    st.radio("Do you feel interested in things?", ["Select...", "Yes", "No"], key="interest")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.button("← Back", on_click=prev_step)
    with c2:
        st.button("Reset", on_click=reset_assessment)
    with c3:
        if st.button("Next →"):
            ok, msg = validate_step(2)
            st.warning(f"⚠️ {msg}") if not ok else next_step()

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

# ====================== Results & Advice ======================
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
