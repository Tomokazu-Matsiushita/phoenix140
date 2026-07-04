from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

from services.moneytree import MoneytreeDataService
from utils.style import apply_theme

st.set_page_config(page_title="Moneytree Manual Import", page_icon="🌳", layout="wide")
apply_theme()

st.title("🌳 Moneytree Manual Import")
st.caption("Moneytree連携の前段階として、口座残高CSV・取引CSVをPhoenix 140へ取り込みます。")

service = MoneytreeDataService()
service.migrate()

st.info(
    "このSprintでは公式API接続前の土台として、CSV手動インポートを作ります。"
    "将来のMoneytree API同期は、このテーブルに流し込む形で接続できます。"
)

tab_accounts, tab_transactions, tab_templates, tab_admin = st.tabs(
    ["Accounts CSV", "Transactions CSV", "Templates", "Admin"]
)

with tab_accounts:
    st.subheader("口座残高CSVインポート")
    st.caption("必要列: 金融機関 / 口座名 / 口座番号 / 残高。英語列名でもOKです。")

    uploaded = st.file_uploader("Accounts CSV", type=["csv"], key="moneytree_accounts_csv")

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.dataframe(df.head(20), width="stretch")

        if st.button("口座残高をインポート", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name

            result = service.import_accounts_csv(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)

            if result.errors:
                st.warning(f"Inserted: {result.inserted}, Skipped: {result.skipped}, Errors: {len(result.errors)}")
                st.write(result.errors[:10])
            else:
                st.success(f"Imported accounts: {result.inserted}")

with tab_transactions:
    st.subheader("取引CSVインポート")
    st.caption("必要列: 日付 / 摘要 / 金額。カテゴリ・口座番号などがあれば一緒に取り込みます。")

    uploaded_tx = st.file_uploader("Transactions CSV", type=["csv"], key="moneytree_transactions_csv")

    if uploaded_tx is not None:
        df_tx = pd.read_csv(uploaded_tx)
        st.dataframe(df_tx.head(20), width="stretch")

        if st.button("取引をインポート", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_tx.getvalue())
                tmp_path = tmp.name

            result = service.import_transactions_csv(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)

            if result.errors:
                st.warning(f"Inserted: {result.inserted}, Skipped: {result.skipped}, Errors: {len(result.errors)}")
                st.write(result.errors[:10])
            else:
                st.success(f"Imported transactions: {result.inserted}, skipped duplicates: {result.skipped}")

with tab_templates:
    st.subheader("CSVテンプレート")

    account_template = pd.DataFrame(
        [
            {
                "金融機関": "三井住友銀行",
                "口座名": "普通",
                "口座番号": "****1234",
                "口座種別": "bank",
                "通貨": "JPY",
                "残高": 1000000,
                "残高日": "2026-07-04",
            }
        ]
    )

    transaction_template = pd.DataFrame(
        [
            {
                "日付": "2026-07-04",
                "金融機関": "三井住友銀行",
                "口座名": "普通",
                "口座番号": "****1234",
                "摘要": "サンプル支出",
                "カテゴリ": "食費",
                "サブカテゴリ": "外食",
                "金額": -1500,
                "通貨": "JPY",
                "メモ": "",
            }
        ]
    )

    st.download_button(
        "Accounts template CSV",
        data=account_template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="moneytree_accounts_template.csv",
        mime="text/csv",
    )

    st.download_button(
        "Transactions template CSV",
        data=transaction_template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="moneytree_transactions_template.csv",
        mime="text/csv",
    )

    st.markdown("#### Accounts template")
    st.dataframe(account_template, width="stretch", hide_index=True)

    st.markdown("#### Transactions template")
    st.dataframe(transaction_template, width="stretch", hide_index=True)

with tab_admin:
    st.subheader("Admin")

    accounts = service.read_accounts()
    transactions = service.read_transactions(limit=20)
    sync_log = service.read_sync_log()

    c1, c2, c3 = st.columns(3)
    c1.metric("Accounts", len(accounts))
    c2.metric("Transactions shown", len(transactions))
    c3.metric("Sync log", len(sync_log))

    if st.checkbox("手動インポートデータを削除する"):
        if st.button("manual_csvデータを削除", type="primary"):
            service.clear_manual_data()
            st.warning("manual_csvデータを削除しました。")
            st.rerun()

    st.markdown("#### Sync log")
    st.dataframe(sync_log, width="stretch", hide_index=True)
