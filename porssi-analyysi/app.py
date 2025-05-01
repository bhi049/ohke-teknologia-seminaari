from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
import os

app = Flask(__name__)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def ask_gpt(mean, max_, min_, trend_desc, volatility=None, percentage_change=None, daily_change=None, volume=None, ticker=None, deep=False):
    prompt = (
        f"Analyze this stock data and provide a {'detailed' if deep else 'short and clear'} explanation for a beginner:\n"
        f"Average closing price: {mean:.2f}, max: {max_:.2f}, min: {min_:.2f}. "
        f"Trend: {trend_desc}. "
    )
    if volatility is not None:
        prompt += f"Volatility: {volatility:.4f}. "
    if percentage_change is not None:
        prompt += f"Percentage change: {percentage_change:.2f}%. "
    if daily_change is not None:
        prompt += f"Average daily change: {daily_change:.2f}. "
    if volume is not None:
        prompt += f"Average daily volume: approx. {volume:,}. "
    if ticker:
        prompt += f"Ticker: {ticker}. "

    prompt += (
        "Estimate a rough risk level (low, medium, high) and potential opportunity (low, medium, high) based on the data. "
    )
    if deep:
        prompt += "Provide a more detailed explanation including potential factors influencing the stock and things an investor should research."
    else:
        prompt += "Keep it short (max 4–6 sentences) and easy to understand."

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

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}", 400

    try:
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)

        mean_price = df["Close"].mean()
        max_price = df["Close"].max()
        min_price = df["Close"].min()
        trend_desc = "upward" if df["Close"].iloc[-1] > df["Close"].iloc[0] else "downward"
        df["MA"] = df["Close"].rolling(window=window).mean()
        df["Daily Return"] = df["Close"].pct_change()
        volatility = df["Daily Return"].std() if not df["Daily Return"].isnull().all() else None
        percentage_change = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
        daily_change = df["Close"].diff().abs().mean()

        sns.set_theme(style="whitegrid")

        plt.figure(figsize=(10, 4))
        plt.plot(df["Date"], df["Close"], label="Close Price", color="blue")
        plt.plot(df["Date"], df["MA"], label=f"{window}-Day MA", linestyle="--", color="orange")
        plt.title("Price Trend", fontsize=14)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Price (Close)", fontsize=12)
        plt.xticks(rotation=30, fontsize=10)
        plt.yticks(fontsize=10)
        plt.legend(fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        chart_path = os.path.join("static", "chart.png")
        plt.savefig(chart_path)
        plt.close()

        volume_chart_path = None
        if "Volume" in df.columns:
            plt.figure(figsize=(10, 4))
            plt.bar(df["Date"], df["Volume"], color="skyblue", label="Volume")
            plt.title("Daily Trading Volume", fontsize=14)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Volume", fontsize=12)
            plt.xticks(rotation=30, fontsize=10)
            plt.yticks(fontsize=10)
            plt.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()
            volume_chart_path = os.path.join("static", "volume_chart.png")
            plt.savefig(volume_chart_path)
            plt.close()
    except Exception as e:
        return f"Error processing data: {str(e)}", 400

    explanation = None
    if request.method == "POST":
        deep = request.form.get("explain") == "deep"
        explanation = ask_gpt(mean_price, max_price, min_price, trend_desc, volatility, percentage_change, daily_change, deep=deep)

    return render_template("report.html",
                           mean=mean_price,
                           max=max_price,
                           min=min_price,
                           window=window,
                           filename=filename,
                           explanation=explanation,
                           volatility=volatility,
                           percentage_change=percentage_change,
                           daily_change=daily_change,
                           volume_chart_path=volume_chart_path)

if __name__ == "__main__":
    app.run(debug=True)
