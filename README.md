# Stock Portfolio Evaluation Tool

A local web application built with Python and Streamlit to manage and analyze a personal stock portfolio.

## 🧩 Features

* **Data Persistence:** Uses a local SQLite database (`portfolio.db`) for storing holdings.
* **Real-time Data:** Fetches live and historical stock prices using the `yfinance` library.
* **Comprehensive Analysis:** Calculates current value, P/L, total portfolio value, daily/weekly/monthly returns, volatility (Standard Deviation), and Sharpe Ratio.
* **Visualization:** Interactive charts (Pie and Line graphs) using Plotly.
* **Data Management:** Full CRUD (Create, Read, Update, Delete) functionality, plus CSV import/export.

## ⚙️ Setup Guide

1.  **Dependencies:** Ensure you have the packages listed in `requirements.txt` installed in your virtual environment.
2.  **Activation:** Ensure your virtual environment is active (`source venv/bin/activate`).
3.  **Run:** Execute the command: `streamlit run app.py`

## 💻 Usage

The application will open in your browser at [http://localhost:8501](http://localhost:8501).

Use the sidebar navigation to:
1.  **Add/Manage Holdings:** Input or edit your stock purchases.
2.  **Import/Export Data:** Load the `sample_portfolio.csv` file to quickly populate your portfolio.
3.  **Home & Detailed Analysis:** View the calculated metrics, charts, and performance summaries.