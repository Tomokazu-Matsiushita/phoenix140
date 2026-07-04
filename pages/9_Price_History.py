import pandas as pd
import plotly.express as px
import streamlit as st

from services.financial import MarketPriceService, PriceHistoryService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Price History", page_icon="📈", layout="wide")
apply_theme()

st.title("📈 Price History")
st.caption("現在株価の更新履歴と前回更新からの変化を確認します。")

with st.sidebar:
    st.header("Market Data")
    if st.button("現在株価を更新"):
        with st.spinner("Yahoo Financeから株価を取得しています..."):
            update_result = MarketPriceService().update_stock_prices()
        st.success("株価更新が完了しました。")
        st.dataframe(update_result, width="stretch", hide_index=True)
        st.rerun()

service = PriceHistoryService()
latest = service.latest_by_name()
history = service.latest_history(limit=1000)

if history.empty:
    st.info("まだ価格履歴がありません。左側の「現在株価を更新」を押すと履歴が作成されます。")
    st.stop()

st.subheader("Latest Prices")

latest_view = latest.copy()
latest_view["price"] = latest_view["price"].map(lambda x: yen(x))
st.dataframe(latest_view, width="stretch", hide_index=True)

st.subheader("Price History Chart")

names = history["name"].dropna().unique().tolist()
selected_names = st.multiselect("表示銘柄", options=names, default=names[:5])

chart_df = history[history["name"].isin(selected_names)].copy()
chart_df["recorded_at"] = pd.to_datetime(chart_df["recorded_at"])

if not chart_df.empty:
    fig = px.line(chart_df.sort_values("recorded_at"), x="recorded_at", y="price", color="name", markers=True)
    st.plotly_chart(fig, width="stretch")

st.subheader("Raw History")
view = history.copy()
view["recorded_at"] = pd.to_datetime(view["recorded_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
st.dataframe(view, width="stretch", hide_index=True)
