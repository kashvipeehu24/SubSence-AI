# SubSense AI - JSON Contract

Version: 1.0

Status: FINAL (Do Not Change Without Team Approval)

---

# Purpose

This document defines the JSON communication contract between all project modules.

Every developer MUST follow this contract exactly.

No field names should be changed.

No field types should be changed.

Only new optional fields may be added after team discussion.

---

# Data Flow

User

↓

Input Intelligence Module

↓

transactions.json

↓

Financial Intelligence Module

↓

financial_analysis.json

↓

AI Intelligence Module

↓

ai_response.json

↓

Frontend Dashboard

↓

dashboard.json

---

# Module Ownership

## Member 1

Input Intelligence

Produces

transactions.json

---

## Member 2

Financial Intelligence

Consumes

transactions.json

Produces

financial_analysis.json

---

## Member 3

AI Intelligence

Consumes

financial_analysis.json

Produces

ai_response.json

---

## Member 4

Frontend

Consumes

dashboard.json

Displays dashboard only.

---

# Naming Convention

Use

snake_case

Example

financial_health_score

NOT

FinancialHealthScore

NOT

financialHealthScore

---

# Date Format

YYYY-MM-DD

Example

2026-07-25

---

# Currency

INR

Example

649

NOT

₹649

Currency symbol should never be stored inside JSON.

---

# Boolean Format

Only

true

or

false

---

# Null Values

Use

null

if value is unavailable.

Never use

""

for missing values.

---

# Transaction Categories

Allowed values

Entertainment

Music

Video Streaming

Shopping

Utilities

Education

Food

Travel

Gaming

Cloud Services

Insurance

Investment

Healthcare

Productivity

Other

---

# Source Types

Allowed values

Bank Statement

SMS

Email

Manual

---

# Risk Levels

Allowed values

Low

Medium

High

Critical

---

# Confidence Score

Range

0.0

to

1.0

Example

0.96

---

# API Rule

Every backend response must return JSON only.

No HTML.

No plain text.

---

# File Communication

Member 1

↓

transactions.json

↓

Member 2

↓

financial_analysis.json

↓

Member 3

↓

ai_response.json

↓

Frontend

↓

dashboard.json

---

# Rules

✓ Never rename JSON fields.

✓ Never remove required fields.

✓ Keep data types fixed.

✓ Keep arrays even if empty.

✓ Empty array []

Never null.

---

END OF CONTRACT