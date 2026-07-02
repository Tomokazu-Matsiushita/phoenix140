import streamlit as st
import plotly.express as px
from services.bootstrap import bootstrap
from services.queries import properties_df, units_df
from services.formatting import yen
from db.database import SessionLocal
from models.tables import Property
from utils.style import apply_theme

st.set_page_config(page_title="Real Estate", page_icon="🏢", layout="wide")
apply_theme()
bootstrap()

st.title("🏢 Real Estate")
st.caption("不動産情報をダッシュボード上から追加・編集できます。")

props = properties_df()
units = units_df()

with st.expander("＋物件を追加", expanded=False):
    with st.form("add_property"):
        name = st.text_input("物件名")
        location = st.text_input("所在地")
        purchase_price = st.number_input("購入価格", min_value=0, step=100000)
        loan_balance = st.number_input("残債", min_value=0, step=100000)
        interest_rate = st.number_input("金利（%）", min_value=0.0, step=0.1)
        loan_years = st.number_input("返済期間（年）", min_value=0, step=1)
        monthly_payment = st.number_input("月返済額", min_value=0, step=1000)
        unit_count = st.number_input("戸数", min_value=0, step=1)
        memo = st.text_area("メモ")
        submitted = st.form_submit_button("保存")
        if submitted and name:
            with SessionLocal() as s:
                s.add(Property(
                    name=name, location=location, purchase_price=purchase_price,
                    loan_balance=loan_balance, interest_rate=interest_rate,
                    loan_years=loan_years, monthly_payment=monthly_payment,
                    units=unit_count, memo=memo
                ))
                s.commit()
            st.success("物件を追加しました。画面を再読み込みしてください。")

c1, c2, c3 = st.columns(3)
c1.metric("物件数", f"{len(props)}棟")
c2.metric("総戸数", f"{int(props['units'].sum()) if not props.empty else 0}戸")
c3.metric("月返済合計", yen(props["monthly_payment"].sum() if not props.empty else 0))

st.dataframe(props, use_container_width=True, hide_index=True)

if not props.empty:
    fig = px.bar(props, x="name", y="loan_balance", title="物件別残債")
    st.plotly_chart(fig, use_container_width=True)
