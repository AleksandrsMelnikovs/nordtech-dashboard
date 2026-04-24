import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="NordTech Diagnostics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.kpi-card {
    background: #f8faff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.4rem 1.4rem; text-align: center;
}
.kpi-value { font-size: 2.8rem; font-weight: 700; margin: 0; line-height:1.1; }
.kpi-label { font-size: 1rem; color: #475569; margin: 0.4rem 0 0; font-weight:500; }
.kpi-red   { color: #ef4444; }
.kpi-amber { color: #f59e0b; }
.kpi-blue  { color: #2563eb; }

.section-header {
    font-size: 1.25rem; font-weight: 700; color: #1e293b;
    border-left: 5px solid #2563eb;
    padding-left: 0.85rem; margin: 1.75rem 0 0.75rem;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #1e293b !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────
@st.cache_data
def load_enriched():
    df = pd.read_csv("enriched_data.csv")
    df["Date_Clean"] = pd.to_datetime(df["Date_Clean"], errors="coerce")
    df["Had_Return"] = df["Had_Return"].astype(bool)
    df["Had_Ticket"] = df["Had_Ticket"].astype(bool)
    df["Week"]       = df["Week"].astype("Int64")
    return df

df = load_enriched()

# ── SIDEBAR ───────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/48/combo-chart.png", width=40)
st.sidebar.title("NordTech Diagnostics")
st.sidebar.markdown("---")

all_cats = sorted(df["Product_Category"].dropna().unique())
selected_cats = st.sidebar.multiselect(
    "Product Category", options=all_cats, default=all_cats
)

min_week = int(df["Week"].min())
max_week = int(df["Week"].max())
selected_weeks = st.sidebar.slider(
    "ISO Week range",
    min_value=min_week, max_value=max_week,
    value=(min_week, max_week)
)

all_signals = ["🔴 Red", "🟡 Amber", "🟢 Green"]
sel_signals  = st.sidebar.multiselect(
    "Return Signal", options=all_signals, default=all_signals
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Nov–Dec 2023")

# ── APPLY FILTERS ─────────────────────────────────────────────────
mask = (
    df["Product_Category"].isin(selected_cats) &
    df["Week"].between(selected_weeks[0], selected_weeks[1]) &
    df["Return_Signal"].isin(sel_signals)
)
dff = df[mask].copy()

# ── HEADER ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
            padding:1.6rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
    <h1 style="margin:0;font-size:1.9rem;font-weight:700;color:white;">
        🔍 NordTech — Revenue vs Churn Diagnostics
    </h1>
    <p style="margin:0.4rem 0 0;font-size:1rem;color:rgba(255,255,255,0.80);font-weight:400;">
        Operational monitoring · Nov–Dec 2023
    </p>
</div>
""", unsafe_allow_html=True)

# ── KPI ROW ───────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

total_rev   = dff["Revenue"].sum()
return_rate = dff["Had_Return"].mean() if len(dff) > 0 else 0
refund_val  = dff[dff["Had_Return"]]["Refund_Amount"].sum()
high_risk   = (dff["Had_Return"] & dff["Had_Ticket"]).sum()

with k1:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value kpi-blue">€{total_rev:,.0f}</p>
        <p class="kpi-label">Total Revenue</p>
    </div>""", unsafe_allow_html=True)

with k2:
    color = "kpi-red" if return_rate >= 0.15 else "kpi-amber" if return_rate >= 0.08 else "kpi-blue"
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value {color}">{return_rate:.1%}</p>
        <p class="kpi-label">Return Rate</p>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value kpi-amber">€{refund_val:,.0f}</p>
        <p class="kpi-label">Total Refunds</p>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value kpi-red">{int(high_risk)}</p>
        <p class="kpi-label">High-Risk Customers</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── CHART 1 — Weekly Revenue vs Returns ──────────────────────────
st.markdown('<p class="section-header">📈 Weekly Revenue vs Return Count</p>',
            unsafe_allow_html=True)

weekly = (
    dff.groupby("Week")
    .agg(Total_Revenue=("Revenue", "sum"),
         Return_Count=("Had_Return", "sum"))
    .reset_index().sort_values("Week")
)

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(
    go.Scatter(x=weekly["Week"], y=weekly["Total_Revenue"],
               name="Revenue (€)", mode="lines+markers",
               line=dict(color="#2563eb", width=2.5), marker=dict(size=7)),
    secondary_y=False)
fig1.add_trace(
    go.Bar(x=weekly["Week"], y=weekly["Return_Count"],
           name="Returns", opacity=0.5, marker_color="#ef4444"),
    secondary_y=True)
fig1.update_layout(
    height=380, plot_bgcolor="white", paper_bgcolor="white",
    legend=dict(orientation="h", y=1.12),
    xaxis_title="Week", margin=dict(t=30, b=40))
fig1.update_yaxes(title_text="Revenue (€)", secondary_y=False)
fig1.update_yaxes(title_text="Returns",     secondary_y=True)
st.plotly_chart(fig1, use_container_width=True)

# ── CHART 2 — Return Rate & Ticket Rate by Category ──────────────
st.markdown('<p class="section-header">📊 Return & Support Rate by Category</p>',
            unsafe_allow_html=True)

cat = (
    dff.groupby("Product_Category")
    .agg(Return_Rate=("Had_Return", "mean"),
         Ticket_Rate=("Had_Ticket", "mean"))
    .reset_index().sort_values("Return_Rate", ascending=False)
)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=cat["Product_Category"], y=cat["Return_Rate"],
    name="Return rate", marker_color="#ef4444",
    text=[f"{v:.1%}" for v in cat["Return_Rate"]], textposition="outside"))
fig2.add_trace(go.Bar(
    x=cat["Product_Category"], y=cat["Ticket_Rate"],
    name="Support rate", marker_color="#f59e0b",
    text=[f"{v:.1%}" for v in cat["Ticket_Rate"]], textposition="outside"))
fig2.add_hline(y=0.15, line_dash="dash", line_color="red",
               annotation_text="🔴 Escalation threshold (15%)",
               annotation_position="top right")
fig2.add_hline(y=0.08, line_dash="dot", line_color="orange",
               annotation_text="🟡 Monitor closely (8%)",
               annotation_position="bottom right")
fig2.update_layout(
    height=380, barmode="group", plot_bgcolor="white", paper_bgcolor="white",
    yaxis_tickformat=".0%", margin=dict(t=30, b=40))
st.plotly_chart(fig2, use_container_width=True)

# ── HIGH-RISK TABLE ───────────────────────────────────────────────
st.markdown('<p class="section-header">🚨 High-Risk Customers — Immediate Action Required</p>',
            unsafe_allow_html=True)
st.caption("Customers who both returned a product and raised a support complaint.")

problem_cases = (
    dff[dff["Had_Return"] & dff["Had_Ticket"]]
    [[
        "Return_Signal", "Ticket_Count", "Product_Category", "Product_Name", "Revenue"
    ]]
    .sort_values("Revenue", ascending=False)
    .reset_index(drop=True)
)
problem_cases["Revenue"] = problem_cases["Revenue"].apply(lambda x: f"€{x:,.2f}")

st.dataframe(
    problem_cases,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Return_Signal"   : st.column_config.TextColumn("Alert"),
        "Revenue"         : st.column_config.TextColumn("Revenue"),
        "Ticket_Count"    : st.column_config.NumberColumn("Support contacts"),
        "Product_Category": st.column_config.TextColumn("Category"),
        "Product_Name"    : st.column_config.TextColumn("Product"),

    }
)

st.markdown("---")
st.caption("NordTech Internal · Revenue vs Churn Diagnostics · Nov–Dec 2023")
