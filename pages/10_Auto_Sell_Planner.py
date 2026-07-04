import json
import hashlib

import pandas as pd
import plotly.express as px
import streamlit as st

from repositories.financial_repository import FinancialRepository
from services.financial import AutoSellPlanGenerator, MarketPriceService
from services.formatting import yen
from utils.style import apply_theme

st.set_page_config(page_title="Auto Sell Planner", page_icon="🤖", layout="wide")
apply_theme()

st.title("🤖 Auto Sell Planner")
st.caption("目標手取り額に対して、税効率・配当維持・バランス型の売却案を自動生成します。")

repo = FinancialRepository()

with st.sidebar:
    st.header("Market Data")
    if st.button("現在株価を更新", key="auto_sell_update_prices"):
        with st.spinner("Yahoo Financeから株価を取得しています..."):
            update_result = MarketPriceService().update_stock_prices()
        st.success("株価更新が完了しました。")
        st.dataframe(update_result, width="stretch", hide_index=True)
        st.rerun()

assets = repo.list_assets()

if assets.empty:
    st.warning("金融資産データがありません。")
    st.stop()

sellable_names = (
    assets[
        (assets["asset_type"].isin(["stock", "fund"]))
        & (assets["quantity"] > 0)
    ]["name"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .tolist()
)

default_core = [x for x in ["三菱商事", "三井住友FG", "武田薬品", "JT"] if x in sellable_names]

DEFAULT_CONFIG = {
    "target_net_cash": 3_500_000,
    "tax_rate_percent": 20.315,
    "shipping_ratio": 50,
    "preserve_names": default_core,
    "preserve_core_policy": True,
}

if "auto_sell_active_config" not in st.session_state:
    st.session_state.auto_sell_active_config = DEFAULT_CONFIG.copy()

# Initialize form widget state from active config only once.
if "auto_sell_form_initialized" not in st.session_state:
    active = st.session_state.auto_sell_active_config
    st.session_state.auto_sell_input_target_net_cash = active["target_net_cash"]
    st.session_state.auto_sell_input_tax_rate_percent = active["tax_rate_percent"]
    st.session_state.auto_sell_input_shipping_ratio = active["shipping_ratio"]
    st.session_state.auto_sell_input_preserve_names = active["preserve_names"]
    st.session_state.auto_sell_input_preserve_core_policy = active["preserve_core_policy"]
    st.session_state.auto_sell_form_initialized = True

if "auto_sell_run_id" not in st.session_state:
    st.session_state.auto_sell_run_id = 1


def normalize_names(names):
    return [str(x).strip() for x in names if str(x).strip()]


def config_fingerprint(config: dict) -> str:
    payload = {
        "target_net_cash": int(config["target_net_cash"]),
        "tax_rate_percent": float(config["tax_rate_percent"]),
        "shipping_ratio": int(config["shipping_ratio"]),
        "preserve_names": sorted(normalize_names(config["preserve_names"])),
        "preserve_core_policy": bool(config["preserve_core_policy"]),
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


st.subheader("条件設定")

with st.form("auto_sell_conditions_form", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    input_target_net_cash = c1.number_input(
        "目標税引後手取り",
        min_value=0,
        value=int(st.session_state.auto_sell_input_target_net_cash),
        step=100_000,
        key="auto_sell_input_target_net_cash",
    )
    input_tax_rate_percent = c2.number_input(
        "税率（%）",
        min_value=0.0,
        max_value=50.0,
        value=float(st.session_state.auto_sell_input_tax_rate_percent),
        step=0.001,
        key="auto_sell_input_tax_rate_percent",
    )
    input_shipping_ratio = c3.slider(
        "海運株の最大売却比率",
        min_value=0,
        max_value=100,
        value=int(st.session_state.auto_sell_input_shipping_ratio),
        step=10,
        key="auto_sell_input_shipping_ratio",
    )

    input_preserve_names = st.multiselect(
        "売却から除外する銘柄",
        options=sellable_names,
        default=st.session_state.auto_sell_input_preserve_names,
        key="auto_sell_input_preserve_names",
    )

    input_preserve_core_policy = st.checkbox(
        "policy=コア を売却対象から除外",
        value=bool(st.session_state.auto_sell_input_preserve_core_policy),
        key="auto_sell_input_preserve_core_policy",
    )

    submitted = st.form_submit_button("この条件で売却案を更新", type="primary")

if submitted:
    st.session_state.auto_sell_active_config = {
        "target_net_cash": int(input_target_net_cash),
        "tax_rate_percent": float(input_tax_rate_percent),
        "shipping_ratio": int(input_shipping_ratio),
        "preserve_names": normalize_names(input_preserve_names),
        "preserve_core_policy": bool(input_preserve_core_policy),
    }
    st.session_state.auto_sell_run_id += 1
    st.toast("売却案を更新しました。", icon="✅")

if st.button("条件を初期値に戻す", key="auto_sell_reset_conditions"):
    st.session_state.auto_sell_active_config = DEFAULT_CONFIG.copy()
    st.session_state.auto_sell_input_target_net_cash = DEFAULT_CONFIG["target_net_cash"]
    st.session_state.auto_sell_input_tax_rate_percent = DEFAULT_CONFIG["tax_rate_percent"]
    st.session_state.auto_sell_input_shipping_ratio = DEFAULT_CONFIG["shipping_ratio"]
    st.session_state.auto_sell_input_preserve_names = DEFAULT_CONFIG["preserve_names"]
    st.session_state.auto_sell_input_preserve_core_policy = DEFAULT_CONFIG["preserve_core_policy"]
    st.session_state.auto_sell_run_id += 1
    st.rerun()

config = st.session_state.auto_sell_active_config
excluded_set = set(normalize_names(config["preserve_names"]))
fingerprint = config_fingerprint(config)

st.success(
    "反映中の条件 | "
    f"更新ID: {st.session_state.auto_sell_run_id} | "
    f"条件ID: {fingerprint} | "
    f"除外銘柄: {('、'.join(sorted(excluded_set)) if excluded_set else 'なし')}"
)

st.caption(
    "注意: 除外銘柄を変更した後は、必ず「この条件で売却案を更新」を押してください。"
)

generator = AutoSellPlanGenerator()
scenarios = generator.generate(
    assets=assets,
    target_net_cash=float(config["target_net_cash"]),
    tax_rate=float(config["tax_rate_percent"]) / 100,
    preserve_names=list(excluded_set),
    preserve_core_policy=bool(config["preserve_core_policy"]),
    shipping_max_sell_ratio=float(config["shipping_ratio"]) / 100,
)

if not scenarios:
    st.warning("条件に合う売却案を作成できませんでした。除外銘柄や海運株の売却比率を見直してください。")
    st.stop()

violations = []

for scenario in scenarios:
    if not scenario.result.details.empty:
        sold_names = set(scenario.result.details["name"].dropna().astype(str).str.strip())
        violations.extend(sorted(sold_names & excluded_set))

if violations:
    st.error(
        "除外銘柄が売却案に含まれています。再生成ロジックに問題があります: "
        + "、".join(sorted(set(violations)))
    )
    st.stop()

achieved_scenarios = [s.name for s in scenarios if s.result.net_proceeds >= float(config["target_net_cash"])]
if achieved_scenarios:
    st.success("目標達成案があります: " + "、".join(achieved_scenarios))
else:
    st.warning(
        "現在の除外条件では、目標税引後手取りに届く案がありません。"
        " 除外銘柄を減らす、policy=コア除外をOFFにする、または目標額を下げてください。"
    )

st.markdown("---")
st.subheader("自動生成された売却案")

summary_rows = []
for scenario in scenarios:
    r = scenario.result
    sold_names = []
    if not r.details.empty:
        sold_names = r.details["name"].dropna().astype(str).str.strip().tolist()

    summary_rows.append(
        {
            "scenario": scenario.name,
            "net_proceeds": r.net_proceeds,
            "surplus_shortfall": r.surplus_shortfall,
            "tax": r.tax,
            "dividend_loss": r.dividend_loss,
            "sold_names": "、".join(sold_names),
            "condition_id": fingerprint,
            "achieved": r.net_proceeds >= float(config["target_net_cash"]),
        }
    )

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, width="stretch", hide_index=True)

tabs = st.tabs([s.name for s in scenarios])

for tab, scenario in zip(tabs, scenarios):
    with tab:
        st.markdown(f"### {scenario.name}")
        st.caption(scenario.description)

        r = scenario.result

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("売却代金", yen(r.gross_proceeds))
        m2.metric("税引後手取り", yen(r.net_proceeds))
        m3.metric("目標との差額", yen(r.surplus_shortfall))
        m4.metric("年間配当減少", yen(r.dividend_loss))

        m5, m6, m7 = st.columns(3)
        m5.metric("譲渡損益", yen(r.realized_gain_loss))
        m6.metric("税額", yen(r.tax))
        m7.metric("課税対象利益", yen(r.taxable_gain))

        if r.surplus_shortfall >= 0:
            st.success("目標手取り額を達成しています。")
        else:
            st.warning(f"目標まで {yen(abs(r.surplus_shortfall))} 不足しています。")

        if not r.details.empty:
            details = r.details.copy()
            details["condition_id"] = fingerprint
            st.dataframe(details, width="stretch", hide_index=True)

            chart_df = details.sort_values("gross_proceeds", ascending=True)
            fig = px.bar(
                chart_df,
                x="gross_proceeds",
                y="name",
                orientation="h",
                title=f"{scenario.name}: 売却代金内訳",
            )
            st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.subheader("候補一覧")

candidate_view = assets[
    (assets["asset_type"].isin(["stock", "fund"]))
    & (assets["quantity"] > 0)
].copy()

candidate_view["name_norm"] = candidate_view["name"].astype(str).str.strip()
candidate_view["excluded"] = candidate_view["name_norm"].isin(excluded_set)
candidate_view = candidate_view.sort_values(["excluded", "policy", "name"], ascending=[False, True, True])

st.dataframe(
    candidate_view[
        [
            "name",
            "asset_type",
            "sector",
            "quantity",
            "current_price",
            "value",
            "annual_dividend",
            "policy",
            "excluded",
        ]
    ],
    width="stretch",
    hide_index=True,
)

st.info(
    "この機能はルールベースのシナリオ生成です。実際の売却判断では、約定価格、手数料、税制、NISA区分、翌年以降の損失繰越、配当権利日などを確認してください。"
)
