import streamlit as st
from services.bootstrap import bootstrap
from services.queries import properties_df, monthly_cf_df
from db.database import SessionLocal
from models.tables import MonthlyPropertyCF
from utils.style import apply_theme
from services.formatting import yen

st.set_page_config(page_title="Monthly CF", page_icon="💰", layout="wide")
apply_theme()
bootstrap()

st.title("💰 Monthly Property Cash Flow")
props = properties_df()
if props.empty:
    st.warning("先に物件を登録してください。")
    st.stop()

with st.form("monthly_cf"):
    prop_name = st.selectbox("物件", props["name"].tolist())
    prop_id = int(props.loc[props["name"] == prop_name, "id"].iloc[0])
    month = st.text_input("対象月（YYYY-MM）", value="2026-07")
    rent_income = st.number_input("家賃収入", min_value=0, step=1000)
    loan_payment = st.number_input("返済", min_value=0, step=1000)
    management_fee = st.number_input("管理料", min_value=0, step=1000)
    repair_cost = st.number_input("修繕費", min_value=0, step=1000)
    tax_cost = st.number_input("税金", min_value=0, step=1000)
    other_cost = st.number_input("その他", min_value=0, step=1000)
    memo = st.text_area("メモ")
    submitted = st.form_submit_button("保存")
    if submitted:
        with SessionLocal() as s:
            s.add(MonthlyPropertyCF(
                property_id=prop_id, month=month, rent_income=rent_income,
                loan_payment=loan_payment, management_fee=management_fee,
                repair_cost=repair_cost, tax_cost=tax_cost, other_cost=other_cost, memo=memo
            ))
            s.commit()
        st.success("月次収支を保存しました。")

df = monthly_cf_df()
if not df.empty:
    df["net_cf"] = df["rent_income"] - df["loan_payment"] - df["management_fee"] - df["repair_cost"] - df["tax_cost"] - df["other_cost"]
    st.metric("登録済みCF合計", yen(df["net_cf"].sum()))
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("まだ月次収支の登録がありません。")
