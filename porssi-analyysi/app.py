from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for matplotlib
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath) # Save the uploaded file to document folder
            return redirect(url_for("report", filename=file.filename))
    return render_template("upload.html")

@app.route("/report/<filename>")
def report(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Read the CSV file and sort by date
    df = pd.read_csv(filepath)
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    # Calculate statistics
    mean_price = df["Close"].mean()
    max_price = df["Close"].max()
    min_price = df["Close"].min()

    # Create a chart and save it to static folder
    plt.figure(figsize=(10, 4))
    plt.plot(df["Date"], df["Close"])
    plt.title("Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Price (Close)")
    plt.tight_layout()
    chart_path = os.path.join("static", "chart.png")
    plt.savefig(chart_path)
    plt.close()

    return render_template("report.html", mean=mean_price, max=max_price, min=min_price)

if __name__ == "__main__":
    app.run(debug=True)