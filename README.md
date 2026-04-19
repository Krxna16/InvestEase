# InvestEase

**InvestEase** is a production-ready, multi-user web application for tracking and forecasting stock portfolios. Built with a modern, interactive interface, it provides users with real-time financial data, risk-adjusted performance metrics, and automated portfolio predictions.

## 🚀 Key Highlights
- **Multi-Tenant System:** Securely isolated user sessions with portfolios filtered reliably by `user_id`.
- **Production Database:** Uses **PostgreSQL** deployed via Render with **SQLAlchemy** ORM and connection pooling for scalable, efficient queries.
- **Secure Authentication:** Implements stateless **Bcrypt** cryptographic password hashing with secure environment credential loading targeting Cloud deployments.
- **Quantitative Analytics:** Automatically computes portfolio risk measures (Sharpe Ratio, Volatility) and stock beta against live S&P500 baselines.

## 📈 Core Features
- **Secure Accounts:** Clean and robust login/registration flows.
- **Real-Time Data:** Automated market data synchronization using `yfinance`.
- **Growth Forecasting:** 30-day linear regression modeling based on historical portfolio growth rates.
- **Interactive Dashboards:** Dynamic sector distributions and financial timelines rendered dynamically via Plotly.
- **Flexible Management:** Full portfolio CRUD operations with CSV import/export capabilities.

## 🧰 Tech Stack
- **Frontend & Routing:** Streamlit
- **Backend Database:** PostgreSQL, SQLAlchemy
- **Security & Config:** Bcrypt, Python-dotenv
- **Financial APIs:** Yahoo Finance (`yfinance`)
- **Data Science:** Pandas, NumPy, Scikit-Learn, SciPy
- **Data Visualization:** Plotly

## 🏗️ Architecture Overview
The application follows a standard three-tier architecture. **Streamlit** handles all UI and stateful frontend routing. The data processing layer aggregates live financial inputs and runs predictive statistical models isolated per user. Finally, all persistent state is maintained across a pooled **PostgreSQL** connection, entirely eliminating vulnerable local file storage and ensuring reliable scalability.

## ⚙️ Setup Instructions

**1. Clone & Install Dependencies**
```bash
git clone https://github.com/Krxna16/stock-portfolio-tool.git
cd stock-portfolio-tool
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure Environment**
Create a `.env` file in the root directory and map your PostgreSQL instance:
```env
DATABASE_URL=postgresql://user:password@hostname:5432/dbname
```

**3. Launch the Application**
```bash
streamlit run app.py
```
*(The application will construct required SQL tables automatically upon initialization.)*

## 💡 Key Takeaways
InvestEase transforms traditional localized python scripting concepts into a full-scale deployed SaaS architecture. It effectively synthesizes secure production-ready database management, rigorous cryptographic logic, and live multi-featured statistical dashboards into a single optimized pipeline.