import streamlit as st
import pandas as pd
import plotly.express as px

from repositories.financial_repository import FinancialRepository
from services.financial import SellSimulator, MarketPriceService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Sell Simulator", page_icon="🧮", layout="wide")
apply_theme()

st.title("🧮 Sell Simulator")
st.caption("特定口座での税引後手取り・損益通算・配当減少を試算します。")

repo = FinancialRepository()

with st.sidebar:
    st.header("Market Data")
    if st.button("現在株価を更新"):
        with st.spinner("Yahoo Financeから株価を取得しています..."):
            update_result = MarketPriceService().update_stock_prices()
        st.success("株価更新が完了しました。")
        st.dataframe(update_result, width="stretch", hide_index=True)
        st.rerun()

assets = repo.list_assets()

if assets.empty:
    st.warning("金融資産データがありません。")
    st.stop()

sellable = assets[
    (assets["quantity"] > 0)
    & (assets["current_price"] > 0)
    & (assets["cost_price"] >= 0)
].copy()

if sellable.empty:
    st.warning("売却シミュレーション可能な資産がありません。")
    st.stop()

sellable["cost_value"] = sellable["quantity"] * sellable["cost_price"]
sellable["gain_loss"] = sellable["value"] - sellable["cost_value"]
sellable["gain_loss_rate"] = sellable["gain_loss"] / sellable["cost_value"].replace(0, pd.NA) * 100

with st.sidebar:
    st.header("Simulation Settings")
    target_net_cash = st.number_input("目標税引後手取り", min_value=0, value=3_500_000, step=100_000)
    tax_rate_percent = st.number_input("税率（%）", min_value=0.0, max_value=50.0, value=20.315, step=0.001)
    tax_rate = tax_rate_percent / 100

if "last_price_updated_at" in sellable.columns and sellable["last_price_updated_at"].notna().any():
    latest_update = sellable["last_price_updated_at"].dropna().max()
    st.info(f"現在株価の最終更新: {latest_update}")

st.subheader("売却対象を選択")

default_candidates = [
    name for name in ["セルソース", "NZAMカーボン", "日本郵船", "商船三井", "大紀アルミ", "トヨタ自動車", "明和産業", "あおぞら銀行"]
    if name in sellable["name"].tolist()
]

selected = st.multiselect(
    "売却候補",
    options=sellable["name"].tolist(),
    default=default_candidates,
)

sale_plan = []

if selected:
    st.markdown("### 売却株数・口数")
    for name in selected:
        row = sellable[sellable["name"] == name].iloc[0]
        max_qty = float(row["quantity"])
        step = 1.0 if max_qty <= 10 else 100.0
        default_qty = max_qty if name in ["セルソース", "NZAMカーボン"] else min(max_qty, step)

        c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"保有: {max_qty:g}")
        c3.write(f"現在値: {yen(row['current_price'])}")
        sell_qty = c4.number_input(
            f"売却数量_{name}",
            min_value=0.0,
            max_value=max_qty,
            value=float(default_qty),
            step=step,
            label_visibility="collapsed",
        )
        sale_plan.append({"name": name, "sell_quantity": sell_qty})

simulator = SellSimulator()
result = simulator.simulate(
    assets=sellable,
    sale_plan=sale_plan,
    tax_rate=tax_rate,
    target_net_cash=target_net_cash,
)

st.markdown("---")
st.subheader("シミュレーション結果")

k1, k2, k3, k4 = st.columns(4)
k1.metric("売却代金", yen(result.gross_proceeds))
k2.metric("譲渡損益", yen(result.realized_gain_loss))
k3.metric("税額", yen(result.tax))
k4.metric("税引後手取り", yen(result.net_proceeds))

k5, k6, k7 = st.columns(3)
k5.metric("年間配当減少", yen(result.dividend_loss))
k6.metric("目標との差額", yen(result.surplus_shortfall))
k7.metric("課税対象利益", yen(result.taxable_gain))

if result.surplus_shortfall >= 0:
    st.success(f"目標税引後手取り {yen(target_net_cash)} を達成しています。")
else:
    st.warning(f"目標まで {yen(abs(result.surplus_shortfall))} 不足しています。")

if not result.details.empty:
    display = result.details.copy()
    for col in ["current_price", "cost_price", "gross_proceeds", "cost_basis", "realized_gain_loss", "annual_dividend_loss"]:
        display[col] = display[col].map(lambda x: f"{x:,.0f}")

    st.dataframe(display, width="stretch", hide_index=True)

    chart_df = result.details.sort_values("gross_proceeds", ascending=True)
    fig = px.bar(chart_df, x="gross_proceeds", y="name", orientation="h", title="売却代金内訳")
    st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.subheader("売却候補一覧")
view = sellable.sort_values("gain_loss")
st.dataframe(
    view[["name", "asset_type", "sector", "quantity", "cost_price", "current_price", "value", "gain_loss", "annual_dividend", "policy"]],
    width="stretch",
    hide_index=True,
)
