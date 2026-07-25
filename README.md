# 🚀 SubSence AI
### AI-Powered Subscription Intelligence Platform

SubSence AI is an intelligent financial assistant that analyzes bank statements, detects subscriptions, identifies duplicate services, discovers hidden price hikes, and provides AI-powered recommendations to reduce unnecessary spending.

---

# 🌟 Features

- 📂 Upload Bank Statements (CSV, PDF, JSON)
- 🧠 AI-powered Subscription Detection
- 💰 Financial Health Analysis
- 🔍 Duplicate Subscription Detection
- 📈 Price Hike Detection
- 📊 Interactive Dashboard
- 🤖 AI Recommendations
- 📑 Comprehensive Financial Report

---

# 🏗 Project Architecture

```
                User Uploads Statement
                        │
                        ▼
              Input Intelligence Module
                        │
                        ▼
          Structured Transaction Extraction
                        │
                        ▼
            Financial Intelligence Module
                        │
                        ▼
        Subscription & Spending Analysis
                        │
                        ▼
               AI Intelligence Module
                        │
                        ▼
        Personalized Financial Insights
                        │
                        ▼
            Dashboard & Final Report
```

---

# 📁 Project Structure

```
SubSence-AI
│
├── backend/
│   ├── app.py
│   ├── input_intelligence/
│   ├── FINANCIAL/
│   ├── ai/
│   ├── routes/
│   └── uploads/
│
├── frontend/
│   ├── index.html
│   ├── upload.html
│   ├── dashboard.html
│   ├── loading.html
│   ├── css/
│   └── js/
│
├── sample_json/
│
├── README.md
│
└── requirements.txt
```

---

# ⚙ Workflow

## Step 1 — Upload

The user uploads a financial statement.

Supported formats:

- CSV
- PDF
- JSON

The uploaded file is sent to:

```
POST /api/upload
```

---

## Step 2 — Input Intelligence

The Input Intelligence module performs:

- Statement Parsing
- Data Cleaning
- Merchant Extraction
- Date Extraction
- Amount Detection
- Transaction Classification

Output:

```
Structured Transactions
```

Example

```json
{
  "merchant":"Netflix",
  "amount":649,
  "date":"2025-01-05"
}
```

---

## Step 3 — Financial Intelligence

The Financial Intelligence engine analyzes transactions.

It detects:

- Active subscriptions
- Duplicate subscriptions
- Monthly spending
- Annual spending
- Subscription frequency
- Price hikes
- Spending trends
- Financial health score

Output

```
financial_analysis.json
```

---

## Step 4 — AI Intelligence

The AI module studies the financial analysis and generates recommendations.

Examples:

- Cancel duplicate subscriptions
- Switch to cheaper plans
- Reduce unnecessary spending
- Optimize recurring payments

Output

```
AI Recommendations
```

---

## Step 5 — Dashboard

The frontend requests:

```
GET /api/dashboard
```

The dashboard displays:

- Financial Health Score
- Active Subscriptions
- Duplicate Services
- Price Hikes
- Monthly Spending
- AI Recommendations

---

# 🔄 API Flow

```
Frontend
      │
      ▼
POST /api/upload
      │
      ▼
Input Intelligence
      │
      ▼
Financial Intelligence
      │
      ▼
AI Intelligence
      │
      ▼
Dashboard JSON
      │
      ▼
Frontend Dashboard
```

---

# 📡 API Endpoints

## Health

```
GET /api/health
```

Checks server status.

---

## Upload

```
POST /api/upload
```

Uploads financial statement.

---

## Analysis

```
GET /api/analysis/<analysis_id>
```

Returns complete financial analysis.

---

## Dashboard

```
GET /api/dashboard
```

Returns dashboard data.

---

## AI

```
GET /api/ai
```

Returns AI-generated recommendations.

---

## Report

```
GET /api/report
```

Returns the complete report.

---

# 🛠 Technologies Used

## Frontend

- HTML5
- CSS3
- JavaScript

## Backend

- Flask
- Python

## AI

- Gemini API (optional)
- Rule-based fallback

## Data Processing

- Pandas
- JSON
- CSV Parser
- PDF Parser

---

# 💡 Financial Intelligence

SubSence AI detects:

✅ Recurring subscriptions

✅ Duplicate streaming services

✅ Hidden renewals

✅ Silent price increases

✅ Monthly subscription costs

✅ Annual subscription costs

✅ Subscription health score

---

# 🤖 AI Intelligence

The AI engine provides:

- Smart saving recommendations
- Subscription optimization
- Duplicate service alerts
- Financial health insights
- Personalized advice

---

# 🎯 User Journey

```
Upload Statement
       │
       ▼
Transactions Extracted
       │
       ▼
Subscriptions Detected
       │
       ▼
Financial Analysis
       │
       ▼
AI Recommendation
       │
       ▼
Interactive Dashboard
```

---

# 🚀 How to Run

## Clone

```bash
git clone <repository-url>
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Start Backend

```bash
python backend/app.py
```

---

## Open Browser

```
http://127.0.0.1:5000
```

---

# ✅ Supported Inputs

| Format | Supported |
|---------|-----------|
| CSV | ✅ |
| PDF | ✅ |
| JSON | ✅ |

---

# 📊 Output

SubSence AI generates:

- Financial Health Score
- Active Subscriptions
- Duplicate Subscriptions
- Price Hikes
- Monthly Spending
- AI Recommendations
- Complete Financial Report

---

# Future Enhancements

- Bank API Integration
- UPI Transaction Analysis
- Email Receipt Parsing
- Real-time Subscription Tracking
- Mobile Application
- Personalized Budget Planner
- Predictive Spending Analytics

---

# Contributors

Built with ❤️ by the SubSence AI Team.
