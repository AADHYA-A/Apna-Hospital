import io, json, os, time
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

import engine

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
STARTED = time.time()
METRICS = json.load(open(os.path.join(os.path.dirname(__file__), "models", "metrics.json")))


@app.context_processor
def inject():
    return {"metrics": METRICS}


# ---------------- pages ----------------
@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", page="home", preset=request.args.get("symptoms", ""))


@app.route("/predict", methods=["GET", "POST"])  # backwards-compatible with the original form
def predict_legacy():
    syms = request.values.get("symptoms", "")
    return redirect(url_for("index", symptoms=syms))


@app.route("/about")
def about():
    return render_template("about.html", page="about", n_diseases=len(engine.CLASSES), n_symptoms=len(engine.SYMPTOMS))


@app.route("/contact")
def contact():
    return render_template("contact.html", page="contact")


@app.route("/developer")
def developer():
    return render_template("developer.html", page="developer")


@app.route("/blog")
def blog():
    return render_template("blog.html", page="blog")


@app.route("/diseases")
def diseases():
    items = sorted(({"name": engine.pretty_disease(c), "specialist": engine.specialist_for(c),
                     "description": engine.disease_info(c)["description"]} for c in engine.CLASSES), key=lambda d: d["name"])
    return render_template("diseases.html", page="diseases", items=items)


# ---------------- API ----------------
@app.route("/api/symptoms")
def api_symptoms():
    return jsonify([{"key": s, "label": engine.pretty_symptom(s)} for s in engine.SYMPTOMS])


@app.route("/api/parse", methods=["POST"])
def api_parse():
    text = (request.get_json(silent=True) or {}).get("text", "")[:1000]
    keys = engine.parse_text(text)
    return jsonify({"symptoms": [{"key": k, "label": engine.pretty_symptom(k)} for k in keys]})


def _clean(symptoms):
    if not isinstance(symptoms, list):
        return []
    return [s for s in symptoms if isinstance(s, str)][:40]


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    syms = _clean(data.get("symptoms"))
    try:
        return jsonify(engine.predict(syms))
    except ValueError:
        return jsonify({"error": "Please provide at least one valid symptom."}), 400


@app.route("/report.pdf", methods=["POST"])
def report():
    syms = _clean(json.loads(request.form.get("symptoms", "[]")))
    try:
        res = engine.predict(syms)
    except ValueError:
        return redirect(url_for("index"))
    from report import build_pdf
    buf = io.BytesIO(build_pdf(res))
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="apna-hospital-report.pdf")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "uptime_s": int(time.time() - STARTED), **METRICS})


@app.errorhandler(404)
def nf(_):
    return render_template("index.html", page="home", preset=""), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
