"""Prediction + triage engine for Apna Hospital."""
import ast, difflib, os, re
import joblib, numpy as np, pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: pd.read_csv(os.path.join(BASE, "datasets", f))


def key(s):
    s = str(s).lower().replace("diseae", "disease").replace("paroymsal", "paroxysmal")
    return re.sub(r"[^a-z0-9]", "", s)


DISPLAY = {"Peptic ulcer diseae": "Peptic ulcer disease", "Osteoarthristis": "Osteoarthritis",
           "(vertigo) Paroymsal  Positional Vertigo": "Positional vertigo (BPPV)",
           "Dimorphic hemmorhoids(piles)": "Haemorrhoids (piles)", "hepatitis A": "Hepatitis A",
           "Paralysis (brain hemorrhage)": "Paralysis (brain haemorrhage)", "GERD": "GERD (acid reflux)",
           "AIDS": "HIV / AIDS"}


def pretty_disease(d):
    d = d.strip()
    return DISPLAY.get(d, d)


def pretty_symptom(s):
    s = re.sub(r"[_\s]+", " ", s.replace(".1", "")).strip()
    s = s.replace("typhos", "typhos").replace("feets", "feet").replace("extremeties", "extremities")
    s = s.replace("dischromic", "discoloured").replace("scurring", "scarring").replace("diarrhoea", "diarrhoea")
    return s[:1].upper() + s[1:]


# ---------- load model & data ----------
def _load_bundle():
    p = os.path.join(BASE, "models", "model.joblib")
    try:
        return joblib.load(p)
    except Exception:  # version mismatch / missing -> retrain transparently
        from train import train
        return train()[0]


B = _load_bundle()
MODEL, FEATURES, CLASSES = B["model"], B["features"], B["classes"]
FIDX = {f: i for i, f in enumerate(FEATURES)}
HIDDEN = {"fluid_overload.1"}
SYMPTOMS = [f for f in FEATURES if f not in HIDDEN]

train_df = D("Training.csv")
train_df.columns = [c.strip() for c in train_df.columns]
train_df["prognosis"] = train_df["prognosis"].str.strip()
PREV = train_df.groupby("prognosis")[FEATURES].mean()          # symptom prevalence per disease
GLOBAL_PREV = PREV.mean()

sev = D("Symptom-severity.csv")
SEVERITY = {r.Symptom.strip(): int(r.weight) for r in sev.itertuples() if r.Symptom.strip() != "prognosis"}
SEVERITY["fluid_overload.1"] = SEVERITY.get("fluid_overload", 4)


def _by_key(df, col):
    df = df.copy(); df["_k"] = df[col].map(key); return df


DESC = _by_key(D("description.csv"), "Disease")
PREC = _by_key(D("precautions_df.csv"), "Disease")
MEDS = _by_key(D("medications.csv"), "Disease")
DIET = _by_key(D("diets.csv"), "Disease")
WORK = _by_key(D("workout_df.csv"), "disease")


def _lst(x):
    try:
        v = ast.literal_eval(x); return [str(i).strip() for i in v]
    except Exception:
        return [str(x)]


def disease_info(name):
    k = key(name)
    desc = " ".join(DESC[DESC._k == k]["Description"].tolist())
    pre = PREC[PREC._k == k][["Precaution_1", "Precaution_2", "Precaution_3", "Precaution_4"]].values
    pre = [str(p).strip().capitalize() for p in (pre[0] if len(pre) else []) if str(p) != "nan"]
    meds = _lst(MEDS[MEDS._k == k]["Medication"].iloc[0]) if (MEDS._k == k).any() else []
    diet = _lst(DIET[DIET._k == k]["Diet"].iloc[0]) if (DIET._k == k).any() else []
    work = [str(w).strip() for w in WORK[WORK._k == k]["workout"].tolist()]
    return {"description": desc, "precautions": pre, "medications": meds, "diet": diet, "lifestyle": work}


