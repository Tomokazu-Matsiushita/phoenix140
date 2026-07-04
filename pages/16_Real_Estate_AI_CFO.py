import pandas as pd
import streamlit as st

from services.real_estate import (
    AcquisitionInput,
    ExitIRRInput,
    RealEstateAICFOService,
)
from utils.style import apply_theme

st.set_page_config(page_title="Real Estate AI CFO", page_icon="🧠", layout="wide")
apply_theme()

st.title("🧠 Real Estate AI CFO")
st.caption("不動産ポートフォリオ・取得判断・出口判断をPhoenix CFOがルールベースでレビューします。")

service = RealEstateAICFOService()

with st.sidebar:
    st.header("取得シナリオ")
    include_acquisition = st.checkbox("取得判断もレビューする", value=True)

    acq_property_name = st.text_input("取得物件名", value="oblige新田町")
    acq_purchase_price = st.number_input("取得 購入価格", min_value=0, value=76_000_000, step=1_000_000)
    acq_loan_amount = st.number_input("取得 借入額", min_value=0, value=76_000_000, step=1_000_000)
    acq_rate = st.number_input("取得 金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    acq_years = st.number_input("取得 借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)
    acq_monthly_full_rent = st.number_input("取得 満室月額賃料", min_value=0, value=665_000, step=10_000)
    acq_vacancy = st.number_input("取得 想定空室率（%）", min_value=0.0, max_value=100.0, value=8.33, step=0.5)

    st.header("出口シナリオ")
    include_exit = st.checkbox("出口判断もレビューする", value=True)

    exit_property_name = st.text_input("出口物件名", value="oblige新田町")
    exit_purchase_price = st.number_input("出口 購入価格", min_value=0, value=76_000_000, step=1_000_000)
    exit_loan_amount = st.number_input("出口 借入額", min_value=0, value=76_000_000, step=1_000_000)
    exit_rate = st.number_input("出口 金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    exit_years = st.number_input("出口 借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)
    exit_initial_cash = st.number_input("出口 初期必要資金", min_value=0, value=5_320_000, step=100_000)
    exit_annual_cf = st.number_input("出口 年間返済後CF", value=2_475_987, step=100_000)
    exit_holding_years = st.number_input("出口 保有年数", min_value=1, max_value=50, value=10, step=1)
    exit_price = st.number_input("出口 売却価格", min_value=0, value=76_000_000, step=1_000_000)

acquisition_input = None
if include_acquisition:
    acquisition_input = AcquisitionInput(
        property_name=acq_property_name,
        purchase_price=float(acq_purchase_price),
        loan_amount=float(acq_loan_amount),
        annual_interest_rate=float(acq_rate),
        loan_years=float(acq_years),
        monthly_full_rent=float(acq_monthly_full_rent),
        vacancy_rate=float(acq_vacancy),
    )

exit_input = None
if include_exit:
    exit_input = ExitIRRInput(
        property_name=exit_property_name,
        purchase_price=float(exit_purchase_price),
        loan_amount=float(exit_loan_amount),
        annual_interest_rate=float(exit_rate),
        loan_years=float(exit_years),
        initial_cash_required=float(exit_initial_cash),
        annual_cash_flow=float(exit_annual_cf),
        holding_years=int(exit_holding_years),
        exit_price=float(exit_price),
    )

review = service.full_review(
    acquisition_input=acquisition_input,
    exit_input=exit_input,
)

st.subheader("Executive Summary")
st.info(review["executive_summary"])

if review["priority_actions"]:
    st.subheader("Priority Actions")
    for idx, action in enumerate(review["priority_actions"], start=1):
        st.markdown(f"{idx}. {action}")

st.markdown("---")
st.subheader("CFO Review Cards")

comments = review["comments"]

if not comments:
    st.warning("レビュー対象がありません。")
    st.stop()

status_order = {
    "良好": "✅",
    "有力": "🟢",
    "条件付き": "🟡",
    "注意": "⚠️",
    "要改善": "🔴",
    "見送り": "🔴",
    "要データ確認": "⚠️",
}

for item in comments:
    icon = status_order.get(item["status"], "ℹ️")
    with st.expander(f"{icon} {item['title']} | {item['status']} | score {item['score']:.0f}", expanded=True):
        st.markdown(item["summary"])

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("#### Strengths")
            if item["strengths"]:
                for strength in item["strengths"]:
                    st.markdown(f"- {strength}")
            else:
                st.caption("特になし")

        with c2:
            st.markdown("#### Risks")
            if item["risks"]:
                for risk in item["risks"]:
                    st.markdown(f"- {risk}")
            else:
                st.caption("大きなリスクは検出されていません。")

        with c3:
            st.markdown("#### Actions")
            if item["actions"]:
                for action in item["actions"]:
                    st.markdown(f"- {action}")
            else:
                st.caption("追加アクションなし")

st.markdown("---")
st.subheader("Review Table")

table = pd.DataFrame(
    [
        {
            "area": item["area"],
            "title": item["title"],
            "status": item["status"],
            "score": item["score"],
            "summary": item["summary"],
        }
        for item in comments
    ]
)

st.dataframe(table, width="stretch", hide_index=True)

st.markdown("---")
st.info("このコメントはルールベースのPhoenix AI CFOです。実際の投資判断では、家賃相場、修繕履歴、融資条件、税務、売却可能性を必ず別途確認してください。")
