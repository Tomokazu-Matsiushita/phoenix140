from datetime import datetime

import streamlit as st

from components.scenario_sidebar import render_integrated_scenario_sidebar
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService
from utils.style import apply_theme

st.set_page_config(page_title="Investment Memo Export", page_icon="📝", layout="wide")
apply_theme()

st.title("📝 Investment Memo / Decision Report Export")
st.caption("Integrated AI CFOの判断結果を、投資判断メモとしてMarkdown/CSVで出力します。")

assumptions, integrated_input, memo_info = render_integrated_scenario_sidebar(
    page_key="investment_memo",
    include_memo=True,
)

service = InvestmentMemoService()
memo = service.build(
    InvestmentMemoInput(
        title=memo_info["title"],
        author=memo_info["author"],
        purpose=memo_info["purpose"],
        memo_date=memo_info.get("memo_date"),
        integrated_input=integrated_input,
    )
)

review = memo["review"]
decision = review["decision"]
markdown = memo["markdown"]
tables = memo["tables"]

st.subheader("Memo Summary")

label = decision.get("label", "-")
score = decision.get("score", 0)

if label == "実行候補":
    st.success(f"{label} | score {score:.1f}")
elif label == "条件付き実行":
    st.info(f"{label} | score {score:.1f}")
elif label == "待つ":
    st.warning(f"{label} | score {score:.1f}")
else:
    st.error(f"{label} | score {score:.1f}")

st.markdown(review["executive_summary"])

st.markdown("---")
st.subheader("Download")

file_stem = f"phoenix140_investment_memo_{datetime.now().strftime('%Y%m%d_%H%M')}"

st.download_button(
    label="Markdownメモをダウンロード",
    data=markdown.encode("utf-8"),
    file_name=f"{file_stem}.md",
    mime="text/markdown",
)

scenario_csv = tables["scenario_review"].to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="Scenario CSVをダウンロード",
    data=scenario_csv.encode("utf-8-sig"),
    file_name=f"{file_stem}_scenario_review.csv",
    mime="text/csv",
)

factor_csv = tables["decision_factors"].to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="Decision Factors CSVをダウンロード",
    data=factor_csv.encode("utf-8-sig"),
    file_name=f"{file_stem}_decision_factors.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Memo Preview")

st.markdown(markdown)

st.markdown("---")
st.info(
    "このページの初期値はScenario Assumptions Centerから読み込まれます。"
    "サイドバーで一時変更した値はこのメモに即時反映されます。"
)
