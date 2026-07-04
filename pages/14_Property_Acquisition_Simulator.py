import pandas as pd
import plotly.express as px
import streamlit as st

from services.real_estate import AcquisitionInput, PropertyAcquisitionService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Property Acquisition Simulator", page_icon="🏘️", layout="wide")
apply_theme()

st.title("🏘️ Property Acquisition Simulator")
st.caption("新規物件購入前に、利回り・NOI・DSCR・返済後CF・自己資金回収年数を確認します。")

service = PropertyAcquisitionService()

with st.sidebar:
    st.header("物件条件")

    property_name = st.text_input("物件名", value="oblige新田町")

    purchase_price = st.number_input("購入価格", min_value=0, value=76_000_000, step=1_000_000)
    loan_amount = st.number_input("借入額", min_value=0, value=76_000_000, step=1_000_000)
    annual_interest_rate = st.number_input("金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    loan_years = st.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)

    st.header("初期費用")
    acquisition_cost_rate = st.number_input("諸費用率（%）", min_value=0.0, max_value=30.0, value=7.0, step=0.5)
    renovation_cost = st.number_input("初期修繕・リフォーム", min_value=0, value=0, step=100_000)
    initial_cash_buffer = st.number_input("初期予備資金", min_value=0, value=0, step=100_000)

    st.header("収入")
    units = st.number_input("戸数", min_value=1, value=12, step=1)
    monthly_full_rent = st.number_input("満室月額賃料", min_value=0, value=665_000, step=10_000)
    vacancy_rate = st.number_input("想定空室率（%）", min_value=0.0, max_value=100.0, value=8.33, step=0.5)

    st.header("経費")
    fixed_asset_tax_annual = st.number_input("固定資産税・都市計画税/年", min_value=0, value=618_429, step=10_000)
    management_fee_monthly = st.number_input("管理費/月", min_value=0, value=59_300, step=1_000)
    cleaning_fee_monthly = st.number_input("清掃費/月", min_value=0, value=0, step=1_000)
    insurance_annual = st.number_input("保険料/年", min_value=0, value=0, step=10_000)
    repair_reserve_monthly = st.number_input("修繕積立想定/月", min_value=0, value=30_000, step=5_000)
    other_expense_annual = st.number_input("その他経費/年", min_value=0, value=0, step=10_000)

inputs = AcquisitionInput(
    property_name=property_name,
    purchase_price=float(purchase_price),
    loan_amount=float(loan_amount),
    annual_interest_rate=float(annual_interest_rate),
    loan_years=float(loan_years),
    acquisition_cost_rate=float(acquisition_cost_rate),
    renovation_cost=float(renovation_cost),
    initial_cash_buffer=float(initial_cash_buffer),
    units=int(units),
    monthly_full_rent=float(monthly_full_rent),
    vacancy_rate=float(vacancy_rate),
    fixed_asset_tax_annual=float(fixed_asset_tax_annual),
    management_fee_monthly=float(management_fee_monthly),
    cleaning_fee_monthly=float(cleaning_fee_monthly),
    insurance_annual=float(insurance_annual),
    repair_reserve_monthly=float(repair_reserve_monthly),
    other_expense_annual=float(other_expense_annual),
)

result = service.evaluate(inputs)

st.subheader("購入判断サマリー")

c1, c2, c3, c4 = st.columns(4)
c1.metric("判定", result["health"])
c2.metric("DSCR", "-" if result["dscr"] is None else f"{result['dscr']:.2f}x")
c3.metric("返済後CF/年", yen(result["cash_flow_after_debt"]))
c4.metric("初期必要資金", yen(result["initial_cash_required"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("表面利回り", "-" if result["gross_yield_full"] is None else f"{result['gross_yield_full']:.2%}")
c6.metric("実効表面利回り", "-" if result["gross_yield_effective"] is None else f"{result['gross_yield_effective']:.2%}")
c7.metric("NOI利回り", "-" if result["noi_yield"] is None else f"{result['noi_yield']:.2%}")
c8.metric("自己資金利回り", "-" if result["cash_on_cash"] is None else f"{result['cash_on_cash']:.2%}")

c9, c10, c11, c12 = st.columns(4)
c9.metric("月額返済", yen(result["monthly_payment"]))
c10.metric("NOI", yen(result["noi"]))
c11.metric("損益分岐稼働率", "-" if result["break_even_occupancy"] is None else f"{result['break_even_occupancy']:.1%}")
c12.metric("自己資金回収年数", "-" if result["payback_years"] is None else f"{result['payback_years']:.1f}年")

if result["health"] == "有力候補":
    st.success(result["cfo_comment"])
elif result["health"] == "条件付き候補":
    st.info(result["cfo_comment"])
elif result["health"] == "慎重検討":
    st.warning(result["cfo_comment"])
else:
    st.error(result["cfo_comment"])

st.markdown("---")
st.subheader("詳細計算")

detail_rows = [
    ("購入価格", result["purchase_price"]),
    ("借入額", result["loan_amount"]),
    ("自己資金", result["own_capital"]),
    ("諸費用", result["acquisition_cost"]),
    ("初期修繕・予備資金込み必要資金", result["initial_cash_required"]),
    ("満室年間賃料", result["full_annual_rent"]),
    ("空室控除後年間賃料", result["effective_annual_rent"]),
    ("運営経費", result["operating_expense"]),
    ("NOI", result["noi"]),
    ("年間返済額", result["annual_debt_service"]),
    ("返済後CF", result["cash_flow_after_debt"]),
]

detail_df = pd.DataFrame(detail_rows, columns=["項目", "金額"])
detail_df["金額"] = detail_df["金額"].map(yen)
st.dataframe(detail_df, width="stretch", hide_index=True)

st.markdown("---")
st.subheader("金利・空室ストレステスト")

stress = service.sensitivity_table(inputs)

if not stress.empty:
    cash_pivot = stress.pivot(index="vacancy_rate", columns="interest_rate", values="cash_flow_after_debt")
    dscr_pivot = stress.pivot(index="vacancy_rate", columns="interest_rate", values="dscr")

    st.caption("返済後CFマトリクス")
    cash_display = cash_pivot.copy()
    for col in cash_display.columns:
        cash_display[col] = cash_display[col].map(lambda x: yen(x) if pd.notna(x) else "-")
    st.dataframe(cash_display, width="stretch")

    st.caption("DSCRマトリクス")
    dscr_display = dscr_pivot.copy()
    for col in dscr_display.columns:
        dscr_display[col] = dscr_display[col].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")
    st.dataframe(dscr_display, width="stretch")

    fig = px.line(
        stress,
        x="interest_rate",
        y="cash_flow_after_debt",
        color="vacancy_rate",
        markers=True,
        title="金利・空室率別 返済後CF",
    )
    st.plotly_chart(fig, width="stretch")

    fig2 = px.line(
        stress,
        x="interest_rate",
        y="dscr",
        color="vacancy_rate",
        markers=True,
        title="金利・空室率別 DSCR",
    )
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.info("このシミュレーターは投資判断のたたき台です。実際の購入前には、レントロール、修繕履歴、税金、保険、融資条件、出口価格を別途確認してください。")
