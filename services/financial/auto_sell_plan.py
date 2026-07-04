from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from services.financial.sell_simulator import SellSimulator, SellSimulationResult


@dataclass
class AutoSellScenario:
    name: str
    description: str
    plan: list[dict[str, Any]]
    result: SellSimulationResult


class AutoSellPlanGenerator:
    # Rule-based generator for sell plan candidates.
    #
    # This is not investment advice. It is a scenario generator for decision support.
    # The future AI CFO layer can call this generator and explain the results.

    CORE_DEFAULTS = ["三菱商事", "三井住友FG", "武田薬品", "JT"]
    SHIPPING_NAMES = ["日本郵船", "商船三井"]

    POLICY_RANK = {
        "損益通算候補": 0,
        "整理候補": 1,
        "調整": 2,
        "準コア": 4,
        "コア": 99,
    }

    def __init__(self, simulator: SellSimulator | None = None) -> None:
        self.simulator = simulator or SellSimulator()

    @staticmethod
    def _normalize_name(value: Any) -> str:
        return str(value).strip()

    def generate(
        self,
        assets: pd.DataFrame,
        target_net_cash: float = 3_500_000,
        tax_rate: float = 0.20315,
        preserve_names: list[str] | None = None,
        preserve_core_policy: bool = True,
        shipping_max_sell_ratio: float = 0.5,
        lot_size: float = 100.0,
    ) -> list[AutoSellScenario]:
        if assets.empty:
            return []

        # None means use default core exclusions.
        # [] means the user intentionally excludes nothing.
        if preserve_names is None:
            preserve_names = self.CORE_DEFAULTS.copy()

        preserve_set = {self._normalize_name(x) for x in preserve_names}

        scenarios: list[AutoSellScenario] = []

        base_candidates = self._build_candidate_units(
            assets=assets,
            preserve_set=preserve_set,
            preserve_core_policy=preserve_core_policy,
            shipping_max_sell_ratio=shipping_max_sell_ratio,
            lot_size=lot_size,
        )

        if not base_candidates.empty:
            base_candidates = base_candidates[~base_candidates["name_norm"].isin(preserve_set)].copy()

        scenario_defs = [
            (
                "税効率優先",
                "含み損・低税負担を優先し、税引後手取りを作る案です。海運株は画面で指定した最大売却比率を守ります。",
                ["policy_rank", "unit_gain_loss", "dividend_loss_per_cash"],
                [True, True, True],
                base_candidates,
            ),
            (
                "配当維持優先",
                "年間配当の減少をできるだけ抑えながら手取りを作る案です。海運株は画面で指定した最大売却比率を守ります。",
                ["dividend_loss_per_cash", "policy_rank", "unit_gain_loss"],
                [True, True, True],
                base_candidates,
            ),
            (
                "バランス型",
                "コア資産を守りつつ、税効率・配当維持・売却しやすさのバランスを取る案です。海運株は画面で指定した最大売却比率を守ります。",
                ["balanced_score", "policy_rank", "dividend_loss_per_cash"],
                [True, True, True],
                base_candidates,
            ),
        ]

        for name, description, sort_cols, ascending, candidates in scenario_defs:
            if candidates.empty:
                plan = []
                result = self.simulator.simulate(
                    assets=assets,
                    sale_plan=plan,
                    tax_rate=tax_rate,
                    target_net_cash=target_net_cash,
                )
            else:
                sorted_candidates = candidates.sort_values(sort_cols, ascending=ascending)
                plan = self._greedy_plan(
                    assets=assets,
                    candidate_units=sorted_candidates,
                    target_net_cash=target_net_cash,
                    tax_rate=tax_rate,
                    preserve_set=preserve_set,
                )
                result = self.simulator.simulate(
                    assets=assets,
                    sale_plan=plan,
                    tax_rate=tax_rate,
                    target_net_cash=target_net_cash,
                )

            scenarios.append(AutoSellScenario(name=name, description=description, plan=plan, result=result))

        # Target achievement scenario:
        # If normal constraints cannot reach target, this scenario relaxes only the shipping ratio to 100%.
        # Explicit excluded names and policy=core exclusion are still respected.
        target_candidates = self._build_candidate_units(
            assets=assets,
            preserve_set=preserve_set,
            preserve_core_policy=preserve_core_policy,
            shipping_max_sell_ratio=1.0,
            lot_size=lot_size,
        )

        if not target_candidates.empty:
            target_candidates = target_candidates[~target_candidates["name_norm"].isin(preserve_set)].copy()

            target_sorted = target_candidates.sort_values(
                ["policy_rank", "unit_gain_loss", "dividend_loss_per_cash", "unit_gross"],
                ascending=[True, True, True, True],
            )

            target_plan = self._greedy_plan(
                assets=assets,
                candidate_units=target_sorted,
                target_net_cash=target_net_cash,
                tax_rate=tax_rate,
                preserve_set=preserve_set,
            )
        else:
            target_plan = []

        target_result = self.simulator.simulate(
            assets=assets,
            sale_plan=target_plan,
            tax_rate=tax_rate,
            target_net_cash=target_net_cash,
        )

        scenarios.append(
            AutoSellScenario(
                name="目標達成優先",
                description=(
                    "目標手取り額の達成を優先する案です。明示的に除外した銘柄とpolicy=コア除外設定は守り、"
                    "海運株の最大売却比率だけ100%まで緩和して計算します。"
                ),
                plan=target_plan,
                result=target_result,
            )
        )

        return scenarios

    def _build_candidate_units(
        self,
        assets: pd.DataFrame,
        preserve_set: set[str],
        preserve_core_policy: bool,
        shipping_max_sell_ratio: float,
        lot_size: float,
    ) -> pd.DataFrame:
        sellable = assets.copy()

        required_cols = [
            "name",
            "asset_type",
            "quantity",
            "current_price",
            "cost_price",
            "annual_dividend",
            "policy",
            "value",
        ]
        for col in required_cols:
            if col not in sellable.columns:
                sellable[col] = 0

        sellable["name_norm"] = sellable["name"].map(self._normalize_name)

        for col in ["quantity", "current_price", "cost_price", "annual_dividend", "value"]:
            sellable[col] = pd.to_numeric(sellable[col], errors="coerce").fillna(0)

        sellable = sellable[
            (sellable["quantity"] > 0)
            & (sellable["current_price"] > 0)
            & (sellable["cost_price"] >= 0)
            & (sellable["asset_type"].isin(["stock", "fund"]))
        ].copy()

        if preserve_set:
            sellable = sellable[~sellable["name_norm"].isin(preserve_set)].copy()

        if preserve_core_policy:
            sellable = sellable[~sellable["policy"].eq("コア")].copy()

        rows = []

        for _, row in sellable.iterrows():
            name = row["name"]
            name_norm = row["name_norm"]
            quantity = float(row["quantity"] or 0)
            current_price = float(row["current_price"] or 0)
            cost_price = float(row["cost_price"] or 0)
            annual_dividend = float(row["annual_dividend"] or 0)
            policy = row.get("policy", "")
            asset_type = row.get("asset_type", "")

            if quantity <= 0 or current_price <= 0:
                continue

            if asset_type == "fund" or quantity <= lot_size:
                step = quantity
            else:
                step = lot_size

            max_qty = quantity

            if name in self.SHIPPING_NAMES:
                shipping_max_sell_ratio = max(0.0, min(float(shipping_max_sell_ratio), 1.0))
                max_qty = quantity * shipping_max_sell_ratio

            if max_qty <= 0 or step <= 0:
                continue

            if max_qty < step:
                # Respect the ratio. For Japanese stocks, if the allowed amount is less than one trading unit,
                # no unit is generated.
                continue

            steps = int(max_qty // step)

            unit_dividend_loss = annual_dividend * (step / quantity) if quantity else 0
            unit_gross = step * current_price
            unit_cost = step * cost_price
            unit_gain_loss = unit_gross - unit_cost

            for i in range(steps):
                rows.append(
                    {
                        "name": name,
                        "name_norm": name_norm,
                        "unit_index": i + 1,
                        "unit_quantity": step,
                        "unit_gross": unit_gross,
                        "unit_cost": unit_cost,
                        "unit_gain_loss": unit_gain_loss,
                        "unit_dividend_loss": unit_dividend_loss,
                        "dividend_loss_per_cash": unit_dividend_loss / unit_gross if unit_gross else 999,
                        "policy": policy,
                        "policy_rank": self.POLICY_RANK.get(policy, 3),
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Lower is better.
        df["balanced_score"] = (
            df["policy_rank"] * 1000
            + df["dividend_loss_per_cash"] * 100000
            + df["unit_gain_loss"].clip(lower=-1_000_000, upper=1_000_000) / 10000
        )

        return df

    def _greedy_plan(
        self,
        assets: pd.DataFrame,
        candidate_units: pd.DataFrame,
        target_net_cash: float,
        tax_rate: float,
        preserve_set: set[str],
    ) -> list[dict[str, Any]]:
        plan_qty: dict[str, float] = {}

        for _, unit in candidate_units.iterrows():
            name = unit["name"]
            name_norm = self._normalize_name(name)

            # Final guard: excluded names must never enter the plan.
            if name_norm in preserve_set:
                continue

            plan_qty[name] = plan_qty.get(name, 0.0) + float(unit["unit_quantity"])

            plan = [{"name": n, "sell_quantity": q} for n, q in plan_qty.items()]
            result = self.simulator.simulate(
                assets=assets,
                sale_plan=plan,
                tax_rate=tax_rate,
                target_net_cash=target_net_cash,
            )

            if result.net_proceeds >= target_net_cash:
                return plan

        return [{"name": n, "sell_quantity": q} for n, q in plan_qty.items()]
