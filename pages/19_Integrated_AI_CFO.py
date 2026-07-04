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

assumptions, inputs, _ = render_integrated_scenario_sidebar(page_key="integrated_ai_cfo", include_memo=False)

st.info(
    "このページは Scenario Assumptions Center の保存値を初期値として読み込みます。"
    "左サイドバーで変更した値は、このページの判断に即時反映されます。"
    "共通条件として残す場合は、サイドバー下部の「このページの条件をCenterに保存」を押してください。"
)

with st.expander("🎛️ 現在この判断に使っているAssumptions", expanded=True):
    st.caption(
        "ここに表示されている値が、Integrated AI CFOへ渡されている現在の入力値です。"
        "Center保存値から読み込まれ、サイドバー変更後の値が反映されています。"
    )

    meta_cols = st.columns(3)
    meta_cols[0].metric("Scenario", assumptions.get("scenario_name", "Base Case"))
    meta_cols[1].metric("Last saved", assumptions.get("saved_at") or "Not saved")
    meta_cols[2].metric("Source", "config/scenario_assumptions.json + sidebar")

    trace_rows = [
        {"section": "Safety", "parameter": "現在現金", "value": yen(inputs.current_cash), "used_for": "取得後現金・安全資金判定"},
        {"section": "Safety", "parameter": "月間生活費", "value": yen(inputs.monthly_living_expense), "used_for": "生活費何か月分残るか"},
        {"section": "Safety", "parameter": "生活防衛資金 月数", "value": f"{inputs.emergency_months:.1f}か月", "used_for": "必要安全資金"},
        {"section": "Safety", "parameter": "修繕予備資金", "value": yen(inputs.property_repair_reserve), "used_for": "必要安全資金"},
        {"section": "Safety", "parameter": "税金予備資金", "value": yen(inputs.tax_reserve), "used_for": "必要安全資金"},
        {"section": "Safety", "parameter": "最低現金ライン", "value": yen(inputs.minimum_cash_floor), "used_for": "危険判定"},
        {"section": "Sale", "parameter": "売却目標 税引後", "value": yen(inputs.target_net_cash), "used_for": "売却案の必要資金判定"},
        {"section": "Sale", "parameter": "譲渡益税率", "value": f"{inputs.tax_rate:.3%}", "used_for": "株式売却税額"},
        {"section": "Sale", "parameter": "除外銘柄", "value": "、".join(inputs.preserve_names or []), "used_for": "売却候補から除外"},
        {"section": "Sale", "parameter": "コア除外", "value": str(inputs.preserve_core_policy), "used_for": "コア資産保護"},
        {"section": "Sale", "parameter": "海運株最大売却比率", "value": f"{inputs.shipping_max_sell_ratio:.0%}", "used_for": "海運株の売却制限"},
        {"section": "Acquisition", "parameter": "物件名", "value": inputs.acquisition_input.property_name, "used_for": "取得シナリオ"},
        {"section": "Acquisition", "parameter": "購入価格", "value": yen(inputs.acquisition_input.purchase_price), "used_for": "利回り・必要資金"},
        {"section": "Acquisition", "parameter": "借入額", "value": yen(inputs.acquisition_input.loan_amount), "used_for": "返済額・DSCR"},
        {"section": "Acquisition", "parameter": "金利", "value": f"{inputs.acquisition_input.annual_interest_rate:.2f}%", "used_for": "返済額・DSCR"},
        {"section": "Acquisition", "parameter": "借入期間", "value": f"{inputs.acquisition_input.loan_years:.0f}年", "used_for": "返済額"},
        {"section": "Acquisition", "parameter": "満室月額賃料", "value": yen(inputs.acquisition_input.monthly_full_rent), "used_for": "NOI・CF"},
        {"section": "Acquisition", "parameter": "想定空室率", "value": f"{inputs.acquisition_input.vacancy_rate:.2f}%", "used_for": "有効賃料・CF"},
        {"section": "Exit", "parameter": "保有年数", "value": f"{inputs.exit_input.holding_years}年", "used_for": "IRR・残債"},
        {"section": "Exit", "parameter": "売却価格", "value": yen(inputs.exit_input.exit_price), "used_for": "売却後手残り・IRR"},
        {"section": "Exit", "parameter": "年間返済後CF", "value": yen(inputs.exit_input.annual_cash_flow), "used_for": "累積CF・IRR"},
        {"section": "Exit", "parameter": "初期必要資金", "value": yen(inputs.exit_input.initial_cash_required), "used_for": "IRR・回収倍率"},
    ]

    st.dataframe(pd.DataFrame(trace_rows), width="stretch", hide_index=True)

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

with st.expander("🧮 判断がどう変わるかのCalculation Trace", expanded=True):
    if best:
        calc_rows = [
            {"item": "最有力売却シナリオ", "value": best.get("scenario", "-"), "meaning": "Auto Sell Planの中で流動性スコアが最も高い案"},
            {"item": "税引後売却資金", "value": yen(best.get("net_proceeds")), "meaning": "株式売却で使える資金"},
            {"item": "取得初期必要資金", "value": yen(best.get("initial_cash_required")), "meaning": "物件購入時に必要な自己資金・諸費用"},
            {"item": "取得後現金", "value": yen(best.get("after_transaction_cash")), "meaning": "現在現金 + 売却資金 - 初期必要資金"},
            {"item": "安全資金差額", "value": yen(best.get("safety_surplus")), "meaning": "取得後現金 - 必要安全資金"},
            {"item": "配当減少/年", "value": yen(best.get("dividend_loss")), "meaning": "売却により失う年間配当"},
            {"item": "不動産CF/年", "value": yen(best.get("annual_property_cf")), "meaning": "取得物件の返済後CF"},
            {"item": "年間CF差分", "value": yen(best.get("annual_cf_delta")), "meaning": "不動産CF - 配当減少"},
            {"item": "取得DSCR", "value": "-" if best.get("acquisition_dscr") is None else f"{best.get('acquisition_dscr'):.2f}x", "meaning": "NOI / 年間返済額"},
            {"item": "出口IRR", "value": "-" if exit_result.get("irr") is None else f"{exit_result.get('irr'):.2%}", "meaning": "保有中CFと売却後手残りを含むIRR"},
            {"item": "最終スコア", "value": f"{score:.1f}", "meaning": "安全資金・CF・DSCR・IRR等を総合したルールベーススコア"},
        ]
        st.dataframe(pd.DataFrame(calc_rows), width="stretch", hide_index=True)
    else:
        st.warning("計算トレースを表示できるシナリオがありません。")

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
