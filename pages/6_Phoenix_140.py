import streamlit as st
from utils.style import apply_theme

st.set_page_config(page_title="Phoenix 140", page_icon="❤️", layout="wide")
apply_theme()

st.title("❤️ Phoenix 140")
st.caption("健康も資産。Version 4でOura/Garmin/Apple Health連携予定。")

c1, c2, c3, c4 = st.columns(4)
c1.metric("VO2max", "55", "target")
c2.metric("Full Marathon", "3:45:18")
c3.metric("Sleep", "Oura連携予定")
c4.metric("Goal", "140歳")

st.markdown("""
## Version 4で追加予定

- Oura睡眠スコア
- Garmin VO2max
- 体重・安静時心拍
- 年間走行距離
- 健康資産スコア
""")
