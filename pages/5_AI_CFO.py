import streamlit as st
from services.bootstrap import bootstrap
from services.queries import get_dashboard_metrics
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="AI CFO", page_icon="🤖", layout="wide")
apply_theme()
bootstrap()

st.title("🤖 AI CFO")
st.caption("Version 3ではローカルルールベース。Version 4でOpenAI API接続を想定。")

m = get_dashboard_metrics()

if st.button("月次レビューを生成"):
    st.markdown(f"""
## 月次レビュー

### 全体
金融資産は **{yen(m["financial_assets"])}**、年間CFは **{yen(m["annual_cf"])}** です。  
FIRE達成率は **{m["fire_rate"]:.1f}%** です。

### 不動産
不動産は **{m["properties"]}棟 / {m["units"]}戸**、稼働率は **{m["occupancy_rate"]:.1f}%** です。  
稼働率が90%を下回る場合は、募集条件・広告費・原状回復スピードを確認してください。

### 株式
年間配当は **{yen(m["annual_dividend"])}** です。  
今後は「コア銘柄」と「調整銘柄」を分け、資金需要時は調整銘柄から売却する方針が合理的です。

### 次のアクション
1. 不動産の月次収支を入力する  
2. 空室の募集状況を更新する  
3. 金融API連携の認証情報を準備する  
4. Version 4で健康データ連携を追加する
""")
else:
    st.info("ボタンを押すと、現在のDBデータに基づいてレビューを生成します。")
