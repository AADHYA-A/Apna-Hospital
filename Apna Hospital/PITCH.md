# Hackathon pitch cheat-sheet

## One-liner
"Apna Hospital tells you how urgently to act, not just what you might have."

## 90-second demo script
1. Type: *"bad headache, my stomach is burning, vision is blurry but no fever"* -> chips appear live ("no fever" is ignored).
2. Analyse -> top-3 with scores, triage banner, severity score.
3. Tap a follow-up chip -> the result re-ranks instantly (the "20 questions" moment).
4. Open **Why this match** -> explainability.
5. Click the **chest pain** example -> red emergency banner and Call 112 button (the safety layer overrides the model).
6. Download the PDF report. Toggle dark mode. Show it on your phone.

## Talking points for judges
- **Safety first:** a deterministic red-flag layer sits above the ML model.
- **Explainable:** every result shows matched and missing symptoms.
- **We audited the data:** found and fixed a one-row shift that gave Heart attack the varicose-vein treatments.
- **Honest about limits:** the About page states the dataset has only 304 distinct patterns, so the 100% CV score is not real-world accuracy. Judges reward this.
- **Deployable:** one-click Render / Docker / HF Spaces, open JSON API.
- **Privacy:** no server-side storage of symptoms.

## Likely questions
- *Is it accurate?* It is a decision-support demo on a public educational dataset; we show confidence and always route red flags to emergency care.
- *Why random forest?* It gives usable probabilities for ranking and follow-up selection, and runs fast on CPU.
- *What next?* Hindi/Kannada UI, clinician-validated data, telemedicine hand-off, nearby-hospital lookup.

## Before you submit
- Replace the placeholder contact email and add your repo/demo links on /contact and /developer.
- Deploy and test /health plus one prediction on the live URL.
