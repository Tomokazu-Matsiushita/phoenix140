import streamlit as st
from services.bootstrap import bootstrap
from services.queries import properties_df, units_df
from db.database import SessionLocal
from models.tables import RentalUnit
from utils.style import apply_theme

st.set_page_config(page_title="Units", page_icon="🚪", layout="wide")
apply_theme()
bootstrap()

st.title("🚪 Units / 入居状況")
props = properties_df()
units = units_df()

if props.empty:
    st.warning("先に物件を登録してください。")
    st.stop()

prop_name = st.selectbox("物件", props["name"].tolist())
prop_id = int(props.loc[props["name"] == prop_name, "id"].iloc[0])
target = units[units["property_id"] == prop_id] if not units.empty else units

with st.expander("＋部屋を追加", expanded=False):
    with st.form("add_unit"):
        room_no = st.text_input("部屋番号")
        rent = st.number_input("賃料", min_value=0, step=1000)
        management_fee = st.number_input("共益費", min_value=0, step=500)
        parking_fee = st.number_input("駐車場", min_value=0, step=500)
        occupied = st.checkbox("入居中", value=True)
        submitted = st.form_submit_button("保存")
        if submitted and room_no:
            with SessionLocal() as s:
                s.add(RentalUnit(property_id=prop_id, room_no=room_no, rent=rent, management_fee=management_fee, parking_fee=parking_fee, occupied=occupied))
                s.commit()
            st.success("部屋を追加しました。画面を再読み込みしてください。")

st.dataframe(target[["room_no","rent","management_fee","parking_fee","occupied"]], use_container_width=True, hide_index=True)
if not target.empty:
    st.metric("稼働率", f"{target['occupied'].mean()*100:.1f}%")
