import pandas as pd
import plotly.express as px
import streamlit as st

from services.moneytree import MoneytreeDataService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Moneytree Dashboard", page_icon="🌳", layout="wide")
apply_theme()

st.title("🌳 Moneytree Dashboard")
st.caption("Moneytree由来データの口座残高・資産内訳・取引履歴を表示します。")

service = MoneytreeDataService()
service.migrate()

summary = service.portfolio_summary()
accounts = service.read_accounts()
transactions = service.read_transactions(limit=500)

c1, c2, c3 = st.columns(3)
c1.metric("Total balance", yen(summary["total_balance"]))
c2.metric("Accounts", summary["account_count"])
c3.metric("Transactions", summary["transaction_count"])

st.markdown("---")
st.subheader("Accounts")

if accounts.empty:
    st.info("口座データがありません。Moneytree Manual ImportからCSVを取り込んでください。")
else:
    display_accounts = accounts.copy()
    if "balance" in display_accounts.columns:
        display_accounts["balance"] = display_accounts["balance"].map(yen)
    st.dataframe(display_accounts, width="stretch", hide_index=True)

    col1, col2 = st.columns(2)

    by_institution = summary["by_institution"]
    if not by_institution.empty:
        fig = px.bar(
            by_institution,
            x="institution",
            y="balance",
            title="Balance by institution",
        )
        col1.plotly_chart(fig, width="stretch")

    by_type = summary["by_type"]
    if not by_type.empty:
        fig2 = px.pie(
            by_type,
            names="account_type",
            values="balance",
            title="Balance by account type",
        )
        col2.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.subheader("Transactions")

if transactions.empty:
    st.info("取引データがありません。")
else:
    tx = transactions.copy()
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)

    monthly_cashflow = summary["monthly_cashflow"]
    spending_by_category = summary["spending_by_category"]

    col1, col2 = st.columns(2)

    if not monthly_cashflow.empty:
        fig3 = px.bar(
            monthly_cashflow,
            x="month",
            y="amount",
            title="Monthly net cashflow",
        )
        col1.plotly_chart(fig3, width="stretch")

    if not spending_by_category.empty:
        fig4 = px.bar(
            spending_by_category.head(15),
            x="category",
            y="expense_amount",
            title="Spending by category",
        )
        col2.plotly_chart(fig4, width="stretch")

    display_tx = tx.copy()
    if "amount" in display_tx.columns:
        display_tx["amount"] = display_tx["amount"].map(yen)

    st.dataframe(display_tx, width="stretch", hide_index=True)

st.markdown("---")
st.info("このDashboardは手動CSVインポートデータを表示します。次Sprint以降でMoneytree API Connectorをこのデータモデルへ接続します。")
