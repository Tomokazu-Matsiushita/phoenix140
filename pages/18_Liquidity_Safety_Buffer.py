import pandas as pd
import plotly.express as px
import streamlit as st

from services.capital_allocation_service import CapitalAllocationInput
from services.liquidity_safety_service import LiquiditySafetyInput, LiquiditySafetyService
from services.real_estate import AcquisitionInput
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Liquidity Safety Buffer", page_icon="🛟", layout="wide")
apply_theme()

st.title("🛟 Liquidity & Safety Buffer Check")
st.caption("株式売却・不動産取得後に、手元現金と生活防衛資金が十分残るかを確認します。")

service = LiquiditySafetyService()

with st.sidebar:
    st.header("手元資金・安全資金")
    current_cash = st.number_input("現在の現金・銀行残高", min_value=0, value=4_856_312, step=100_000)
    monthly_living_expense = st.number_input("月間生活費", min_value=0, value=700_000, step=50_000)
    emergency_months = st.number_input("生活防衛資金 月数", min_value=0.0, max_value=36.0, value=6.0, step=1.0)
    property_repair_reserve = st.number_input("不動産修繕予備資金", min_value=0, value=1_500_000, step=100_000)
    tax_reserve = st.number_input("税金予備資金", min_value=0, value=500_000, step=100_000)
    other_commitments = st.number_input("その他予定支出", min_value=0, value=0, step=100_000)
    minimum_cash_floor = st.number_input("最低現金ライン", min_value=0, value=2_000_000, step=100_000)

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

capital_input = CapitalAllocationInput(
    target_net_cash=float(target_net_cash),
    tax_rate=float(tax_rate_percent) / 100,
    preserve_names=preserve_names,
    preserve_core_policy=bool(preserve_core_policy),
    shipping_max_sell_ratio=float(shipping_ratio),
    acquisition_input=acquisition_input,
)

liquidity_input = LiquiditySafetyInput(
    current_cash=float(current_cash),
    monthly_living_expense=float(monthly_living_expense),
    emergency_months=float(emergency_months),
    property_repair_reserve=float(property_repair_reserve),
    tax_reserve=float(tax_reserve),
    other_commitments=float(other_commitments),
    minimum_cash_floor=float(minimum_cash_floor),
    capital_allocation_input=capital_input,
)

review = service.review(liquidity_input)
scenario_review = review["scenario_review"]
recommendation = review["recommendation"]

st.subheader("Phoenix CFO Safety Recommendation")

if recommendation["status"] == "実行候補":
    st.success(f"{recommendation['status']} | {recommendation['summary']}")
elif recommendation["status"] == "条件付き候補":
    st.info(f"{recommendation['status']} | {recommendation['summary']}")
else:
    st.warning(f"{recommendation['status']} | {recommendation['summary']}")

if review["actions"]:
    st.markdown("#### Priority Actions")
    for action in review["actions"]:
        st.markdown(f"- {action}")

st.markdown("---")
st.subheader("安全資金サマリー")

required_buffer = review["required_buffer"]
current_months = review["current_months_covered"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("現在現金", yen(current_cash))
c2.metric("必要安全資金", yen(required_buffer))
c3.metric("現在の生活費月数", "-" if current_months is None else f"{current_months:.1f}か月")
c4.metric("最低現金ライン", yen(minimum_cash_floor))

st.markdown("---")
st.subheader("シナリオ別 流動性チェック")

if scenario_review.empty:
    st.warning("シナリオがありません。")
    st.stop()

display = scenario_review.copy()

money_cols = [
    "current_cash",
    "net_proceeds",
    "initial_cash_required",
    "after_transaction_cash",
    "required_buffer",
    "safety_surplus",
    "cash_floor_surplus",
    "dividend_loss",
    "annual_property_cf",
    "annual_cf_delta",
    "monthly_cf_delta",
]

for col in money_cols:
    if col in display.columns:
        display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")

if "months_covered_after" in display.columns:
    display["months_covered_after"] = display["months_covered_after"].map(lambda x: f"{x:.1f}か月" if pd.notna(x) else "-")

table_cols = [
    "scenario",
    "status",
    "liquidity_score",
    "after_transaction_cash",
    "required_buffer",
    "safety_surplus",
    "cash_floor_surplus",
    "months_covered_after",
    "monthly_cf_delta",
    "funds_acquisition",
    "sold_names",
    "cfo_comment",
]

st.dataframe(display[[c for c in table_cols if c in display.columns]], width="stretch", hide_index=True)

st.markdown("---")
st.subheader("チャート")

chart_df = scenario_review.copy()

fig = px.bar(
    chart_df,
    x="scenario",
    y="safety_surplus",
    color="status",
    title="シナリオ別 安全資金余剰/不足",
)
st.plotly_chart(fig, width="stretch")

fig2 = px.bar(
    chart_df,
    x="scenario",
    y="after_transaction_cash",
    color="status",
    title="シナリオ別 取得後現金",
)
st.plotly_chart(fig2, width="stretch")

fig3 = px.scatter(
    chart_df,
    x="months_covered_after",
    y="monthly_cf_delta",
    size="after_transaction_cash",
    color="status",
    hover_name="scenario",
    title="生活費月数 vs 月次CF差分",
)
st.plotly_chart(fig3, width="stretch")

st.markdown("---")
st.subheader("シナリオ詳細")

for _, row in scenario_review.iterrows():
    with st.expander(f"{row['scenario']} | {row['status']} | score {row['liquidity_score']:.1f}", expanded=False):
        st.markdown(row["cfo_comment"])
        st.markdown(f"**売却銘柄:** {row.get('sold_names', '-')}")
        st.markdown(f"**税引後売却資金:** {yen(row.get('net_proceeds'))}")
        st.markdown(f"**取得後現金:** {yen(row.get('after_transaction_cash'))}")
        st.markdown(f"**安全資金余剰/不足:** {yen(row.get('safety_surplus'))}")
        st.markdown(f"**月次CF差分:** {yen(row.get('monthly_cf_delta'))}")

st.markdown("---")
st.info("この画面は流動性の安全確認です。実行前には、実際の銀行残高、カード支払予定、税金、修繕予定、融資実行条件を必ず確認してください。")
