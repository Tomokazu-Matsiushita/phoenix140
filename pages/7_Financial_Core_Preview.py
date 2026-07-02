import streamlit as st
import plotly.express as px

from services.financial import FinancialService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Financial Core Preview", page_icon="🧱", layout="wide")
apply_theme()

st.title("🧱 Financial Core Preview")
st.caption("Sprint 2の金融サービス層プレビューです。既存DBを使いながら、将来の正規化モデルへ移行する土台です。")

service = FinancialService()
summary = service.financial_summary()

c1, c2, c3, c4 = st.columns(4)
c1.metric("金融資産合計", yen(summary["total_assets"]))
c2.metric("株式", yen(summary["stock_value"]))
c3.metric("現預金", yen(summary["cash_value"]))
c4.metric("年間配当", yen(summary["annual_dividend"]))

tab1, tab2, tab3 = st.tabs(["配当ランキング", "損益通算候補", "売却優先候補"])

with tab1:
    df = service.dividend_ranking()
    st.dataframe(df, width="stretch", hide_index=True)

with tab2:
    df = service.tax_loss_candidates()
    st.dataframe(df, width="stretch", hide_index=True)

with tab3:
    df = service.sell_priority_candidates()
    st.dataframe(df, width="stretch", hide_index=True)
    if not df.empty:
        fig = px.bar(df, x="name", y="sell_priority_score", title="売却優先度スコア（低いほど売却候補）")
        st.plotly_chart(fig, width="stretch")
