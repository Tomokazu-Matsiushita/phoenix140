import pandas as pd
import plotly.express as px
import streamlit as st

from services.real_estate import LoanDSCRService, PropertyMetricsService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Loan DSCR Simulator", page_icon="🏦", layout="wide")
apply_theme()

st.title("🏦 Loan & DSCR Simulator")
st.caption("金利上昇・返済条件・追加空室がDSCRと返済後CFに与える影響を確認します。")

metrics_service = PropertyMetricsService()
loan_service = LoanDSCRService(metrics_service)

metrics = metrics_service.property_metrics()

if metrics.empty:
    st.warning("物件データがありません。")
    st.stop()

property_names = metrics["name"].dropna().astype(str).tolist()

with st.sidebar:
    selected_property = st.selectbox("物件", property_names)
    base = loan_service.property_base(selected_property)

    st.header("Simulation Inputs")

    loan_balance = st.number_input(
        "ローン残高",
        min_value=0,
        value=int(base.get("loan_balance") or 0),
        step=1_000_000,
    )

    rate = st.number_input(
        "金利（%）",
        min_value=0.0,
        max_value=20.0,
        value=float(base.get("interest_rate") or 0),
        step=0.1,
    )

    years = st.number_input(
        "残存年数",
        min_value=1.0,
        max_value=50.0,
        value=float(base.get("loan_years") or 30),
        step=1.0,
    )

    max_units = int(base.get("occupied_units") or base.get("units") or 0)
    additional_vacancy = st.slider(
        "追加空室数",
        min_value=0,
        max_value=max(max_units, 0),
        value=0,
    )

    use_formula = st.checkbox("ローン計算式で返済額を再計算", value=True)

sim = loan_service.simulate(
    property_name=selected_property,
    annual_rate_percent=rate,
    years=years,
    loan_balance=loan_balance,
    additional_vacancy=additional_vacancy,
    use_formula_payment=use_formula,
)

if not sim:
    st.warning("シミュレーションできませんでした。")
    st.stop()

st.subheader("シミュレーション結果")

c1, c2, c3, c4 = st.columns(4)
c1.metric("月額返済", yen(sim["monthly_payment"]))
c2.metric("年間返済", yen(sim["annual_debt_service"]))
c3.metric("調整後DSCR", "-" if sim["adjusted_dscr"] is None else f"{sim['adjusted_dscr']:.2f}x")
c4.metric("調整後返済後CF", yen(sim["adjusted_cash_flow_after_debt"]))

c5, c6, c7 = st.columns(3)
c5.metric("調整後年間収入", yen(sim["adjusted_annual_income"]))
c6.metric("調整後NOI", yen(sim["adjusted_noi"]))
c7.metric("追加空室数", f"{additional_vacancy}")

if sim["adjusted_cash_flow_after_debt"] < 0:
    st.error("返済後CFがマイナスです。空室・金利・返済条件の再確認が必要です。")
elif sim["adjusted_dscr"] is not None and sim["adjusted_dscr"] < 1.0:
    st.warning("DSCRが1.0倍未満です。返済余力に注意してください。")
elif sim["adjusted_dscr"] is not None and sim["adjusted_dscr"] < 1.25:
    st.warning("DSCRは1.0倍以上ですが、余裕は限定的です。")
else:
    st.success("DSCRと返済後CFは比較的安定しています。")

st.markdown("---")
st.subheader("金利感応度")

sensitivity = loan_service.rate_sensitivity(
    property_name=selected_property,
    additional_vacancy=additional_vacancy,
)

if not sensitivity.empty:
    display = sensitivity.copy()
    for col in ["monthly_payment", "annual_debt_service", "adjusted_annual_income", "adjusted_noi", "adjusted_cash_flow_after_debt"]:
        display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")
    display["adjusted_dscr"] = display["adjusted_dscr"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")

    st.dataframe(display, width="stretch", hide_index=True)

    fig = px.line(
        sensitivity,
        x="interest_rate",
        y="adjusted_cash_flow_after_debt",
        markers=True,
        title=f"{selected_property}: 金利別 返済後CF",
    )
    st.plotly_chart(fig, width="stretch")

    fig2 = px.line(
        sensitivity,
        x="interest_rate",
        y="adjusted_dscr",
        markers=True,
        title=f"{selected_property}: 金利別 DSCR",
    )
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.subheader("ポートフォリオ金利ストレス")

portfolio_stress = loan_service.portfolio_rate_sensitivity(additional_vacancy=additional_vacancy)

if not portfolio_stress.empty:
    display = portfolio_stress.copy()
    for col in ["portfolio_noi", "portfolio_debt_service", "portfolio_cash_flow_after_debt"]:
        display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")
    display["portfolio_dscr"] = display["portfolio_dscr"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")
    st.dataframe(display, width="stretch", hide_index=True)

    fig3 = px.line(
        portfolio_stress,
        x="rate_addition",
        y="portfolio_cash_flow_after_debt",
        markers=True,
        title="ポートフォリオ: 金利上昇幅別 返済後CF",
    )
    st.plotly_chart(fig3, width="stretch")
