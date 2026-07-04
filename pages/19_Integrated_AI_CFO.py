import pandas as pd
import streamlit as st

from components.scenario_sidebar import render_integrated_scenario_sidebar
from services.integrated_ai_cfo_service import IntegratedAICFOService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Integrated AI CFO", page_icon="🧠", layout="wide")
apply_theme()

st.title("🧠 Integrated AI CFO Final Recommendation")
st.caption("株式売却・不動産取得・流動性・出口IRRを束ねて、Phoenix CFOが最終判断を出します。")

_, inputs, _ = render_integrated_scenario_sidebar(page_key="integrated_ai_cfo", include_memo=False)

service = IntegratedAICFOService()
review = service.review(inputs)
decision = review["decision"]
best = review["best_scenario"]
exit_result = review["exit_result"]

st.subheader("Final Recommendation")

label = decision["label"]
headline = decision["headline"]
score = decision["score"]

if label == "実行候補":
    st.success(f"{label} | score {score:.1f} | {headline}")
elif label == "条件付き実行":
    st.info(f"{label} | score {score:.1f} | {headline}")
elif label == "待つ":
    st.warning(f"{label} | score {score:.1f} | {headline}")
else:
    st.error(f"{label} | score {score:.1f} | {headline}")

st.markdown(review["executive_summary"])

st.markdown("---")
st.subheader("Decision Factors")

factor_df = pd.DataFrame(review["decision_factors"])
st.dataframe(factor_df, width="stretch", hide_index=True)

st.markdown("---")
st.subheader("Must Check Before Action")

for item in review["must_check"]:
    st.markdown(f"- {item}")

st.markdown("---")
st.subheader("Best Scenario Snapshot")

if best:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最有力シナリオ", best.get("scenario", "-"))
    c2.metric("取得後現金", yen(best.get("after_transaction_cash")))
    c3.metric("安全資金差額", yen(best.get("safety_surplus")))
    c4.metric("年間CF差分", yen(best.get("annual_cf_delta")))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("売却手取り", yen(best.get("net_proceeds")))
    c6.metric("配当減少/年", yen(best.get("dividend_loss")))
    c7.metric("取得DSCR", "-" if best.get("acquisition_dscr") is None else f"{best.get('acquisition_dscr'):.2f}x")
    c8.metric("出口IRR", "-" if exit_result.get("irr") is None else f"{exit_result.get('irr'):.2%}")

    st.markdown(f"**売却銘柄:** {best.get('sold_names', '-')}")
    st.markdown(f"**流動性コメント:** {best.get('cfo_comment', '-')}")
else:
    st.warning("最有力シナリオがありません。")

st.markdown("---")
st.subheader("All Liquidity Scenarios")

scenario_review = review["liquidity_review"]["scenario_review"]

if not scenario_review.empty:
    display = scenario_review.copy()

    for col in [
        "net_proceeds",
        "dividend_loss",
        "initial_cash_required",
        "after_transaction_cash",
        "safety_surplus",
        "annual_property_cf",
        "annual_cf_delta",
        "monthly_cf_delta",
    ]:
        if col in display.columns:
            display[col] = display[col].map(lambda x: yen(x) if pd.notna(x) else "-")

    table_cols = [
        "scenario",
        "status",
        "liquidity_score",
        "net_proceeds",
        "after_transaction_cash",
        "safety_surplus",
        "annual_cf_delta",
        "funds_acquisition",
        "sold_names",
    ]

    st.dataframe(display[[c for c in table_cols if c in display.columns]], width="stretch", hide_index=True)
else:
    st.info("シナリオがありません。")

st.markdown("---")
st.info(
    "このページの初期値はScenario Assumptions Centerから読み込まれます。"
    "サイドバーで一時変更した値はこのページに即時反映されます。共通条件として残す場合は「このページの条件をCenterに保存」を押してください。"
)
