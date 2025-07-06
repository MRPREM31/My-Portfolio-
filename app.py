from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/journey")
def journey():
    return render_template("journey.html")

@app.route("/work_experience")
def work_experience():
    return render_template("work-experience.html")

if __name__ == "__main__":
    app.run(debug=True)
