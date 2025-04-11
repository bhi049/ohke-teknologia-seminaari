# 📊 Stock Data Analysis Application

This project is a **Flask-based web application** designed to analyze stock market data from CSV files. Users can upload a CSV file containing stock data, and the application generates a report with key statistics and a price trend chart.

---

## 🚀 Features

- **CSV File Upload**: Users can upload CSV files containing stock data with columns such as `Date`, `Open`, `High`, `Low`, `Close`, and `Volume`.
- **Data Analysis**:
  - Calculates the average, maximum, and minimum closing prices.
  - Sorts the data by date for accurate trend analysis.
- **Visualization**:
  - Generates a line chart of the stock's closing prices over time using `matplotlib`.
- **Dynamic Reports**:
  - Displays the calculated statistics and chart on a user-friendly HTML report.

---

## 🔑 Key Files

### `app.py`
- Handles routes for uploading files and generating reports.
- Reads and processes the uploaded CSV file using `pandas`.
- Generates a line chart using `matplotlib` and saves it to the `static/` folder.

### `templates/`
- `upload.html`: Provides a form for users to upload CSV files.
- `report.html`: Displays the analysis results, including statistics and the price trend chart.

### `requirements.txt`
- Lists all the Python dependencies required to run the application, including Flask, pandas, and matplotlib.

### `.gitignore`
- Excludes unnecessary files and directories from version control, such as virtual environments, compiled Python files, and generated charts.

---