# ---------- triage knowledge ----------
EMERGENCY_SYMPTOMS = {
    "chest_pain": "Chest pain can signal a heart problem",
    "coma": "Loss of consciousness",
    "altered_sensorium": "Confusion or altered consciousness",
    "slurred_speech": "Slurred speech can be a stroke sign",
    "weakness_of_one_body_side": "One-sided weakness can be a stroke sign",
    "blood_in_sputum": "Coughing up blood",
    "stomach_bleeding": "Internal bleeding",
    "acute_liver_failure": "Possible acute liver failure",
}
URGENT_SYMPTOMS = {"breathlessness", "bloody_stool", "fast_heart_rate", "palpitations", "high_fever",
                   "yellowing_of_eyes", "loss_of_balance", "visual_disturbances"}
EMERGENCY_DISEASES = {"Heart attack", "Paralysis (brain hemorrhage)"}

SPECIALIST = {
    "Fungal infection": "Dermatologist", "Allergy": "Allergist / General physician", "GERD": "Gastroenterologist",
    "Chronic cholestasis": "Gastroenterologist / Hepatologist", "Drug Reaction": "General physician (urgent)",
    "Peptic ulcer diseae": "Gastroenterologist", "AIDS": "Infectious disease specialist",
    "Diabetes": "Endocrinologist / Diabetologist", "Gastroenteritis": "General physician",
    "Bronchial Asthma": "Pulmonologist", "Hypertension": "Cardiologist", "Migraine": "Neurologist",
    "Cervical spondylosis": "Orthopaedic / Physiotherapist", "Paralysis (brain hemorrhage)": "Neurologist (emergency)",
    "Jaundice": "Gastroenterologist / Hepatologist", "Malaria": "General physician / Infectious disease",
    "Chicken pox": "General physician / Dermatologist", "Dengue": "General physician",
    "Typhoid": "General physician", "Tuberculosis": "Pulmonologist", "Common Cold": "General physician",
    "Pneumonia": "Pulmonologist", "Dimorphic hemmorhoids(piles)": "Proctologist / General surgeon",
    "Heart attack": "Cardiologist (emergency)", "Varicose veins": "Vascular surgeon",
    "Hypothyroidism": "Endocrinologist", "Hyperthyroidism": "Endocrinologist", "Hypoglycemia": "Endocrinologist",
    "Osteoarthristis": "Orthopaedic", "Arthritis": "Rheumatologist",
    "(vertigo) Paroymsal  Positional Vertigo": "ENT / Neurologist", "Acne": "Dermatologist",
    "Urinary tract infection": "Urologist / General physician", "Psoriasis": "Dermatologist",
    "Impetigo": "Dermatologist",
}


def specialist_for(d):
    d = d.strip()
    if d.startswith("hepatitis") or d.startswith("Hepatitis") or d == "Alcoholic hepatitis":
        return "Gastroenterologist / Hepatologist"
    for k, v in SPECIALIST.items():
        if k.strip() == d:
            return v
    return "General physician"


