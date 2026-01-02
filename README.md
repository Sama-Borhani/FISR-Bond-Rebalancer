This project has evolved into a sophisticated, autonomous multi-asset trading desk. Here is a professional **README.md** that highlights your quantitative skills, the "Market Study" logic, and the institutional risk controls you've built.

---

# 🏛️ FISR: Quantitative Bond Rebalancing Desk

**Fixed Income Systematic Rebalancer (FISR)** is an autonomous, data-driven portfolio management system designed to manage a $100,000 model portfolio across a dynamic universe of bond ETFs. The system utilizes a "Study and Retain" discovery engine to optimize duration-matching while enforcing institutional-grade risk guardrails.

## 🚀 Key Features

* **Dynamic Market Discovery**: Unlike static rebalancers, the system "studies" a 12-bond universe (Treasuries, Corporates, Inflation-Protected, and International) via `yfinance`. It only "retains" and trades assets that meet strict liquidity requirements (Volume > 100k).
* **Target Duration Optimization**: Implements a **Linear Interpolation** heuristic to match a user-defined target duration (e.g., 8.0 years) by bracketing the portfolio across the most efficient points on the yield curve.
* **Institutional Risk Gatekeeper**: A pre-trade verification engine that enforces:
* **Daily Turnover Cap**: Limits total daily volume to 20% of equity to prevent over-trading.
* **Fat-Finger Protection**: Rejects any single order exceeding 5% of total portfolio value.
* **Hard Kill Switch**: Instant suspension of all trading activity via the control dashboard.


* **Real-Time Analytics Dashboard**: Built with Streamlit to provide live mark-to-market valuation, allocation pie charts, and a full audit trail of system logs and trade history.

---

## 🛠️ System Architecture

| Component | Responsibility |
| --- | --- |
| **`strategy.py`** | Market discovery, liquidity analysis, and weight optimization. |
| **`risk.py`** | Pre-trade risk compliance and institutional gatekeeping. |
| **`db.py`** | Persistent storage using SQLite with JSON-serialized signal logging. |
| **`dashboard.py`** | Streamlit UI for live portfolio monitoring and strategy control. |
| **`broker.py`** | Mock execution engine with detailed transaction logging. |

---

## 📊 Portfolio Universe

The engine monitors a diverse set of instruments to ensure coverage across the entire curve:

* **Treasuries**: SHY (Short), IEF (Intermediate), TLT (Long).
* **Corporate**: LQD (Investment Grade), VCIT (Intermediate), VCSH (Short).
* **Inflation/Intl**: TIP (TIPS), BNDX (International), VWOB (Emerging Markets).

---

## 🚦 Getting Started

### 1. Prerequisites

* Python 3.10+
* `yfinance`, `pandas`, `streamlit`, `plotly`

### 2. Installation

```bash
git clone https://github.com/your-username/FISR-Bond-Rebalancer.git
cd FISR-Bond-Rebalancer
pip install -r requirements.txt

```

### 3. Execution

To run the autonomous strategy:

```bash
python src/strategy.py

```

To launch the dashboard:

```bash
streamlit run src/dashboard.py

```

---

## 📈 Performance & Audit

The system is designed for **24/7 autonomous operation** via GitHub Actions. Every hour, the bot:

1. Downloads live market data.
2. Calculates duration drift from the target.
3. Verifies risk compliance.
4. Logs trades and system events for institutional audit.

---

**Would you like me to help you add a "Skills & Technologies" section that specifically maps these features to the requirements often seen in job postings for Canadian banks?**
