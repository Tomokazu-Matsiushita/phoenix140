import pandas as pd
import streamlit as st

from services.phoenix_command_center_service import PhoenixCommandCenterService
from utils.style import apply_theme

try:
    from services.formatting import yen
except Exception:
    def yen(value):
        if value is None:
            return "-"
        try:
            return f"¥{float(value):,.0f}"
        except Exception:
            return str(value)


def pct(value):
    if value is None:
        return "-"
    try:
        return f"{float(value):.2%}"
    except Exception:
        return str(value)


def number_or_dash(value, suffix=""):
    if value is None:
        return "-"
    try:
        return f"{float(value):,.2f}{suffix}"
    except Exception:
        return str(value)


def render_flag(flag):
    level = flag.get("level", "info")
    text = f"**{flag.get('area', '-')}** — {flag.get('message', '')}"
    if level == "danger":
        st.error(text)
    elif level == "warning":
        st.warning(text)
    elif level == "success":
        st.success(text)
    else:
        st.info(text)


st.set_page_config(page_title="Phoenix Command Center", page_icon="🔥", layout="wide")
apply_theme()

service = PhoenixCommandCenterService()
data = service.build()
s = data["snapshot"]
moneytree = data["moneytree_summary"]

st.title("🔥 Phoenix 140 Command Center")
st.caption("金融資産・不動産・安全資金・最終判断・健康の入口を1画面で確認する一覧ダッシュボードです。")

st.info(
    "ここは全体俯瞰用のホーム画面です。細かい条件変更はScenario Assumptions Center、"
    "最終判断の詳細はIntegrated AI CFO、実データ確認はMoneytree Dashboardで行います。"
)

top1, top2, top3, top4 = st.columns(4)
top1.metric("CFO Decision", s.decision_label, f"score {s.decision_score:.1f}")
top2.metric("Moneytree Balance", yen(s.moneytree_total_balance), f"{s.moneytree_account_count} accounts")
top3.metric("After Transaction Cash", yen(s.after_transaction_cash))
top4.metric("Safety Surplus", yen(s.safety_surplus))

st.markdown("---")

st.subheader("🚦 Today’s Watchlist")
for flag in data["risk_flags"]:
    render_flag(flag)

st.markdown("---")

left, right = st.columns([1.15, 0.85])

with left:
    st.subheader("🧭 One-page Snapshot")

    c1, c2, c3 = st.columns(3)
    c1.metric("Scenario", s.scenario_name)
    c2.metric("Best scenario", s.best_scenario_name or "-")
    c3.metric("Data status", s.sync_status)

    c4, c5, c6 = st.columns(3)
    c4.metric("Annual CF delta", yen(s.annual_cf_delta))
    c5.metric("Acquisition DSCR", number_or_dash(s.acquisition_dscr, "x"))
    c6.metric("Exit IRR", pct(s.exit_irr))

    c7, c8, c9 = st.columns(3)
    c7.metric("Property", s.property_name)
    c8.metric("Purchase price", yen(s.purchase_price))
    c9.metric("Vacancy rate", f"{s.vacancy_rate:.2f}%")

    st.markdown("#### Cash movement")
    cash_rows = [
        {"item": "現在現金（Scenario）", "value": yen(s.current_cash), "meaning": "Scenario Assumptions上の現在現金"},
        {"item": "売却目標 税引後", "value": yen(s.target_net_cash), "meaning": "株式売却で確保したい手取り"},
        {"item": "取得後現金", "value": yen(s.after_transaction_cash), "meaning": "現在現金 + 売却手取り - 初期必要資金"},
        {"item": "安全資金差額", "value": yen(s.safety_surplus), "meaning": "取得後現金 - 必要安全資金"},
        {"item": "年間不動産CF", "value": yen(s.annual_property_cf), "meaning": "物件取得による返済後CF"},
        {"item": "配当減少", "value": yen(s.dividend_loss), "meaning": "株式売却で失う年間配当"},
        {"item": "年間CF差分", "value": yen(s.annual_cf_delta), "meaning": "不動産CF - 配当減少"},
    ]
    st.dataframe(pd.DataFrame(cash_rows), width="stretch", hide_index=True)

with right:
    st.subheader("⚡ Quick Actions")

    for card in data["action_cards"]:
        with st.container(border=True):
            st.markdown(f"### {card['title']}")
            st.caption(card["status"])
            st.write(card["message"])
            st.markdown(f"Open page: **{card['page']}**")

    st.subheader("🩺 Health")
    health = data["health_summary"]
    with st.container(border=True):
        st.markdown(f"**Status:** {health['status']}")
        st.write(health["message"])
        st.caption("Candidate metrics: " + ", ".join(health["candidate_metrics"]))

