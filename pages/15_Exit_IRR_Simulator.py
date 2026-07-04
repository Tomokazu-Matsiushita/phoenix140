import pandas as pd
import plotly.express as px
import streamlit as st

from services.real_estate import ExitIRRInput, ExitIRRService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Exit IRR Simulator", page_icon="🚪", layout="wide")
apply_theme()

st.title("🚪 Exit / IRR Simulator")
st.caption("保有年数・売却価格・残債・累積CFを含めて、不動産投資の出口リターンを確認します。")

service = ExitIRRService()

with st.sidebar:
    st.header("物件・借入条件")

    property_name = st.text_input("物件名", value="oblige新田町")
    purchase_price = st.number_input("購入価格", min_value=0, value=76_000_000, step=1_000_000)
    loan_amount = st.number_input("借入額", min_value=0, value=76_000_000, step=1_000_000)
    annual_interest_rate = st.number_input("金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    loan_years = st.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)

    st.header("投下自己資金・CF")
    initial_cash_required = st.number_input("初期必要資金", min_value=0, value=5_320_000, step=100_000)
    annual_cash_flow = st.number_input("年間返済後CF", value=2_475_987, step=100_000)
    annual_cash_flow_growth_rate = st.number_input("年間CF成長率（%）", min_value=-20.0, max_value=20.0, value=0.0, step=0.5)

    st.header("出口条件")
    holding_years = st.number_input("保有年数", min_value=1, max_value=50, value=10, step=1)
    exit_price = st.number_input("売却価格", min_value=0, value=76_000_000, step=1_000_000)
    selling_cost_rate = st.number_input("売却諸費用率（%）", min_value=0.0, max_value=20.0, value=4.0, step=0.5)

    st.header("税金 簡易設定")
    annual_depreciation = st.number_input("年間減価償却費", min_value=0, value=0, step=100_000)
    capital_gain_tax_rate = st.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=20.315, step=0.1)

inputs = ExitIRRInput(
    property_name=property_name,
    purchase_price=float(purchase_price),
    loan_amount=float(loan_amount),
    annual_interest_rate=float(annual_interest_rate),
    loan_years=float(loan_years),
    initial_cash_required=float(initial_cash_required),
    annual_cash_flow=float(annual_cash_flow),
    annual_cash_flow_growth_rate=float(annual_cash_flow_growth_rate),
    holding_years=int(holding_years),
    exit_price=float(exit_price),
    selling_cost_rate=float(selling_cost_rate),
    annual_depreciation=float(annual_depreciation),
    capital_gain_tax_rate=float(capital_gain_tax_rate),
)

result = service.evaluate(inputs)

st.subheader("出口リターン サマリー")

c1, c2, c3, c4 = st.columns(4)
c1.metric("判定", result["health"])
c2.metric("IRR", "-" if result["irr"] is None else f"{result['irr']:.2%}")
c3.metric("総損益", yen(result["total_profit"]))
c4.metric("回収倍率", "-" if result["equity_multiple"] is None else f"{result['equity_multiple']:.2f}x")

c5, c6, c7, c8 = st.columns(4)
c5.metric("累積CF", yen(result["cumulative_cash_flow"]))
c6.metric("売却後手残り", yen(result["sale_cash_after_debt_tax"]))
c7.metric("売却時残債", yen(result["remaining_loan_balance"]))
c8.metric("年平均単純利回り", "-" if result["simple_annual_return"] is None else f"{result['simple_annual_return']:.2%}")

if result["health"] == "有力":
    st.success(result["cfo_comment"])
elif result["health"] == "条件付き":
    st.info(result["cfo_comment"])
elif result["health"] == "低リターン":
    st.warning(result["cfo_comment"])
else:
    st.error(result["cfo_comment"])

st.markdown("---")
st.subheader("出口計算の内訳")

detail_rows = [
    ("購入価格", result["purchase_price"]),
    ("初期必要資金", result["initial_cash_required"]),
    ("月額返済", result["monthly_payment"]),
    ("年間返済", result["annual_debt_service"]),
    ("売却価格", result["exit_price"]),
    ("売却諸費用", result["selling_cost"]),
    ("売却時残債", result["remaining_loan_balance"]),
    ("課税譲渡益 簡易", result["taxable_gain"]),
    ("譲渡益税 簡易", result["capital_gain_tax"]),
    ("売却後手残り", result["sale_cash_after_debt_tax"]),
    ("累積CF", result["cumulative_cash_flow"]),
    ("総回収額", result["total_recovery"]),
    ("総損益", result["total_profit"]),
]

detail_df = pd.DataFrame(detail_rows, columns=["項目", "金額"])
detail_df["金額"] = detail_df["金額"].map(yen)
st.dataframe(detail_df, width="stretch", hide_index=True)

st.markdown("---")
st.subheader("年次キャッシュフロー")

cash_flow_df = pd.DataFrame(
    {
        "year": list(range(0, len(result["cash_flows"]))),
        "cash_flow": result["cash_flows"],
    }
)
display_cf = cash_flow_df.copy()
display_cf["cash_flow"] = display_cf["cash_flow"].map(yen)
st.dataframe(display_cf, width="stretch", hide_index=True)

fig_cf = px.bar(cash_flow_df, x="year", y="cash_flow", title="年次キャッシュフロー")
st.plotly_chart(fig_cf, width="stretch")

st.markdown("---")
st.subheader("保有年数・売却価格ストレス")

stress = service.sensitivity_table(inputs)

if not stress.empty:
    irr_pivot = stress.pivot(index="holding_years", columns="exit_price_change_rate", values="irr")
    profit_pivot = stress.pivot(index="holding_years", columns="exit_price_change_rate", values="total_profit")

    st.caption("IRRマトリクス")
    irr_display = irr_pivot.copy()
    for col in irr_display.columns:
        irr_display[col] = irr_display[col].map(lambda x: f"{x:.2%}" if pd.notna(x) else "-")
    st.dataframe(irr_display, width="stretch")

    st.caption("総損益マトリクス")
    profit_display = profit_pivot.copy()
    for col in profit_display.columns:
        profit_display[col] = profit_display[col].map(lambda x: yen(x) if pd.notna(x) else "-")
    st.dataframe(profit_display, width="stretch")

    fig = px.line(
        stress,
        x="holding_years",
        y="irr",
        color="exit_price_change_rate",
        markers=True,
        title="保有年数・売却価格変化率別 IRR",
    )
    st.plotly_chart(fig, width="stretch")

    fig2 = px.line(
        stress,
        x="holding_years",
        y="total_profit",
        color="exit_price_change_rate",
        markers=True,
        title="保有年数・売却価格変化率別 総損益",
    )
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.info("このIRRは簡易シミュレーションです。実際の税金、減価償却、仲介手数料、繰上返済手数料、修繕費、売却時期、空室変動は別途確認してください。")
