from flask import Flask, render_template, request
from src.inference.predict import PhishingPredictor

app = Flask(__name__)
predictor = PhishingPredictor()

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        url = request.form.get("url")

        if url:
            result = predictor.predict(url)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)