# ---------- natural-language parsing ----------
SYNONYMS = {
    "stomach ache": "stomach_pain", "tummy ache": "stomach_pain", "tummy pain": "stomach_pain", "stomach ache": "stomach_pain",
    "belly ache": "belly_pain", "throwing up": "vomiting", "threw up": "vomiting", "puking": "vomiting", "vomit": "vomiting",
    "loose motion": "diarrhoea", "loose stool": "diarrhoea", "diarrhea": "diarrhoea", "runs": "diarrhoea",
    "tired": "fatigue", "exhausted": "fatigue", "tiredness": "fatigue", "no energy": "lethargy",
    "sore throat": "throat_irritation", "scratchy throat": "throat_irritation", "body ache": "muscle_pain",
    "body pain": "muscle_pain", "muscle ache": "muscle_pain", "short of breath": "breathlessness",
    "shortness of breath": "breathlessness", "difficulty breathing": "breathlessness", "can't breathe": "breathlessness",
    "breathing problem": "breathlessness", "burning urination": "burning_micturition", "burning while peeing": "burning_micturition",
    "burning pee": "burning_micturition", "painful urination": "burning_micturition", "itchy": "itching", "itch": "itching",
    "rash": "skin_rash", "dizzy": "dizziness", "light headed": "dizziness", "lightheaded": "dizziness",
    "pimples": "pus_filled_pimples", "zits": "blackheads", "sneezing": "continuous_sneezing", "sneeze": "continuous_sneezing",
    "stuffy nose": "congestion", "blocked nose": "congestion", "nose block": "congestion", "cold": "runny_nose",
    "fever": "high_fever", "high temperature": "high_fever", "slight fever": "mild_fever", "low grade fever": "mild_fever",
    "low fever": "mild_fever", "shaking": "shivering", "yellow eyes": "yellowing_of_eyes", "yellow skin": "yellowish_skin",
    "jaundiced": "yellowish_skin", "heart racing": "fast_heart_rate", "racing heart": "fast_heart_rate",
    "heart pounding": "palpitations", "chest tightness": "chest_pain", "chest pressure": "chest_pain",
    "neck stiffness": "stiff_neck", "gas": "passage_of_gases", "bloating": "distention_of_abdomen",
    "bloated": "distention_of_abdomen", "heartburn": "acidity", "acid reflux": "acidity", "no appetite": "loss_of_appetite",
    "not hungry": "loss_of_appetite", "weak": "muscle_weakness", "sleepy": "lethargy", "sad": "depression",
    "low mood": "depression", "worried": "anxiety", "nervous": "anxiety", "dry cough": "cough", "coughing": "cough",
    "sweaty": "sweating", "night sweats": "sweating", "puffy face": "puffy_face_and_eyes", "swollen face": "puffy_face_and_eyes",
    "swollen feet": "swollen_legs", "swollen ankles": "swollen_legs", "joint ache": "joint_pain", "knee ache": "knee_pain",
    "pain in knee": "knee_pain", "back ache": "back_pain", "backache": "back_pain", "head ache": "headache",
    "head pain": "headache", "blurry vision": "blurred_and_distorted_vision", "blurred vision": "blurred_and_distorted_vision",
    "red eyes": "redness_of_eyes", "watery eyes": "watering_from_eyes", "peeing a lot": "polyuria",
    "frequent urination": "polyuria", "very thirsty": "excessive_hunger", "vertigo": "spinning_movements",
    "room spinning": "spinning_movements", "spinning": "spinning_movements", "can't smell": "loss_of_smell",
    "lost smell": "loss_of_smell", "blood in stool": "bloody_stool", "constipated": "constipation",
    "blisters": "blister", "peeling skin": "skin_peeling", "nausea": "nausea", "nauseous": "nausea",
    "feel sick": "nausea", "weight loss": "weight_loss", "lost weight": "weight_loss", "gained weight": "weight_gain",
}
NEG = re.compile(r"\b(no|not|without|never|don'?t have|doesn'?t have|denies|zero)\b[\w\s,']{0,18}$")
LABELS = {s: re.sub(r"[_\s]+", " ", s.replace(".1", "")).strip().lower() for s in SYMPTOMS}
LABEL_ITEMS = sorted(LABELS.items(), key=lambda kv: -len(kv[1]))
_syn_items = sorted(SYNONYMS.items(), key=lambda kv: -len(kv[0]))


