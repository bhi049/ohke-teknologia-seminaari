from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for matplotlib
import matplotlib.pyplot as plt
import seaborn as sns  # Add seaborn for chart styling
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

    try:
        # Read the CSV file and sort by date
        df = pd.read_csv(filepath)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}", 400

    try:
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

        # Calculate additional metrics
        df["Daily Return"] = df["Close"].pct_change()
        volatility = df["Daily Return"].std() if not df["Daily Return"].isnull().all() else None
        percentage_change = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
        daily_change = df["Close"].diff().abs().mean()

        # Apply seaborn style for cleaner charts
        sns.set_theme(style="whitegrid")

        # Create price trend chart
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

        # Create volume chart if Volume column exists
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
    if request.method == "POST" and request.form.get("explain") == "true":
        explanation = ask_gpt(mean_price, max_price, min_price, trend_desc)

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