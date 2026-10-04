"""One-off data repair.

The original medications.csv was row-shifted by one starting at 'Hepatitis E' (e.g. Heart attack
listed compression stockings, Pneumonia listed laxatives, Alcoholic hepatitis listed TB drugs).
This script rewrites medications.csv with correct, conservative 'treatment classes' and patches
two wrong precaution rows. Run once; idempotent.
"""
import pandas as pd

M = {
 "Fungal infection": ["Topical antifungal cream (clotrimazole)", "Oral antifungals (fluconazole, terbinafine)", "Medicated antifungal powder"],
 "Allergy": ["Antihistamines", "Nasal corticosteroid sprays", "Decongestants", "Epinephrine auto-injector (severe allergy)", "Allergen immunotherapy"],
 "GERD": ["Antacids", "H2 blockers", "Proton pump inhibitors (PPIs)", "Prokinetics"],
 "Chronic cholestasis": ["Ursodeoxycholic acid", "Cholestyramine (for itching)", "Treat underlying cause"],
 "Drug Reaction": ["Stop the suspected drug (only on medical advice)", "Antihistamines", "Corticosteroids", "Epinephrine (anaphylaxis)"],
 "Peptic ulcer disease": ["Proton pump inhibitors (PPIs)", "H. pylori eradication antibiotics", "H2 blockers", "Antacids", "Cytoprotective agents"],
 "AIDS": ["Antiretroviral therapy (ART)", "Prophylaxis for opportunistic infections"],
 "Diabetes": ["Metformin", "Insulin", "Sulfonylureas", "DPP-4 inhibitors", "GLP-1 receptor agonists"],
 "Gastroenteritis": ["Oral rehydration solution (ORS)", "Antiemetics", "Zinc (children)", "Probiotics", "IV fluids if severely dehydrated"],
 "Bronchial Asthma": ["Reliever inhalers (bronchodilators)", "Inhaled corticosteroids", "Leukotriene modifiers", "Anticholinergics"],
 "Hypertension": ["ACE inhibitors / ARBs", "Calcium channel blockers", "Diuretics", "Beta-blockers"],
 "Migraine": ["Analgesics (paracetamol, NSAIDs)", "Triptans", "Anti-nausea medication", "Preventive medication (specialist-guided)"],
 "Cervical spondylosis": ["Pain relievers", "Muscle relaxants", "Physiotherapy", "Cervical collar (short-term)"],
 "Paralysis (brain hemorrhage)": ["EMERGENCY: hospital care, brain imaging", "Blood-pressure control", "Surgery if needed", "Rehabilitation (physio / occupational therapy)"],
 "Jaundice": ["Treat the underlying cause", "IV fluids", "Antiviral medication (if viral)", "Medicines for itching"],
 "Malaria": ["Antimalarial drugs (artemisinin-based combinations)", "Paracetamol for fever", "IV fluids", "Hospital care for severe malaria"],
 "Chicken pox": ["Paracetamol for fever (avoid aspirin)", "Calamine lotion", "Antihistamines for itch", "Antiviral (acyclovir) in high-risk cases"],
 "Dengue": ["Paracetamol for fever (avoid aspirin / ibuprofen)", "Oral fluids / ORS", "Platelet monitoring", "Hospital care for warning signs"],
 "Typhoid": ["Antibiotics (as prescribed)", "Paracetamol for fever", "Oral / IV fluids", "Typhoid vaccination (prevention)"],
 "hepatitis A": ["Rest and hydration", "Supportive care", "Hepatitis A vaccination (prevention)", "Avoid alcohol and liver-toxic drugs"],
 "Hepatitis B": ["Antivirals (tenofovir / entecavir)", "Regular liver monitoring", "Hepatitis B vaccination (prevention)"],
 "Hepatitis C": ["Direct-acting antivirals", "Regular liver monitoring"],
 "Hepatitis D": ["Pegylated interferon (specialist-guided)", "Hepatitis B vaccination (prevention)", "Regular liver monitoring"],
 "Hepatitis E": ["Rest and hydration", "Supportive care", "Avoid alcohol and liver-toxic drugs", "Specialist care in pregnancy or severe cases"],
 "Alcoholic hepatitis": ["Stop alcohol completely", "Nutritional support", "Corticosteroids (severe cases)", "Hospital care"],
 "Tuberculosis": ["Multi-drug anti-TB therapy (isoniazid, rifampicin, ethambutol, pyrazinamide)", "Full 6-month course is essential", "Free DOTS treatment at government centres (India)"],
 "Common Cold": ["Paracetamol", "Decongestants", "Antihistamines", "Cough suppressants", "Warm fluids and rest"],
 "Pneumonia": ["Antibiotics (bacterial)", "Antipyretics", "Oxygen therapy if needed", "Hospital care for severe cases"],
 "Dimorphic hemmorhoids(piles)": ["Stool softeners / fibre supplements", "Topical creams or suppositories", "Warm sitz baths", "Procedures or surgery if severe"],
 "Heart attack": ["EMERGENCY: call 112 / 108 immediately", "Aspirin (chewed, if not allergic) while waiting", "Hospital treatment: clot-busters, stents or bypass"],
 "Varicose veins": ["Compression stockings", "Elevating the legs", "Sclerotherapy", "Laser / endovenous treatment"],
 "Hypothyroidism": ["Levothyroxine (daily)", "Regular TSH monitoring"],
 "Hyperthyroidism": ["Antithyroid medication", "Beta-blockers for symptoms", "Radioactive iodine", "Thyroid surgery"],
 "Hypoglycemia": ["15 g fast-acting sugar (glucose tablets, juice)", "Recheck sugar after 15 minutes", "Glucagon injection (severe)", "Adjust diabetes medication with your doctor"],
 "Osteoarthristis": ["Pain relievers (paracetamol, topical NSAIDs)", "Physiotherapy and exercise", "Hot / cold packs", "Joint injections or replacement surgery"],
 "Arthritis": ["NSAIDs", "DMARDs (for rheumatoid arthritis)", "Biologics", "Corticosteroids (short-term)"],
 "(vertigo) Paroymsal Positional Vertigo": ["Epley manoeuvre (canalith repositioning)", "Vestibular rehabilitation", "Anti-nausea medication", "Home exercises"],
 "Acne": ["Topical retinoids / benzoyl peroxide", "Topical or oral antibiotics", "Hormonal treatment", "Isotretinoin (dermatologist only)"],
 "Urinary tract infection": ["Antibiotics (as prescribed)", "Plenty of fluids", "Urinary analgesics", "Probiotics"],
 "Psoriasis": ["Topical corticosteroids / vitamin D analogues", "Phototherapy", "Systemic medication", "Biologics"],
 "Impetigo": ["Topical antibiotics (mupirocin)", "Oral antibiotics if widespread", "Gentle cleaning of sores"],
}
df = pd.DataFrame({"Disease": list(M), "Medication": [str(v) for v in M.values()]})
df.to_csv("datasets/medications.csv", index=False)

p = pd.read_csv("datasets/precautions_df.csv", index_col=0)
fix = {"Psoriasis": ["moisturise skin daily", "avoid triggers (stress, alcohol, smoking)", "salt baths", "consult doctor"],
       "Hypertension ": ["reduce salt intake", "meditation", "reduce stress", "get proper sleep"]}
for d, v in fix.items():
    p.loc[p.Disease == d, ["Precaution_1", "Precaution_2", "Precaution_3", "Precaution_4"]] = v
p.to_csv("datasets/precautions_df.csv")
print("fixed", len(df), "medication rows")