def parse_text(text):
    """Turn free text like 'bad headache, I keep throwing up but no fever' into symptom keys."""
    t = " " + re.sub(r"\s+", " ", text.lower().replace("_", " ")) + " "
    found, taken = [], []

    def overlaps(a, b):
        return any(not (b <= s or a >= e) for s, e in taken)

    def add(sym, a, b):
        if sym in FIDX and not overlaps(a, b):
            taken.append((a, b))
            if not NEG.search(t[max(0, a - 28):a]) and sym not in found:
                found.append(sym)

    for sym, lab in LABEL_ITEMS:
        for m in re.finditer(r"(?<![a-z])" + re.escape(lab) + r"(?![a-z])", t):
            add(sym, m.start(), m.end())
    for phrase, sym in _syn_items:
        for m in re.finditer(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", t):
            add(sym, m.start(), m.end())
    # fuzzy fallback on 1-3 word n-grams for typos ("hedache", "vomitting")
    words = [(m.group(), m.start(), m.end()) for m in re.finditer(r"[a-z']+", t)]
    vocab = list(LABELS.values()) + list(SYNONYMS)
    lab2sym = {v: k for k, v in LABELS.items()}
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            a, b = words[i][1], words[i + n - 1][2]
            if overlaps(a, b):
                continue
            gram = " ".join(w[0] for w in words[i:i + n])
            if len(gram) < 5:
                continue
            c = difflib.get_close_matches(gram, vocab, n=1, cutoff=0.86)
            if c:
                add(lab2sym.get(c[0]) or SYNONYMS[c[0]], a, b)
    return found


# ---------- prediction ----------
def vectorize(symptoms):
    v = np.zeros((1, len(FEATURES)))
    for s in symptoms:
        if s in FIDX:
            v[0, FIDX[s]] = 1
    return v


def triage(symptoms, top):
    score = sum(SEVERITY.get(s, 1) for s in symptoms)
    flags = [EMERGENCY_SYMPTOMS[s] for s in symptoms if s in EMERGENCY_SYMPTOMS]
    urgent = [s for s in symptoms if s in URGENT_SYMPTOMS]
    emergency_dx = top and top["raw"].strip() in {d.strip() for d in EMERGENCY_DISEASES} and top["probability"] >= 0.25
    if flags or emergency_dx:
        level, title = "emergency", "Seek emergency care now"
        msg = "Call 112 (or 108 for an ambulance in India) or go to the nearest emergency department. Don't drive yourself."
    elif urgent or score >= 28:
        level, title = "urgent", "See a doctor within 24 hours"
        msg = "Your symptoms deserve prompt medical attention. Book a same-day appointment or visit an urgent-care clinic."
    elif score >= 12:
        level, title = "moderate", "Book a doctor's appointment"
        msg = "Arrange a consultation in the next few days, sooner if symptoms worsen."
    else:
        level, title = "mild", "Likely manageable at home"
        msg = "Rest, hydrate and monitor. See a doctor if symptoms persist beyond 2-3 days or get worse."
    return {"level": level, "title": title, "message": msg, "severity_score": int(score), "red_flags": flags}


def follow_ups(symptoms, probs, k=6):
    order = np.argsort(probs)[::-1][:4]
    cand = {}
    for i in order:
        p = probs[i]
        if p < 0.03:
            continue
        prev = PREV.loc[CLASSES[i]]
        for s in SYMPTOMS:
            if s in symptoms:
                continue
            cand[s] = cand.get(s, 0) + p * prev[s] * (1 - GLOBAL_PREV[s])
    best = sorted(cand.items(), key=lambda kv: -kv[1])[:k]
    return [{"key": s, "label": pretty_symptom(s)} for s, sc in best if sc > 0.02]


def predict(symptoms):
    symptoms = [s for s in dict.fromkeys(symptoms) if s in FIDX]
    if not symptoms:
        raise ValueError("no valid symptoms")
    probs = MODEL.predict_proba(vectorize(symptoms))[0]
    order = np.argsort(probs)[::-1]
    results = []
    for i in order[:3]:
        raw = CLASSES[i]
        prev = PREV.loc[raw]
        typical = [s for s in prev.sort_values(ascending=False).index if prev[s] >= 0.3 and s not in HIDDEN][:8]
        results.append({
            "raw": raw, "name": pretty_disease(raw), "probability": round(float(probs[i]), 4),
            "matched": [{"key": s, "label": pretty_symptom(s)} for s in symptoms if prev[s] > 0],
            "unmatched_typical": [{"key": s, "label": pretty_symptom(s)} for s in typical if s not in symptoms],
            "specialist": specialist_for(raw), **disease_info(raw),
        })
    tri = triage(symptoms, results[0])
    return {
        "symptoms": [{"key": s, "label": pretty_symptom(s), "severity": SEVERITY.get(s, 1)} for s in symptoms],
        "results": results, "triage": tri, "follow_ups": follow_ups(symptoms, probs),
        "confidence_note": ("Low confidence: add more symptoms to sharpen the result."
                            if results[0]["probability"] < 0.4 else
                            "Moderate confidence: answer the follow-up questions to confirm." if results[0]["probability"] < 0.7
                            else "Strong pattern match with the training data."),
    }
