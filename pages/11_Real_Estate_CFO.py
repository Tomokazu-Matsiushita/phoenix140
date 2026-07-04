import pandas as pd
import plotly.express as px
import streamlit as st

from services.real_estate import RealEstateCFOService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Real Estate CFO", page_icon="🏢", layout="wide")
apply_theme()

st.title("🏢 Real Estate CFO")
st.caption("物件別の収入・空室・ローン返済・DSCRを確認するCFOビューです。")

service = RealEstateCFOService()
snapshot = service.snapshot()
summary = snapshot["summary"]

def pct(value):
    if value is None:
        return "-"
    return f"{value:.1%}"

def yen_or_dash(value):
    if value is None:
        return "-"
    return yen(value)

c1, c2, c3, c4 = st.columns(4)
c1.metric("物件数", f"{summary['property_count']}")
c2.metric("総戸数", f"{summary['total_units']}")
c3.metric("入居戸数", f"{summary['occupied_units']}")
c4.metric("稼働率", pct(summary["occupancy_rate"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("月額賃料収入", yen_or_dash(summary["monthly_rent"]))
c6.metric("年間賃料収入", yen_or_dash(summary["annual_rent"]))
c7.metric("年間返済額", yen_or_dash(summary["annual_debt_service"]))
c8.metric("DSCR", "-" if summary["dscr"] is None else f"{summary['dscr']:.2f}x")

c9, c10, c11 = st.columns(3)
c9.metric("年間経費", yen_or_dash(summary["annual_expense"]))
c10.metric("NOI", yen_or_dash(summary["noi"]))
c11.metric("返済後CF", yen_or_dash(summary["cash_flow_after_debt"]))

st.markdown("---")
st.subheader("物件別サマリー")

property_summary = service.property_summary()

if property_summary.empty:
    st.info("物件別サマリーを作成できるデータがまだありません。既存のReal Estateページで物件・部屋・月次CFを登録してください。")
else:
    display = property_summary.copy()
    for col in ["annual_income", "price", "monthly_rent"]:
        if col in display.columns:
            display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")
    if "gross_yield" in display.columns:
        display["gross_yield"] = display["gross_yield"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "-")

    st.dataframe(display, width="stretch", hide_index=True)

    numeric_summary = property_summary.copy()
    if "annual_income" in numeric_summary.columns and "property" in numeric_summary.columns:
        fig = px.bar(numeric_summary, x="property", y="annual_income", title="物件別年間収入")
        st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.subheader("データ確認")

tabs = st.tabs(["Properties", "Units", "Monthly CF", "Loans", "Repairs", "Available Tables"])

with tabs[0]:
    df = snapshot["properties"]
    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("properties table not found or empty.")

with tabs[1]:
    df = snapshot["units"]
    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("units table not found or empty.")

with tabs[2]:
    df = snapshot["monthly_cashflows"]
    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("monthly cashflow table not found or empty.")

with tabs[3]:
    df = snapshot["loans"]
    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("loans table not found or empty.")

with tabs[4]:
    df = snapshot["repairs"]
    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("repairs table not found or empty.")

with tabs[5]:
    tables_df = pd.DataFrame({"table_name": snapshot["available_tables"]})
    st.dataframe(tables_df, width="stretch", hide_index=True)
