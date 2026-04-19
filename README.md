# 🚀 InvestEase
A production-ready, multi-user stock portfolio forecasting and tracking platform.

---

## 🌐 Live Demo
🔗 [Experience InvestEase Live](https://your-app-link.streamlit.app)

---

## ⚡ Key Highlights
* **Multi-User Architecture:** Fully separated and secure user environments.
* **PostgreSQL Backend:** Centralized, persistent database handling structured asset relationships.
* **ML Forecasting System:** Evaluates data natively utilizing Linear Regression and Random Forest models.
* **Authentication Security:** Secure, salted bcrypt password hashing protocols.
* **Interactive UI:** Smooth, highly intuitive interfaces engineered entirely in Streamlit.

---

## ✨ Features

### Authentication
* Secure registration and login mechanics.
* Environment isolation preventing cross-account data leaks.

### Portfolio Management
* Complete CRUD management for individual stock holdings.
* Automated CSV import/export tooling.
* Live asset valuations ingested dynamically via `yfinance`.

### Financial Analytics
* Holistic portfolio metrics tracking Cost Basis to Current Value.
* Volatility indicators and risk-adjusted Sharpe Ratios.
* Automatic sector breakdown and distribution aggregation.

### Forecasting
* Built-in 30-day algorithmic trend extrapolation.
* Auto-selection across multiple regression algorithms based on data variance.
* Visual display of prediction metrics tracking historic trends natively against projections.

### Visualization
* Dynamic Plotly growth charts mirroring the S&P 500 equivalent values.
* High-visibility tracking envelopes eliminating metric overlap constraints.

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit 
* **Backend:** PostgreSQL, SQLAlchemy
* **ML / Data Science:** Scikit-Learn, Pandas, NumPy
* **Visualization:** Plotly
* **API:** yfinance

---

## 🏗️ Architecture Overview

InvestEase relies on a clean 3-tier architecture separating the underlying database from the client presentation layer. Streamlit routes authenticated users into encrypted sessions, loading purely segmented data pulled via SQLAlchemy's ORM out of PostgreSQL. Core ML routing parses this segmented structural data natively into isolated memory stacks, completely insulating predictions between multi-tenant interactions. 

---

## 🧠 Machine Learning Approach

* **Lag-Based Features:** Strict time-series offsets preserving structural integrity and blocking future data leakage.
* **Time-Series Split:** Historical chronologies separate testing from training inherently matching real-world conditions.
* **Model Comparison:** Algorithm natively assesses `Linear Regression` and `Random Forest` models, activating the historically best route against short-term trends.
* **Rigorous Evaluation:** Precision measured reliably using standard RMSE and robust R² percentage benchmarks.
* **Volatility-Based Intervals:** Dynamic upper and lower prediction envelopes shaped proportionally over expected timeframes utilizing $\sigma \sqrt{t}$.

---

## ⚙️ Setup Instructions

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/InvestEase.git
cd InvestEase
```

**2. Install requirements:**
```bash
pip install -r requirements.txt
```

**3. Configure Environment:**
Establish a root `.env` document pointing your system securely to a running database:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/investease
```

**4. Launch Application:**
```bash
streamlit run app.py
```

---

## 🌍 Deployment

* Designed completely statelessly for rapid staging on **Streamlit Cloud**.
* Native background logic fully compatible running distributedly on platforms like **Render**.
* Requires active provisioned **PostgreSQL** attachment.

---

## 📈 Key Takeaways
* **Full-stack ML Project:** Transcends simple analytics into a scalable Python web application.
* **Production-Ready Architecture:** Clean database schema integration alongside proper user routing execution.
* **Clean UI & Real-World Utility:** Directly manages volatile live tracking, blending data science with seamless interactive workflows.

---

> **Disclaimer:** Information projected is for demonstrative programming utility. Not intended for real financial decisions.