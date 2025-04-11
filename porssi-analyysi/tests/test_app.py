import sys
import os
import io
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import shutil
import pytest
import pandas as pd
from app import app

# Fixture to set up a test client for the Flask app
# This allows to simulate requests to the app without running a server
@pytest.fixture
def client():
    test_upload_dir = "test_uploads"
    os.makedirs(test_upload_dir, exist_ok=True)
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "test_uploads"
    with app.test_client() as client:
        yield client
        
    # Cleanup after tests
    shutil.rmtree(test_upload_dir)

# Test 1: Does the index ("/") page load correctly?
# Checks that the page returns status 200 and contains the expected text
def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Upload CSV File" in response.data

# Test 2: Can we upload a CSV file and get redirected to /report?
# Simulates file upload using in-memory CSV content
def test_csv_upload_and_rederict(client):
    csv_content = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-01,100,110,95,105,1000000\n"
        "2024-01-02,106,112,102,110,1500000\n"
    )
    data = {
        "file": (io.BytesIO(csv_content.encode()), "test.csv")
    }
    response = client.post("/", data=data, content_type="multipart/form-data")

    # If upload is successful, the app should redirect (HTTP 302)
    assert response.status_code == 302 # Redirect to /report
    assert "/report" in response.location

# Test 3: Verify that the app correctly calculates basic statistics from CSV data
# Tests mean, max, min, and moving average using pandas directly (no Flask interaction)
def test_report_calculation():
    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Open": [100, 102, 104],
        "High": [105, 107, 109],
        "Low": [98, 100, 102],
        "Close": [101, 103, 105],
        "Volume": [1000000, 1500000, 1200000]
    })

    # Parse date column and sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    # Check average, max, and min closing prices
    assert round(df["Close"].mean(), 2) == 103.0
    assert df["Close"].max() == 105
    assert df["Close"].min() == 101

    # Test a 2-day moving average (rolling window)
    df["MA2"] = df["Close"].rolling(window=2).mean()

    # The 2-day MA for the 3rd row (index 2) should be (103+105)/2 = 104
    assert round(df["MA2"].iloc[2], 2) == 104.0