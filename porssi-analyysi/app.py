from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for matplotlib
import matplotlib.pyplot as plt
from openai import OpenAI
import os

# Initialize Flask and OpenAI client
app = Flask(__name__)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def ask_gpt(mean, max_, min_, trend_desc, ticker=None):
    prompt = (
        f"Give a short summary of a stock analysis.\n"
        f"The average closing price is {mean:.2f}, max is {max_:.2f}, and min is {min_:.2f}. "
        f"The price trend is {trend_desc}. "
    )
    if ticker:
        prompt += f"The stock ticker is {ticker}."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains stock analysis to beginners."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for("report", filename=file.filename, window=30))
    return render_template("upload.html")


@app.route("/report", methods=["GET", "POST"])
def report():
    filename = request.args.get("filename") or request.form.get("filename")
    window = request.args.get("window", type=int) or request.form.get("window", type=int)
    if not filename:
        return "Missing filename", 400
    if not window:
        window = 30

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Read the CSV file and sort by date
    df = pd.read_csv(filepath)
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    # Calculate statistics
    mean_price = df["Close"].mean()
    max_price = df["Close"].max()
    min_price = df["Close"].min()

    # Calculate trend direction
    trend_desc = "upward" if df["Close"].iloc[-1] > df["Close"].iloc[0] else "downward"

    # Calculate moving average
    df["MA"] = df["Close"].rolling(window=window).mean()

    # Create chart
    plt.figure(figsize=(10, 4))
    plt.plot(df["Date"], df["Close"], label="Close Price")
    plt.plot(df["Date"], df["MA"], label=f"{window}-Day MA", linestyle="--")
    plt.title("Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Price (Close)")
    plt.legend()
    plt.tight_layout()
    chart_path = os.path.join("static", "chart.png")
    plt.savefig(chart_path)
    plt.close()

    explanation = None
    if request.method == "POST" and request.form.get("explain") == "true":
        explanation = ask_gpt(mean_price, max_price, min_price, trend_desc)

    return render_template("report.html",
                           mean=mean_price,
                           max=max_price,
                           min=min_price,
                           window=window,
                           filename=filename,
                           explanation=explanation)


if __name__ == "__main__":
    app.run(debug=True)