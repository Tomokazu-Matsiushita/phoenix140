from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from services.integrated_ai_cfo_service import IntegratedCFOInput
from services.real_estate import AcquisitionInput, ExitIRRInput


class ScenarioAssumptionsService:
    def __init__(self, config_path: str | Path = "config/scenario_assumptions.json") -> None:
        self.config_path = Path(config_path)

    def default_assumptions(self) -> dict[str, Any]:
        return {
            "version": "1.0",
            "scenario_name": "Base Case",
            "saved_at": None,
            "memo": {
                "title": "Phoenix 140 Investment Decision Memo",
                "author": "Phoenix AI CFO",
                "purpose": "株式売却による資金確保と不動産取得の可否を総合判断する。",
            },
            "safety": {
                "current_cash": 4_856_312,
                "monthly_living_expense": 700_000,
                "emergency_months": 6.0,
                "property_repair_reserve": 1_500_000,
                "tax_reserve": 500_000,
                "other_commitments": 0,
                "minimum_cash_floor": 2_000_000,
            },
            "sale": {
                "target_net_cash": 3_500_000,
                "tax_rate_percent": 20.315,
                "preserve_names": ["三菱商事", "三井住友FG", "武田薬品", "JT"],
                "preserve_core_policy": True,
                "shipping_max_sell_ratio": 0.5,
            },
            "acquisition": {
                "property_name": "oblige新田町",
                "purchase_price": 76_000_000,
                "loan_amount": 76_000_000,
                "annual_interest_rate": 3.0,
                "loan_years": 34.0,
                "acquisition_cost_rate": 7.0,
                "units": 12,
                "monthly_full_rent": 665_000,
                "vacancy_rate": 8.33,
                "fixed_asset_tax_annual": 618_429,
                "management_fee_monthly": 59_300,
                "repair_reserve_monthly": 30_000,
            },
            "exit": {
                "holding_years": 10,
                "exit_price": 76_000_000,
                "annual_cash_flow": 2_475_987,
                "initial_cash_required": 5_320_000,
                "selling_cost_rate": 4.0,
                "annual_depreciation": 0,
                "capital_gain_tax_rate": 20.315,
            },
        }

    def load(self) -> dict[str, Any]:
        defaults = self.default_assumptions()

        if not self.config_path.exists():
            self.save(defaults)
            return defaults

        try:
            loaded = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return defaults

        return self._deep_merge(defaults, loaded)

    def save(self, assumptions: dict[str, Any]) -> dict[str, Any]:
        merged = self._deep_merge(self.default_assumptions(), assumptions)
        merged["saved_at"] = datetime.now().isoformat(timespec="seconds")

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return merged

    def reset(self) -> dict[str, Any]:
        defaults = self.default_assumptions()
        return self.save(defaults)

    def to_acquisition_input(self, assumptions: dict[str, Any] | None = None) -> AcquisitionInput:
        a = (assumptions or self.load()).get("acquisition", {})

        return AcquisitionInput(
            property_name=str(a.get("property_name", "oblige新田町")),
            purchase_price=float(a.get("purchase_price", 76_000_000)),
            loan_amount=float(a.get("loan_amount", 76_000_000)),
            annual_interest_rate=float(a.get("annual_interest_rate", 3.0)),
            loan_years=float(a.get("loan_years", 34.0)),
            acquisition_cost_rate=float(a.get("acquisition_cost_rate", 7.0)),
            units=int(a.get("units", 12)),
            monthly_full_rent=float(a.get("monthly_full_rent", 665_000)),
            vacancy_rate=float(a.get("vacancy_rate", 8.33)),
            fixed_asset_tax_annual=float(a.get("fixed_asset_tax_annual", 618_429)),
            management_fee_monthly=float(a.get("management_fee_monthly", 59_300)),
            repair_reserve_monthly=float(a.get("repair_reserve_monthly", 30_000)),
        )

    def to_exit_input(self, assumptions: dict[str, Any] | None = None) -> ExitIRRInput:
        data = assumptions or self.load()
        a = data.get("acquisition", {})
        e = data.get("exit", {})

        return ExitIRRInput(
            property_name=str(a.get("property_name", "oblige新田町")),
            purchase_price=float(a.get("purchase_price", 76_000_000)),
            loan_amount=float(a.get("loan_amount", 76_000_000)),
            annual_interest_rate=float(a.get("annual_interest_rate", 3.0)),
            loan_years=float(a.get("loan_years", 34.0)),
            initial_cash_required=float(e.get("initial_cash_required", 5_320_000)),
            annual_cash_flow=float(e.get("annual_cash_flow", 2_475_987)),
            holding_years=int(e.get("holding_years", 10)),
            exit_price=float(e.get("exit_price", 76_000_000)),
            selling_cost_rate=float(e.get("selling_cost_rate", 4.0)),
            annual_depreciation=float(e.get("annual_depreciation", 0)),
            capital_gain_tax_rate=float(e.get("capital_gain_tax_rate", 20.315)),
        )

    def to_integrated_input(self, assumptions: dict[str, Any] | None = None) -> IntegratedCFOInput:
        data = assumptions or self.load()
        safety = data.get("safety", {})
        sale = data.get("sale", {})

        return IntegratedCFOInput(
            current_cash=float(safety.get("current_cash", 4_856_312)),
            monthly_living_expense=float(safety.get("monthly_living_expense", 700_000)),
            emergency_months=float(safety.get("emergency_months", 6.0)),
            property_repair_reserve=float(safety.get("property_repair_reserve", 1_500_000)),
            tax_reserve=float(safety.get("tax_reserve", 500_000)),
            other_commitments=float(safety.get("other_commitments", 0)),
            minimum_cash_floor=float(safety.get("minimum_cash_floor", 2_000_000)),
            target_net_cash=float(sale.get("target_net_cash", 3_500_000)),
            tax_rate=float(sale.get("tax_rate_percent", 20.315)) / 100,
            preserve_names=list(sale.get("preserve_names", [])),
            preserve_core_policy=bool(sale.get("preserve_core_policy", True)),
            shipping_max_sell_ratio=float(sale.get("shipping_max_sell_ratio", 0.5)),
            acquisition_input=self.to_acquisition_input(data),
            exit_input=self.to_exit_input(data),
        )

    def summary_rows(self, assumptions: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        data = assumptions or self.load()
        rows: list[dict[str, Any]] = []

        for section in ["safety", "sale", "acquisition", "exit", "memo"]:
            for key, value in data.get(section, {}).items():
                rows.append(
                    {
                        "section": section,
                        "key": key,
                        "value": ", ".join(value) if isinstance(value, list) else value,
                    }
                )

        return rows

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(base)

        for key, value in (override or {}).items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
