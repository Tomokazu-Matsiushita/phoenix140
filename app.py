import streamlit as st
from services.bootstrap import bootstrap
from services.queries import get_dashboard_metrics
from services.formatting import yen
from utils.style import apply_theme
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Project Phoenix 140", page_icon="🔥", layout="wide")
apply_theme()
bootstrap()

metrics = get_dashboard_metrics()

st.sidebar.title("🔥 Project Phoenix 140")
st.sidebar.caption("v3 / SQLite + API-ready")
st.sidebar.markdown("---")
st.sidebar.caption("左側のPagesメニューから各ページへ移動してください。")

st.title("🔥 Project Phoenix 140")
st.caption("Tomokazu専用：資産・配当・家賃CF・FIRE・健康をつなぐ人生コックピット")

c1, c2, c3, c4 = st.columns(4)
c1.metric("金融資産", yen(metrics["financial_assets"]))
c2.metric("現預金", yen(metrics["cash"]))
c3.metric("年間配当", yen(metrics["annual_dividend"]))
c4.metric("年間家賃CF", yen(metrics["annual_property_cf"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("年間CF合計", yen(metrics["annual_cf"]))
c6.metric("月平均CF", yen(metrics["annual_cf"] / 12))
c7.metric("不動産", f'{metrics["properties"]}棟 / {metrics["units"]}戸')
c8.metric("FIRE達成率", f'{metrics["fire_rate"]:.1f}%')

st.markdown("### Financial freedom meter")
st.progress(min(metrics["fire_rate"] / 100, 1.0))
st.caption(f'{yen(metrics["annual_cf"])} / 目標生活費 {yen(metrics["annual_living_cost"])}')

left, right = st.columns([1.2, 1])

with left:
    st.subheader("資産構成")
    asset_mix = pd.DataFrame([
        {"区分": "株式", "金額": metrics["stocks"]},
        {"区分": "投資信託・WealthNavi・DC", "金額": metrics["investments"]},
        {"区分": "現預金", "金額": metrics["cash"]},
    ])
    fig = px.pie(asset_mix, names="区分", values="金額", hole=0.45)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("AI CFO Memo")
    st.markdown(f"""
#### 今月の見立て
- 年間CFは **{yen(metrics["annual_cf"])}**、FIRE達成率は **{metrics["fire_rate"]:.1f}%** です。
- 不動産は **{metrics["properties"]}棟 / {metrics["units"]}戸**。稼働率は **{metrics["occupancy_rate"]:.1f}%** です。
- Version 3では、CSVではなくSQLiteに保存します。
- 金融APIは `connectors/` 配下に差し替え口を用意済みです。
- Version 4ではOura/Garmin/Apple Health連携を追加できます。
""")
