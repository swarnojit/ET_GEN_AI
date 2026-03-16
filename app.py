import os
import json
import re

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# ── Load env ─────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

vision_model = genai.GenerativeModel("gemini-2.5-flash")
analysis_model = genai.GenerativeModel("gemini-2.5-flash")

# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Tax Wizard — ET AI Hackathon",
    page_icon="💰",
    layout="wide"
)

# ── CSS ──────────────────────────────────────────────
st.markdown("""
<style>
.stApp {background:#0a0a0f;}
.hero{
background:linear-gradient(135deg,#16161f,#1a1a2e);
padding:2rem;
border-radius:18px;
border:1px solid #2a2a3a;
margin-bottom:2rem;
}
.hero h1{color:#f7c948;}
.summary-box{
background:#16161f;
border-left:4px solid #ff6b35;
padding:1rem;
border-radius:0 10px 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────
st.markdown("""
<div class="hero">
<h1>💰 Tax Wizard</h1>
<p>AI-powered Indian Tax Analyzer (FY 2025-26)</p>
</div>
""", unsafe_allow_html=True)

# ── Tax Engine (FY 2025–26) ──────────────────────────
def old_regime_tax(income):
    if income <= 250000:
        tax = 0
    elif income <= 500000:
        tax = (income-250000)*0.05
    elif income <= 1000000:
        tax = 12500 + (income-500000)*0.20
    else:
        tax = 112500 + (income-1000000)*0.30

    if income <= 500000:
        tax = 0

    return tax


def new_regime_tax(income):
    if income <= 400000:
        tax = 0
    elif income <= 800000:
        tax = (income-400000)*0.05
    elif income <= 1200000:
        tax = 20000 + (income-800000)*0.10
    elif income <= 1600000:
        tax = 60000 + (income-1200000)*0.15
    elif income <= 2000000:
        tax = 120000 + (income-1600000)*0.20
    elif income <= 2400000:
        tax = 200000 + (income-2000000)*0.25
    else:
        tax = 300000 + (income-2400000)*0.30

    # rebate
    if income <= 1200000:
        tax = 0

    return tax

# ── Currency Format ──────────────────────────────────
def fmt(x):
    return f"₹{x:,.0f}"

# ── PDF Parsing with Gemini Vision ───────────────────
def parse_form16(uploaded_pdf):

    pdf_bytes = uploaded_pdf.read()

    prompt = """
Extract ALL financial data from this tax document.

Return JSON.

{
"gross_salary": number,
"basic_salary": number,
"hra_received": number,
"rent_paid": number,

"interest_income": number,
"dividend_income": number,
"stock_stcg": number,
"stock_ltcg": number,
"other_income": number,

"sec80c": number,
"sec80d": number,
"nps": number,
"home_loan_interest": number,
"education_loan_interest": number,
"donations_80g": number,

"professional_tax": number,
"tds": number
}

Return 0 if field not found.
"""

    response = vision_model.generate_content([
        {"mime_type": "application/pdf", "data": pdf_bytes},
        prompt
    ])

    txt = response.text
    txt = re.sub(r"```json|```", "", txt)

    match = re.search(r"\{.*\}", txt, re.DOTALL)

    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except:
        return {}

# ── Investment Advice ─────────────────────────────────
def investment_advice(risk):

    if risk == "Low":
        return [
            "PPF (Safe long-term investment)",
            "EPF voluntary contribution",
            "Tax saving fixed deposits",
            "Debt mutual funds"
        ]

    if risk == "Medium":
        return [
            "ELSS mutual funds",
            "Balanced advantage funds",
            "NPS retirement planning"
        ]

    return [
        "Small cap ELSS funds",
        "Index funds",
        "Aggressive equity mutual funds"
    ]

# ── Sidebar Inputs ───────────────────────────────────
with st.sidebar:

    st.header("💼 Salary Income")

    gross_salary = st.number_input("Gross Salary", value=0)
    basic_salary = st.number_input("Basic Salary", value=0)

    hra_received = st.number_input("HRA Received", value=0)
    rent_paid = st.number_input("Rent Paid", value=0)

    city_type = st.selectbox("City Type", ["metro","non-metro"])

    st.divider()

    st.header("📈 Other Income")

    interest_income = st.number_input("Interest Income", value=0)
    dividend_income = st.number_input("Dividend Income", value=0)

    stock_stcg = st.number_input("Stock STCG", value=0)
    stock_ltcg = st.number_input("Stock LTCG", value=0)

    other_income = st.number_input("Other Income", value=0)

    st.divider()

    st.header("📉 Tax Deductions")

    sec80c = st.number_input("80C Investments", value=0)
    sec80d = st.number_input("Health Insurance 80D", value=0)
    nps = st.number_input("NPS 80CCD(1B)", value=0)

    home_loan_interest = st.number_input("Home Loan Interest (Sec 24)", value=0)
    education_loan_interest = st.number_input("Education Loan Interest (80E)", value=0)

    donations_80g = st.number_input("Donations (80G)", value=0)

    professional_tax = st.number_input("Professional Tax", value=0)

    st.divider()

    st.header("🧾 Taxes Paid")

    tds = st.number_input("TDS Deducted", value=0)

    st.divider()

    risk = st.selectbox("Investment Risk Appetite", ["Low","Medium","High"])

    uploaded_pdf = st.file_uploader("Upload Form-16 / Financial Document", type=["pdf"])

    analyze_btn = st.button("Analyze Taxes")

# ── Auto Parse PDF ───────────────────────────────────
if uploaded_pdf:

    with st.spinner("Reading document using Gemini Vision..."):
        data = parse_form16(uploaded_pdf)

    if data:

        st.success("Document parsed successfully")

        gross_salary = data.get("gross_salary",0)
        basic_salary = data.get("basic_salary",0)
        hra_received = data.get("hra_received",0)
        rent_paid = data.get("rent_paid",0)

        interest_income = data.get("interest_income",0)
        dividend_income = data.get("dividend_income",0)

        stock_stcg = data.get("stock_stcg",0)
        stock_ltcg = data.get("stock_ltcg",0)
        other_income = data.get("other_income",0)

        sec80c = data.get("sec80c",0)
        sec80d = data.get("sec80d",0)
        nps = data.get("nps",0)

        home_loan_interest = data.get("home_loan_interest",0)
        education_loan_interest = data.get("education_loan_interest",0)

        donations_80g = data.get("donations_80g",0)

        professional_tax = data.get("professional_tax",0)

        tds = data.get("tds",0)

        analyze_btn = True

# ── Analysis ─────────────────────────────────────────
if analyze_btn:

    # total income
    total_income = (
        gross_salary
        + interest_income
        + dividend_income
        + stock_stcg
        + stock_ltcg
        + other_income
    )

    st.header("📊 Financial Overview")

    col1,col2,col3 = st.columns(3)

    col1.metric("Salary Income", fmt(gross_salary))
    col2.metric("Other Income", fmt(
        interest_income + dividend_income + stock_stcg + stock_ltcg + other_income
    ))
    col3.metric("Total Income", fmt(total_income))

    st.divider()

    st.header("💼 Salary Structure")

    col1,col2,col3 = st.columns(3)

    col1.metric("Basic Salary", fmt(basic_salary))
    col2.metric("HRA Received", fmt(hra_received))
    col3.metric("Rent Paid", fmt(rent_paid))

    st.divider()

    st.header("📉 Deduction Breakdown")

    col1,col2,col3 = st.columns(3)

    col1.metric("80C", fmt(sec80c))
    col2.metric("80D", fmt(sec80d))
    col3.metric("NPS", fmt(nps))

    st.write("Home Loan Interest:", fmt(home_loan_interest))
    st.write("Education Loan Interest:", fmt(education_loan_interest))
    st.write("Donations:", fmt(donations_80g))
    st.write("Professional Tax:", fmt(professional_tax))

    st.divider()

    # deductions
    deductions_old = (
        50000 +
        min(sec80c,150000) +
        sec80d +
        min(nps,50000) +
        home_loan_interest +
        education_loan_interest +
        donations_80g +
        professional_tax
    )

    taxable_old = max(0, total_income - deductions_old)
    taxable_new = max(0, total_income - 75000)

    old_tax = old_regime_tax(taxable_old)
    new_tax = new_regime_tax(taxable_new)

    better = "Old Regime" if old_tax < new_tax else "New Regime"
    savings = abs(old_tax-new_tax)

    st.header("📊 Tax Comparison")

    col1,col2 = st.columns(2)

    col1.metric("Old Regime Tax", fmt(old_tax))
    col2.metric("New Regime Tax", fmt(new_tax))

    st.success(f"Better Option: {better}")
    st.write("Estimated Savings:", fmt(savings))

    st.divider()

    st.header("🔍 Missed Tax Saving Opportunities")

    if sec80c < 150000:
        st.write(f"• Invest {fmt(150000-sec80c)} more in Section 80C")

    if nps < 50000:
        st.write(f"• Invest {fmt(50000-nps)} more in NPS")

    if sec80d == 0:
        st.write("• Health insurance deduction available under 80D")

    if home_loan_interest == 0:
        st.write("• Home loan interest deduction available")

    if education_loan_interest == 0:
        st.write("• Education loan interest deduction available")

    st.divider()

    st.header("💡 Investment Advice")

    advice = investment_advice(risk)

    for a in advice:
        st.write("•", a)

    st.divider()

    prompt = f"""
Explain tax comparison in simple English.

Income: {total_income}
Old tax: {old_tax}
New tax: {new_tax}
Savings: {savings}
Risk profile: {risk}
"""

    response = analysis_model.generate_content(prompt)

    st.header("🤖 AI Tax Advisor")

    st.markdown(
        f'<div class="summary-box">{response.text}</div>',
        unsafe_allow_html=True
    )

else:

    st.markdown("""
<div style="text-align:center;padding:3rem;color:#6b6b8a">
<h2>Upload financial document or enter details manually</h2>
</div>
""", unsafe_allow_html=True)