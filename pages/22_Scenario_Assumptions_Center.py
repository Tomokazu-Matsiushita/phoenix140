import json
import pandas as pd
import streamlit as st

from services.scenario_assumptions_service import ScenarioAssumptionsService
from utils.style import apply_theme

st.set_page_config(page_title="Scenario Assumptions Center", page_icon="🎛️", layout="wide")
apply_theme()

st.title("🎛️ Scenario Assumptions Center")
st.caption("Integrated AI CFO、Investment Memo、PDF Memoで使う判断条件をここで一元管理します。")

service = ScenarioAssumptionsService()
assumptions = service.load()

st.info(
    "ここで保存した条件は、Integrated AI CFO / Investment Memo Export / PDF Investment Memo の初期値として読み込まれます。"
    "各ページのサイドバーで一時変更もできますが、共通条件として残す場合はこのCenterで保存してください。"
)

with st.form("scenario_assumptions_form"):
    st.subheader("Scenario")
    scenario_name = st.text_input("シナリオ名", value=str(assumptions.get("scenario_name", "Base Case")))
    saved_at = assumptions.get("saved_at")
    if saved_at:
        st.caption(f"Last saved: {saved_at}")

    memo = dict(assumptions.get("memo", {}))
    safety = dict(assumptions.get("safety", {}))
    sale = dict(assumptions.get("sale", {}))
    acquisition = dict(assumptions.get("acquisition", {}))
    exit_plan = dict(assumptions.get("exit", {}))

    tab_memo, tab_safety, tab_sale, tab_acq, tab_exit, tab_json = st.tabs(
        ["Memo", "Safety", "Sale", "Acquisition", "Exit", "JSON Preview"]
    )

    with tab_memo:
        memo["title"] = st.text_input("タイトル", value=str(memo.get("title", "Phoenix 140 Investment Decision Memo")))
        memo["author"] = st.text_input("作成者", value=str(memo.get("author", "Phoenix AI CFO")))
        memo["purpose"] = st.text_area("目的", value=str(memo.get("purpose", "株式売却による資金確保と不動産取得の可否を総合判断する。")))

    with tab_safety:
        c1, c2 = st.columns(2)
        safety["current_cash"] = c1.number_input("現在の現金・銀行残高", min_value=0, value=int(safety.get("current_cash", 4_856_312)), step=100_000)
        safety["monthly_living_expense"] = c2.number_input("月間生活費", min_value=0, value=int(safety.get("monthly_living_expense", 700_000)), step=50_000)
        safety["emergency_months"] = c1.number_input("生活防衛資金 月数", min_value=0.0, max_value=36.0, value=float(safety.get("emergency_months", 6.0)), step=1.0)
        safety["property_repair_reserve"] = c2.number_input("不動産修繕予備資金", min_value=0, value=int(safety.get("property_repair_reserve", 1_500_000)), step=100_000)
        safety["tax_reserve"] = c1.number_input("税金予備資金", min_value=0, value=int(safety.get("tax_reserve", 500_000)), step=100_000)
        safety["other_commitments"] = c2.number_input("その他予定支出", min_value=0, value=int(safety.get("other_commitments", 0)), step=100_000)
        safety["minimum_cash_floor"] = c1.number_input("最低現金ライン", min_value=0, value=int(safety.get("minimum_cash_floor", 2_000_000)), step=100_000)

    with tab_sale:
        c1, c2 = st.columns(2)
        sale["target_net_cash"] = c1.number_input("売却目標 税引後手取り", min_value=0, value=int(sale.get("target_net_cash", 3_500_000)), step=100_000)
        sale["tax_rate_percent"] = c2.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=float(sale.get("tax_rate_percent", 20.315)), step=0.1)
        sale["preserve_core_policy"] = c1.checkbox("policy=コアを除外", value=bool(sale.get("preserve_core_policy", True)))
        sale["shipping_max_sell_ratio"] = c2.slider("海運株の最大売却比率", min_value=0.0, max_value=1.0, value=float(sale.get("shipping_max_sell_ratio", 0.5)), step=0.1)
        preserve_names_text = st.text_area(
            "除外銘柄（改行区切り）",
            value="\n".join(sale.get("preserve_names", ["三菱商事", "三井住友FG", "武田薬品", "JT"])),
        )
        sale["preserve_names"] = [x.strip() for x in preserve_names_text.splitlines() if x.strip()]

    with tab_acq:
        c1, c2 = st.columns(2)
        acquisition["property_name"] = c1.text_input("物件名", value=str(acquisition.get("property_name", "oblige新田町")))
        acquisition["purchase_price"] = c2.number_input("購入価格", min_value=0, value=int(acquisition.get("purchase_price", 76_000_000)), step=1_000_000)
        acquisition["loan_amount"] = c1.number_input("借入額", min_value=0, value=int(acquisition.get("loan_amount", 76_000_000)), step=1_000_000)
        acquisition["annual_interest_rate"] = c2.number_input("金利（%）", min_value=0.0, max_value=20.0, value=float(acquisition.get("annual_interest_rate", 3.0)), step=0.1)
        acquisition["loan_years"] = c1.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=float(acquisition.get("loan_years", 34.0)), step=1.0)
        acquisition["acquisition_cost_rate"] = c2.number_input("諸費用率（%）", min_value=0.0, max_value=30.0, value=float(acquisition.get("acquisition_cost_rate", 7.0)), step=0.5)
        acquisition["units"] = c1.number_input("戸数", min_value=1, max_value=200, value=int(acquisition.get("units", 12)), step=1)
        acquisition["monthly_full_rent"] = c2.number_input("満室月額賃料", min_value=0, value=int(acquisition.get("monthly_full_rent", 665_000)), step=10_000)
        acquisition["vacancy_rate"] = c1.number_input("想定空室率（%）", min_value=0.0, max_value=100.0, value=float(acquisition.get("vacancy_rate", 8.33)), step=0.5)
        acquisition["fixed_asset_tax_annual"] = c2.number_input("固定資産税/年", min_value=0, value=int(acquisition.get("fixed_asset_tax_annual", 618_429)), step=10_000)
        acquisition["management_fee_monthly"] = c1.number_input("管理費/月", min_value=0, value=int(acquisition.get("management_fee_monthly", 59_300)), step=1_000)
        acquisition["repair_reserve_monthly"] = c2.number_input("修繕積立/月", min_value=0, value=int(acquisition.get("repair_reserve_monthly", 30_000)), step=5_000)

    with tab_exit:
        c1, c2 = st.columns(2)
        exit_plan["holding_years"] = c1.number_input("保有年数", min_value=1, max_value=50, value=int(exit_plan.get("holding_years", 10)), step=1)
        exit_plan["exit_price"] = c2.number_input("売却価格", min_value=0, value=int(exit_plan.get("exit_price", 76_000_000)), step=1_000_000)
        exit_plan["annual_cash_flow"] = c1.number_input("年間返済後CF", value=int(exit_plan.get("annual_cash_flow", 2_475_987)), step=100_000)
        exit_plan["initial_cash_required"] = c2.number_input("初期必要資金", min_value=0, value=int(exit_plan.get("initial_cash_required", 5_320_000)), step=100_000)
        exit_plan["selling_cost_rate"] = c1.number_input("売却諸費用率（%）", min_value=0.0, max_value=30.0, value=float(exit_plan.get("selling_cost_rate", 4.0)), step=0.5)
        exit_plan["annual_depreciation"] = c2.number_input("年間減価償却費", min_value=0, value=int(exit_plan.get("annual_depreciation", 0)), step=100_000)
        exit_plan["capital_gain_tax_rate"] = c1.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=float(exit_plan.get("capital_gain_tax_rate", 20.315)), step=0.1)

    updated = {
        "version": "1.0",
        "scenario_name": scenario_name,
        "memo": memo,
        "safety": safety,
        "sale": sale,
        "acquisition": acquisition,
        "exit": exit_plan,
    }

    with tab_json:
        st.code(json.dumps(updated, ensure_ascii=False, indent=2), language="json")

    c1, c2, c3 = st.columns(3)
    save = c1.form_submit_button("保存する", type="primary")
    reset = c2.form_submit_button("デフォルトに戻す")
    validate = c3.form_submit_button("入力チェック")

if save:
    service.save(updated)
    st.success("Scenario Assumptionsを保存しました。Integrated AI CFO / Memo / PDF の初期値に反映されます。")
    st.rerun()

if reset:
    service.reset()
    st.warning("デフォルト値に戻しました。")
    st.rerun()

if validate:
    integrated_input = service.to_integrated_input(updated)
    st.success("入力チェックOKです。IntegratedCFOInputを作成できます。")
    st.json(
        {
            "property_name": integrated_input.acquisition_input.property_name,
            "target_net_cash": integrated_input.target_net_cash,
            "current_cash": integrated_input.current_cash,
            "exit_price": integrated_input.exit_input.exit_price,
        }
    )

st.markdown("---")
st.subheader("Current Saved Assumptions")

rows = service.summary_rows(service.load())
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
