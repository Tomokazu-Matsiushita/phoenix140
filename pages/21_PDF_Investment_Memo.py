from datetime import datetime

import streamlit as st

from components.scenario_sidebar import render_integrated_scenario_sidebar
from services.investment_memo_pdf_service import InvestmentMemoPDFService
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService
from utils.style import apply_theme

st.set_page_config(page_title="PDF Investment Memo", page_icon="📄", layout="wide")
apply_theme()

st.title("📄 PDF Investment Memo Export")
st.caption("Integrated AI CFOの判断結果をPDF投資判断メモとして出力します。")

_, integrated_input, memo_info = render_integrated_scenario_sidebar(
    page_key="pdf_investment_memo",
    include_memo=True,
)

memo_service = InvestmentMemoService()
pdf_service = InvestmentMemoPDFService()

memo = memo_service.build(
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

st.subheader("PDF Memo Summary")

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

pdf_bytes = pdf_service.build_pdf_bytes(memo)
file_stem = f"phoenix140_investment_memo_{datetime.now().strftime('%Y%m%d_%H%M')}"

st.download_button(
    label="PDF投資判断メモをダウンロード",
    data=pdf_bytes,
    file_name=f"{file_stem}.pdf",
    mime="application/pdf",
)

st.markdown("---")
st.subheader("PDF Contents")
st.markdown("- Final Recommendation")
st.markdown("- Best Scenario Snapshot")
st.markdown("- Decision Factors")
st.markdown("- Acquisition Summary")
st.markdown("- Exit / IRR Summary")
st.markdown("- Liquidity & Safety")
st.markdown("- Scenario Comparison")
st.markdown("- Must Check Before Action")
st.markdown("- CFO Note")

st.info(
    "このページの初期値はScenario Assumptions Centerから読み込まれます。"
    "サイドバーで一時変更した値はこのPDFに即時反映されます。"
)
