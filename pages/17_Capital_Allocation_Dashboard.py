import pandas as pd
import plotly.express as px
import streamlit as st

from services.capital_allocation_service import CapitalAllocationInput, CapitalAllocationService
from services.real_estate import AcquisitionInput
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Capital Allocation", page_icon="🧭", layout="wide")
apply_theme()

st.title("🧭 Integrated Capital Allocation Dashboard")
st.caption("株式売却・税引後手取り・配当減少・不動産取得後CFを一画面で比較します。")

service = CapitalAllocationService()

with st.sidebar:
    st.header("売却条件")
    target_net_cash = st.number_input("売却目標 税引後手取り", min_value=0, value=3_500_000, step=100_000)
    tax_rate_percent = st.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=20.315, step=0.1)
    preserve_core_policy = st.checkbox("policy=コアを除外", value=True)
    preserve_names_text = st.text_area("除外銘柄（改行区切り）", value="三菱商事\n三井住友FG\n武田薬品\nJT")
    shipping_ratio = st.slider("海運株の最大売却比率", min_value=0.0, max_value=1.0, value=0.5, step=0.1)

    st.header("取得物件条件")
    property_name = st.text_input("物件名", value="oblige新田町")
    purchase_price = st.number_input("購入価格", min_value=0, value=76_000_000, step=1_000_000)
    loan_amount = st.number_input("借入額", min_value=0, value=76_000_000, step=1_000_000)
    annual_interest_rate = st.number_input("金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    loan_years = st.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)
    acquisition_cost_rate = st.number_input("諸費用率（%）", min_value=0.0, max_value=30.0, value=7.0, step=0.5)

    st.header("賃料・経費")
    monthly_full_rent = st.number_input("満室月額賃料", min_value=0, value=665_000, step=10_000)
    vacancy_rate = st.number_input("想定空室率（%）", min_value=0.0, max_value=100.0, value=8.33, step=0.5)
    fixed_asset_tax_annual = st.number_input("固定資産税/年", min_value=0, value=618_429, step=10_000)
    management_fee_monthly = st.number_input("管理費/月", min_value=0, value=59_300, step=1_000)
    repair_reserve_monthly = st.number_input("修繕積立想定/月", min_value=0, value=30_000, step=5_000)

preserve_names = [x.strip() for x in preserve_names_text.splitlines() if x.strip()]

acquisition_input = AcquisitionInput(
    property_name=property_name,
    purchase_price=float(purchase_price),
    loan_amount=float(loan_amount),
    annual_interest_rate=float(annual_interest_rate),
    loan_years=float(loan_years),
    acquisition_cost_rate=float(acquisition_cost_rate),
    monthly_full_rent=float(monthly_full_rent),
    vacancy_rate=float(vacancy_rate),
    fixed_asset_tax_annual=float(fixed_asset_tax_annual),
    management_fee_monthly=float(management_fee_monthly),
    repair_reserve_monthly=float(repair_reserve_monthly),
)

inputs = CapitalAllocationInput(
    target_net_cash=float(target_net_cash),
    tax_rate=float(tax_rate_percent) / 100,
    preserve_names=preserve_names,
    preserve_core_policy=bool(preserve_core_policy),
    shipping_max_sell_ratio=float(shipping_ratio),
    acquisition_input=acquisition_input,
)

review = service.review(inputs)
acquisition = review["acquisition"]
comparison = review["comparison"]
recommendation = review["recommendation"]

st.subheader("Phoenix CFO Recommendation")

if recommendation["status"] == "実行候補":
    st.success(f"{recommendation['status']} | {recommendation['summary']}")
elif recommendation["status"] == "条件付き候補":
    st.info(f"{recommendation['status']} | {recommendation['summary']}")
else:
    st.warning(f"{recommendation['status']} | {recommendation['summary']}")

if review["portfolio_comment"]:
    for comment in review["portfolio_comment"]:
        st.markdown(f"- {comment}")

st.markdown("---")
st.subheader("取得物件サマリー")

c1, c2, c3, c4 = st.columns(4)
c1.metric("初期必要資金", yen(acquisition["initial_cash_required"]))
c2.metric("返済後CF/年", yen(acquisition["cash_flow_after_debt"]))
c3.metric("DSCR", "-" if acquisition["dscr"] is None else f"{acquisition['dscr']:.2f}x")
c4.metric("判定", acquisition["health"])

c5, c6, c7, c8 = st.columns(4)
c5.metric("表面利回り", "-" if acquisition["gross_yield_full"] is None else f"{acquisition['gross_yield_full']:.2%}")
c6.metric("NOI利回り", "-" if acquisition["noi_yield"] is None else f"{acquisition['noi_yield']:.2%}")
c7.metric("月額返済", yen(acquisition["monthly_payment"]))
c8.metric("損益分岐稼働率", "-" if acquisition["break_even_occupancy"] is None else f"{acquisition['break_even_occupancy']:.1%}")

st.markdown("---")
st.subheader("資本配分シナリオ比較")

if comparison.empty:
    st.warning("比較できる売却シナリオがありません。")
    st.stop()

display = comparison.copy()

for col in [
    "net_proceeds",
    "tax",
    "dividend_loss",
    "initial_cash_required",
    "funding_gap",
    "after_allocation_cash",
    "annual_property_cf",
    "annual_cf_delta",
]:
    if col in display.columns:
        display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")

if "acquisition_dscr" in display.columns:
    display["acquisition_dscr"] = display["acquisition_dscr"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")

table_cols = [
    "scenario",
    "score",
    "net_proceeds",
    "tax",
    "dividend_loss",
    "initial_cash_required",
    "funding_gap",
    "after_allocation_cash",
    "annual_property_cf",
    "annual_cf_delta",
    "acquisition_dscr",
    "acquisition_health",
    "achieves_sale_target",
    "funds_acquisition",
    "sold_names",
]

st.dataframe(display[[c for c in table_cols if c in display.columns]], width="stretch", hide_index=True)

st.markdown("---")
st.subheader("チャート")

chart_df = comparison.copy()

fig = px.bar(
    chart_df,
    x="scenario",
    y="annual_cf_delta",
    title="株式配当減少 vs 不動産CF増加後の年間CF差分",
)
st.plotly_chart(fig, width="stretch")

fig2 = px.bar(
    chart_df,
    x="scenario",
    y="funding_gap",
    title="物件取得に対する資金不足/余剰",
)
st.plotly_chart(fig2, width="stretch")

fig3 = px.scatter(
    chart_df,
    x="dividend_loss",
    y="annual_property_cf",
    size="net_proceeds",
    color="scenario",
    title="配当減少と不動産CFの比較",
)
st.plotly_chart(fig3, width="stretch")

st.markdown("---")
st.subheader("シナリオ詳細")

for _, row in comparison.iterrows():
    with st.expander(f"{row['scenario']} | score {row['score']:.1f}", expanded=False):
        st.markdown(f"**説明:** {row['description']}")
        st.markdown(f"**売却銘柄:** {row['sold_names']}")
        st.markdown(f"**税引後手取り:** {yen(row['net_proceeds'])}")
        st.markdown(f"**年間配当減少:** {yen(row['dividend_loss'])}")
        st.markdown(f"**不動産返済後CF:** {yen(row['annual_property_cf'])}")
        st.markdown(f"**年間CF差分:** {yen(row['annual_cf_delta'])}")
        st.markdown(f"**取得資金との差額:** {yen(row['after_allocation_cash'])}")

st.markdown("---")
st.info("この画面は資本配分のたたき台です。実際の売却・購入判断では、税金、融資承認、物件調査、出口価格、生活資金バッファを必ず別途確認してください。")
