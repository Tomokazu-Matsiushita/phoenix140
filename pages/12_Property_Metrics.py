import pandas as pd
import plotly.express as px
import streamlit as st

from services.real_estate import PropertyMetricsService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Property Metrics", page_icon="🏠", layout="wide")
apply_theme()

st.title("🏠 Property Metrics")
st.caption("物件別の利回り・DSCR・返済後CF・空室影響を確認します。")

service = PropertyMetricsService()
metrics = service.property_metrics()

if metrics.empty:
    st.warning("物件データがありません。")
    st.stop()

total_annual_income = metrics["annual_income"].fillna(0).sum()
total_noi = metrics["noi"].fillna(0).sum()
total_debt = metrics["annual_debt_service"].fillna(0).sum()
total_cf = metrics["cash_flow_after_debt"].fillna(0).sum()
portfolio_dscr = total_noi / total_debt if total_debt else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("年間収入", yen(total_annual_income))
c2.metric("NOI", yen(total_noi))
c3.metric("年間返済", yen(total_debt))
c4.metric("Portfolio DSCR", "-" if portfolio_dscr is None else f"{portfolio_dscr:.2f}x")

c5, c6, c7 = st.columns(3)
c5.metric("返済後CF", yen(total_cf))
c6.metric("物件数", f"{len(metrics)}")
c7.metric("要改善物件", f"{(metrics['health'] == '要改善').sum()}")

st.markdown("---")
st.subheader("物件別メトリクス")

display_cols = [
    "name",
    "location",
    "purchase_price",
    "loan_balance",
    "ltv",
    "annual_income",
    "gross_yield",
    "operating_expense",
    "noi",
    "annual_debt_service",
    "cash_flow_after_debt",
    "dscr",
    "occupancy_rate",
    "break_even_occupancy",
    "health",
    "cfo_comment",
]

available_cols = [c for c in display_cols if c in metrics.columns]
display = metrics[available_cols].copy()

for col in ["purchase_price", "loan_balance", "annual_income", "operating_expense", "noi", "annual_debt_service", "cash_flow_after_debt"]:
    if col in display.columns:
        display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")

for col in ["ltv", "gross_yield", "occupancy_rate", "break_even_occupancy"]:
    if col in display.columns:
        display[col] = display[col].map(lambda x: f"{x:.1%}" if pd.notna(x) else "-")

if "dscr" in display.columns:
    display["dscr"] = display["dscr"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")

st.dataframe(display, width="stretch", hide_index=True)

st.markdown("---")
st.subheader("チャート")

chart_df = metrics.copy()

if "name" in chart_df.columns:
    fig = px.bar(chart_df, x="name", y="cash_flow_after_debt", title="物件別 返済後CF")
    st.plotly_chart(fig, width="stretch")

    fig2 = px.bar(chart_df, x="name", y="dscr", title="物件別 DSCR")
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.subheader("空室影響シミュレーター")

property_names = metrics["name"].dropna().astype(str).tolist()
selected_property = st.selectbox("物件", property_names)

selected_row = metrics[metrics["name"].astype(str).eq(selected_property)].iloc[0]
max_units = int(selected_row.get("occupied_units") or selected_row.get("units") or 0)
additional_vacancy = st.slider("追加空室数", min_value=0, max_value=max(max_units, 0), value=1 if max_units >= 1 else 0)

sim = service.vacancy_simulation(selected_property, additional_vacancy)

if sim:
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("平均月額賃料", yen(sim["avg_rent"]))
    s2.metric("調整後月額収入", yen(sim["adjusted_monthly_income"]))
    s3.metric("調整後返済後CF", yen(sim["adjusted_cash_flow_after_debt"]))
    s4.metric("調整後DSCR", "-" if sim["adjusted_dscr"] is None else f"{sim['adjusted_dscr']:.2f}x")

    if sim["adjusted_cash_flow_after_debt"] < 0:
        st.warning("この空室条件では返済後CFがマイナスになります。")
    elif sim["adjusted_dscr"] is not None and sim["adjusted_dscr"] < 1.0:
        st.warning("この空室条件ではDSCRが1.0倍を下回ります。")
    else:
        st.success("この空室条件でも返済後CFはプラスです。")
