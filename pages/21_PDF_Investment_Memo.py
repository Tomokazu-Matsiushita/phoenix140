from datetime import datetime

import streamlit as st

from services.integrated_ai_cfo_service import IntegratedCFOInput
from services.investment_memo_pdf_service import InvestmentMemoPDFService
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService
from services.real_estate import AcquisitionInput, ExitIRRInput
from utils.style import apply_theme

st.set_page_config(page_title="PDF Investment Memo", page_icon="📄", layout="wide")
apply_theme()

st.title("📄 PDF Investment Memo Export")
st.caption("Integrated AI CFOの判断結果をPDF投資判断メモとして出力します。")

memo_service = InvestmentMemoService()
pdf_service = InvestmentMemoPDFService()

with st.sidebar:
    st.header("メモ情報")
    title = st.text_input("タイトル", value="Phoenix 140 Investment Decision Memo")
    author = st.text_input("作成者", value="Phoenix AI CFO")
    purpose = st.text_area("目的", value="株式売却による資金確保と不動産取得の可否を総合判断する。")
    memo_date = st.text_input("作成日", value=datetime.now().strftime("%Y-%m-%d %H:%M"))

    st.header("安全資金")
    current_cash = st.number_input("現在の現金・銀行残高", min_value=0, value=4_856_312, step=100_000)
    monthly_living_expense = st.number_input("月間生活費", min_value=0, value=700_000, step=50_000)
    emergency_months = st.number_input("生活防衛資金 月数", min_value=0.0, max_value=36.0, value=6.0, step=1.0)
    property_repair_reserve = st.number_input("不動産修繕予備資金", min_value=0, value=1_500_000, step=100_000)
    tax_reserve = st.number_input("税金予備資金", min_value=0, value=500_000, step=100_000)
    minimum_cash_floor = st.number_input("最低現金ライン", min_value=0, value=2_000_000, step=100_000)

    st.header("売却条件")
    target_net_cash = st.number_input("売却目標 税引後手取り", min_value=0, value=3_500_000, step=100_000)
    tax_rate_percent = st.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=20.315, step=0.1)
    preserve_core_policy = st.checkbox("policy=コアを除外", value=True)
    preserve_names_text = st.text_area("除外銘柄（改行区切り）", value="三菱商事\n三井住友FG\n武田薬品\nJT")
    shipping_ratio = st.slider("海運株の最大売却比率", min_value=0.0, max_value=1.0, value=0.5, step=0.1)

    st.header("取得条件")
    property_name = st.text_input("物件名", value="oblige新田町")
    purchase_price = st.number_input("購入価格", min_value=0, value=76_000_000, step=1_000_000)
    loan_amount = st.number_input("借入額", min_value=0, value=76_000_000, step=1_000_000)
    annual_interest_rate = st.number_input("金利（%）", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    loan_years = st.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=34.0, step=1.0)
    acquisition_cost_rate = st.number_input("諸費用率（%）", min_value=0.0, max_value=30.0, value=7.0, step=0.5)
    monthly_full_rent = st.number_input("満室月額賃料", min_value=0, value=665_000, step=10_000)
    vacancy_rate = st.number_input("想定空室率（%）", min_value=0.0, max_value=100.0, value=8.33, step=0.5)
    fixed_asset_tax_annual = st.number_input("固定資産税/年", min_value=0, value=618_429, step=10_000)
    management_fee_monthly = st.number_input("管理費/月", min_value=0, value=59_300, step=1_000)
    repair_reserve_monthly = st.number_input("修繕積立/月", min_value=0, value=30_000, step=5_000)

    st.header("出口条件")
    holding_years = st.number_input("保有年数", min_value=1, max_value=50, value=10, step=1)
    exit_price = st.number_input("売却価格", min_value=0, value=76_000_000, step=1_000_000)
    annual_cash_flow = st.number_input("年間返済後CF", value=2_475_987, step=100_000)
    initial_cash_required = st.number_input("初期必要資金", min_value=0, value=5_320_000, step=100_000)

preserve_names = [x.strip() for x in preserve_names_text.splitlines() if x.strip()]

acquisition_input = AcquisitionInput(
    property_name=property_name,
    purchase_price=float(purchase_price),
    loan_amount=float(loan_amount),
    annual_interest_rate=float(annual_interest_rate),
    loan_years=float(loan_years),
    acquisition_cost_rate=float(acquisition_cost_rate),
    monthly_full_rent=float(monthly_full_rent),
    vacancy_rate=float(vacancy_rate),
    fixed_asset_tax_annual=float(fixed_asset_tax_annual),
    management_fee_monthly=float(management_fee_monthly),
    repair_reserve_monthly=float(repair_reserve_monthly),
)

exit_input = ExitIRRInput(
    property_name=property_name,
    purchase_price=float(purchase_price),
    loan_amount=float(loan_amount),
    annual_interest_rate=float(annual_interest_rate),
    loan_years=float(loan_years),
    initial_cash_required=float(initial_cash_required),
    annual_cash_flow=float(annual_cash_flow),
    holding_years=int(holding_years),
    exit_price=float(exit_price),
)

integrated_input = IntegratedCFOInput(
    current_cash=float(current_cash),
    monthly_living_expense=float(monthly_living_expense),
    emergency_months=float(emergency_months),
    property_repair_reserve=float(property_repair_reserve),
    tax_reserve=float(tax_reserve),
    minimum_cash_floor=float(minimum_cash_floor),
    target_net_cash=float(target_net_cash),
    tax_rate=float(tax_rate_percent) / 100,
    preserve_names=preserve_names,
    preserve_core_policy=bool(preserve_core_policy),
    shipping_max_sell_ratio=float(shipping_ratio),
    acquisition_input=acquisition_input,
    exit_input=exit_input,
)

memo = memo_service.build(
    InvestmentMemoInput(
        title=title,
        author=author,
        purpose=purpose,
        memo_date=memo_date,
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

st.info("PDFはA4縦の投資判断メモです。細かな体裁は今後のSprintで調整できます。")
