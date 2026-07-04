from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from services.scenario_assumptions_service import ScenarioAssumptionsService


def render_integrated_scenario_sidebar(
    page_key: str,
    include_memo: bool = False,
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    service = ScenarioAssumptionsService()
    saved = service.load()

    st.sidebar.header("Scenario Assumptions")
    st.sidebar.caption("初期値は Scenario Assumptions Center の保存条件から読み込みます。")
    st.sidebar.write(f"Scenario: **{saved.get('scenario_name', 'Base Case')}**")
    if saved.get("saved_at"):
        st.sidebar.caption(f"Last saved: {saved.get('saved_at')}")

    memo = dict(saved.get("memo", {}))
    safety = dict(saved.get("safety", {}))
    sale = dict(saved.get("sale", {}))
    acquisition = dict(saved.get("acquisition", {}))
    exit_plan = dict(saved.get("exit", {}))

    current: dict[str, Any] = {
        "version": saved.get("version", "1.0"),
        "scenario_name": saved.get("scenario_name", "Base Case"),
        "memo": memo,
        "safety": safety,
        "sale": sale,
        "acquisition": acquisition,
        "exit": exit_plan,
    }

    if include_memo:
        st.sidebar.header("メモ情報")
        memo["title"] = st.sidebar.text_input(
            "タイトル",
            value=str(memo.get("title", "Phoenix 140 Investment Decision Memo")),
            key=f"{page_key}_memo_title",
        )
        memo["author"] = st.sidebar.text_input(
            "作成者",
            value=str(memo.get("author", "Phoenix AI CFO")),
            key=f"{page_key}_memo_author",
        )
        memo["purpose"] = st.sidebar.text_area(
            "目的",
            value=str(memo.get("purpose", "株式売却による資金確保と不動産取得の可否を総合判断する。")),
            key=f"{page_key}_memo_purpose",
        )
        memo["memo_date"] = st.sidebar.text_input(
            "作成日",
            value=datetime.now().strftime("%Y-%m-%d %H:%M"),
            key=f"{page_key}_memo_date",
        )

    st.sidebar.header("安全資金")
    safety["current_cash"] = st.sidebar.number_input("現在の現金・銀行残高", min_value=0, value=int(safety.get("current_cash", 4_856_312)), step=100_000, key=f"{page_key}_current_cash")
    safety["monthly_living_expense"] = st.sidebar.number_input("月間生活費", min_value=0, value=int(safety.get("monthly_living_expense", 700_000)), step=50_000, key=f"{page_key}_living")
    safety["emergency_months"] = st.sidebar.number_input("生活防衛資金 月数", min_value=0.0, max_value=36.0, value=float(safety.get("emergency_months", 6.0)), step=1.0, key=f"{page_key}_emergency_months")
    safety["property_repair_reserve"] = st.sidebar.number_input("不動産修繕予備資金", min_value=0, value=int(safety.get("property_repair_reserve", 1_500_000)), step=100_000, key=f"{page_key}_repair_reserve")
    safety["tax_reserve"] = st.sidebar.number_input("税金予備資金", min_value=0, value=int(safety.get("tax_reserve", 500_000)), step=100_000, key=f"{page_key}_tax_reserve")
    safety["other_commitments"] = st.sidebar.number_input("その他予定支出", min_value=0, value=int(safety.get("other_commitments", 0)), step=100_000, key=f"{page_key}_other_commitments")
    safety["minimum_cash_floor"] = st.sidebar.number_input("最低現金ライン", min_value=0, value=int(safety.get("minimum_cash_floor", 2_000_000)), step=100_000, key=f"{page_key}_cash_floor")

    st.sidebar.header("売却条件")
    sale["target_net_cash"] = st.sidebar.number_input("売却目標 税引後手取り", min_value=0, value=int(sale.get("target_net_cash", 3_500_000)), step=100_000, key=f"{page_key}_target_cash")
    sale["tax_rate_percent"] = st.sidebar.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=float(sale.get("tax_rate_percent", 20.315)), step=0.1, key=f"{page_key}_tax_rate")
    sale["preserve_core_policy"] = st.sidebar.checkbox("policy=コアを除外", value=bool(sale.get("preserve_core_policy", True)), key=f"{page_key}_core_policy")
    preserve_names_text = st.sidebar.text_area(
        "除外銘柄（改行区切り）",
        value="\n".join(sale.get("preserve_names", ["三菱商事", "三井住友FG", "武田薬品", "JT"])),
        key=f"{page_key}_preserve_names",
    )
    sale["preserve_names"] = [x.strip() for x in preserve_names_text.splitlines() if x.strip()]
    sale["shipping_max_sell_ratio"] = st.sidebar.slider("海運株の最大売却比率", min_value=0.0, max_value=1.0, value=float(sale.get("shipping_max_sell_ratio", 0.5)), step=0.1, key=f"{page_key}_shipping_ratio")

    st.sidebar.header("取得条件")
    acquisition["property_name"] = st.sidebar.text_input("物件名", value=str(acquisition.get("property_name", "oblige新田町")), key=f"{page_key}_property_name")
    acquisition["purchase_price"] = st.sidebar.number_input("購入価格", min_value=0, value=int(acquisition.get("purchase_price", 76_000_000)), step=1_000_000, key=f"{page_key}_purchase_price")
    acquisition["loan_amount"] = st.sidebar.number_input("借入額", min_value=0, value=int(acquisition.get("loan_amount", 76_000_000)), step=1_000_000, key=f"{page_key}_loan_amount")
    acquisition["annual_interest_rate"] = st.sidebar.number_input("金利（%）", min_value=0.0, max_value=20.0, value=float(acquisition.get("annual_interest_rate", 3.0)), step=0.1, key=f"{page_key}_rate")
    acquisition["loan_years"] = st.sidebar.number_input("借入期間（年）", min_value=1.0, max_value=50.0, value=float(acquisition.get("loan_years", 34.0)), step=1.0, key=f"{page_key}_loan_years")
    acquisition["acquisition_cost_rate"] = st.sidebar.number_input("諸費用率（%）", min_value=0.0, max_value=30.0, value=float(acquisition.get("acquisition_cost_rate", 7.0)), step=0.5, key=f"{page_key}_acq_cost")
    acquisition["units"] = st.sidebar.number_input("戸数", min_value=1, max_value=200, value=int(acquisition.get("units", 12)), step=1, key=f"{page_key}_units")
    acquisition["monthly_full_rent"] = st.sidebar.number_input("満室月額賃料", min_value=0, value=int(acquisition.get("monthly_full_rent", 665_000)), step=10_000, key=f"{page_key}_full_rent")
    acquisition["vacancy_rate"] = st.sidebar.number_input("想定空室率（%）", min_value=0.0, max_value=100.0, value=float(acquisition.get("vacancy_rate", 8.33)), step=0.5, key=f"{page_key}_vacancy")
    acquisition["fixed_asset_tax_annual"] = st.sidebar.number_input("固定資産税/年", min_value=0, value=int(acquisition.get("fixed_asset_tax_annual", 618_429)), step=10_000, key=f"{page_key}_fixed_tax")
    acquisition["management_fee_monthly"] = st.sidebar.number_input("管理費/月", min_value=0, value=int(acquisition.get("management_fee_monthly", 59_300)), step=1_000, key=f"{page_key}_mgmt_fee")
    acquisition["repair_reserve_monthly"] = st.sidebar.number_input("修繕積立/月", min_value=0, value=int(acquisition.get("repair_reserve_monthly", 30_000)), step=5_000, key=f"{page_key}_repair_monthly")

    st.sidebar.header("出口条件")
    exit_plan["holding_years"] = st.sidebar.number_input("保有年数", min_value=1, max_value=50, value=int(exit_plan.get("holding_years", 10)), step=1, key=f"{page_key}_holding_years")
    exit_plan["exit_price"] = st.sidebar.number_input("売却価格", min_value=0, value=int(exit_plan.get("exit_price", 76_000_000)), step=1_000_000, key=f"{page_key}_exit_price")
    exit_plan["annual_cash_flow"] = st.sidebar.number_input("年間返済後CF", value=int(exit_plan.get("annual_cash_flow", 2_475_987)), step=100_000, key=f"{page_key}_annual_cf")
    exit_plan["initial_cash_required"] = st.sidebar.number_input("初期必要資金", min_value=0, value=int(exit_plan.get("initial_cash_required", 5_320_000)), step=100_000, key=f"{page_key}_initial_cash")
    exit_plan["selling_cost_rate"] = st.sidebar.number_input("売却諸費用率（%）", min_value=0.0, max_value=30.0, value=float(exit_plan.get("selling_cost_rate", 4.0)), step=0.5, key=f"{page_key}_selling_cost")
    exit_plan["annual_depreciation"] = st.sidebar.number_input("年間減価償却費", min_value=0, value=int(exit_plan.get("annual_depreciation", 0)), step=100_000, key=f"{page_key}_depreciation")
    exit_plan["capital_gain_tax_rate"] = st.sidebar.number_input("譲渡益税率（%）", min_value=0.0, max_value=60.0, value=float(exit_plan.get("capital_gain_tax_rate", 20.315)), step=0.1, key=f"{page_key}_exit_tax")

    st.sidebar.markdown("---")
    current["scenario_name"] = st.sidebar.text_input("保存シナリオ名", value=str(current.get("scenario_name", "Base Case")), key=f"{page_key}_scenario_name")

    if st.sidebar.button("このページの条件をCenterに保存", key=f"{page_key}_save_assumptions"):
        saved_now = service.save(current)
        st.sidebar.success("Scenario Assumptions Centerに保存しました。")
        current = saved_now

    integrated_input = service.to_integrated_input(current)
    memo_info = {
        "title": memo.get("title", "Phoenix 140 Investment Decision Memo"),
        "author": memo.get("author", "Phoenix AI CFO"),
        "purpose": memo.get("purpose", "株式売却による資金確保と不動産取得の可否を総合判断する。"),
        "memo_date": memo.get("memo_date", datetime.now().strftime("%Y-%m-%d %H:%M")),
    }

    return current, integrated_input, memo_info