st.markdown("---")

tab_financial, tab_real_estate, tab_moneytree, tab_trace = st.tabs(
    ["Financial", "Real Estate", "Moneytree", "Trace"]
)

with tab_financial:
    st.subheader("Financial Overview")

    quick = pd.DataFrame(data["quick_metrics"])
    display = quick.copy()

    def format_metric(row):
        unit = row.get("unit")
        value = row.get("value")
        if unit == "JPY":
            return yen(value)
        if unit == "%":
            return pct(value)
        if unit == "x":
            return number_or_dash(value, "x")
        if value is None:
            return "-"
        return value

    if not display.empty:
        display["display_value"] = display.apply(format_metric, axis=1)
        st.dataframe(
            display[["area", "metric", "display_value"]],
            width="stretch",
            hide_index=True,
        )

with tab_real_estate:
    st.subheader("Real Estate Overview")

    re_rows = [
        {"item": "物件名", "value": s.property_name},
        {"item": "購入価格", "value": yen(s.purchase_price)},
        {"item": "借入額", "value": yen(s.loan_amount)},
        {"item": "金利", "value": f"{s.interest_rate:.2f}%"},
        {"item": "想定空室率", "value": f"{s.vacancy_rate:.2f}%"},
        {"item": "出口売却価格", "value": yen(s.exit_price)},
        {"item": "年間返済後CF", "value": yen(s.annual_cash_flow)},
        {"item": "DSCR", "value": number_or_dash(s.acquisition_dscr, "x")},
        {"item": "出口IRR", "value": pct(s.exit_irr)},
    ]
    st.dataframe(pd.DataFrame(re_rows), width="stretch", hide_index=True)

with tab_moneytree:
    st.subheader("Moneytree Data Snapshot")

    mt1, mt2, mt3 = st.columns(3)
    mt1.metric("Total balance", yen(s.moneytree_total_balance))
    mt2.metric("Accounts", s.moneytree_account_count)
    mt3.metric("Transactions", s.moneytree_transaction_count)

    by_institution = moneytree.get("by_institution", pd.DataFrame())
    by_type = moneytree.get("by_type", pd.DataFrame())
    spending = moneytree.get("spending_by_category", pd.DataFrame())
    monthly = moneytree.get("monthly_cashflow", pd.DataFrame())

    if by_institution is not None and not by_institution.empty:
        st.markdown("#### Balance by institution")
        display = by_institution.copy()
        display["balance"] = display["balance"].map(yen)
        st.dataframe(display, width="stretch", hide_index=True)
    else:
        st.info("Moneytree口座データはまだありません。Moneytree Manual Importから取り込んでください。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Monthly cashflow")
        if monthly is not None and not monthly.empty:
            st.bar_chart(monthly.set_index("month")["amount"])
        else:
            st.caption("No transaction data")

    with col2:
        st.markdown("#### Spending by category")
        if spending is not None and not spending.empty:
            chart_df = spending.head(10).copy()
            st.bar_chart(chart_df.set_index("category")["expense_amount"])
        else:
            st.caption("No spending data")

with tab_trace:
    st.subheader("Data Flow Trace")

    st.markdown(
        """
```text
Scenario Assumptions Center
  ↓ config/scenario_assumptions.json
ScenarioAssumptionsService
  ↓ IntegratedCFOInput
Integrated AI CFO Service
  ↓ decision / best scenario / risk flags
Phoenix Command Center
```

```text
Moneytree Manual Import
  ↓ moneytree_accounts / moneytree_transactions
MoneytreeDataService
  ↓ balance / cashflow / spending summary
Phoenix Command Center
```
"""
    )

    trace_rows = [
        {"source": "Scenario Assumptions", "field": "scenario_name", "value": s.scenario_name},
        {"source": "Scenario Assumptions", "field": "saved_at", "value": s.scenario_saved_at or "-"},
        {"source": "Integrated AI CFO", "field": "decision_label", "value": s.decision_label},
        {"source": "Integrated AI CFO", "field": "score", "value": f"{s.decision_score:.1f}"},
        {"source": "Integrated AI CFO", "field": "best_scenario", "value": s.best_scenario_name or "-"},
        {"source": "Moneytree", "field": "account_count", "value": s.moneytree_account_count},
        {"source": "Moneytree", "field": "transaction_count", "value": s.moneytree_transaction_count},
        {"source": "Health", "field": "status", "value": data["health_summary"]["status"]},
    ]
    st.dataframe(pd.DataFrame(trace_rows), width="stretch", hide_index=True)
