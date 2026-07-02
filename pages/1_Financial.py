import streamlit as st
import plotly.express as px
from services.bootstrap import bootstrap
from services.queries import financial_assets_df
from services.formatting import yen
from db.database import SessionLocal
from models.tables import FinancialAsset
from utils.style import apply_theme

st.set_page_config(page_title="Financial", page_icon="📈", layout="wide")
apply_theme()
bootstrap()

st.title("📈 Financial Assets")
st.caption("金融資産。Version 3ではDB保存、Version 4でMoneytree API等に接続予定。")

df = financial_assets_df()

c1, c2, c3 = st.columns(3)
c1.metric("金融資産合計", yen(df["value"].sum()))
c2.metric("年間配当", yen(df["annual_dividend"].sum()))
c3.metric("銘柄・口座数", len(df))

tab1, tab2, tab3 = st.tabs(["一覧", "構成", "API連携"])

with tab1:
    st.dataframe(df[["institution","account_name","asset_type","name","sector","quantity","value","annual_dividend","policy","source"]], width="stretch", hide_index=True)

with tab2:
    fig = px.pie(df.groupby("asset_type", as_index=False)["value"].sum(), names="asset_type", values="value", hole=0.45)
    st.plotly_chart(fig, width="stretch")

with tab3:
    st.info("Moneytree APIの公式認証情報が準備できたら、connectors/moneytree.py を実装します。")
    st.code("MONEYTREE_ACCESS_TOKEN=...", language="bash")
    if st.button("金融API同期（現在はプレースホルダー）"):
        st.warning("まだ公式API未設定です。Version 4で接続します。")
