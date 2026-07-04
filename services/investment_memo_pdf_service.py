from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class InvestmentMemoPDFService:
    def __init__(self) -> None:
        self.font_regular = "HeiseiKakuGo-W5"
        self.font_bold = "HeiseiKakuGo-W5"
        self._register_fonts()

    def _register_fonts(self) -> None:
        for font_name in ["HeiseiKakuGo-W5", "HeiseiMin-W3"]:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont(font_name))
            except Exception:
                pass

    def build_pdf_bytes(self, memo: dict[str, Any]) -> bytes:
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=str(memo.get("title", "Phoenix 140 Investment Memo")),
            author=str(memo.get("author", "Phoenix AI CFO")),
        )

        styles = self._styles()
        story: list[Any] = []

        review = memo.get("review", {}) or {}
        decision = review.get("decision", {}) or {}
        best = review.get("best_scenario", {}) or {}
        exit_result = review.get("exit_result", {}) or {}
        liquidity_review = review.get("liquidity_review", {}) or {}
        allocation = liquidity_review.get("allocation", {}) or {}
        acquisition = allocation.get("acquisition", {}) or {}

        story.append(Paragraph(str(memo.get("title", "Phoenix 140 Investment Memo")), styles["TitleJ"]))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(f"作成日: {self._text(memo.get('memo_date'))}", styles["Small"]))
        story.append(Paragraph(f"作成者: {self._text(memo.get('author'))}", styles["Small"]))
        story.append(Paragraph(f"目的: {self._text(memo.get('purpose'))}", styles["Small"]))
        story.append(Spacer(1, 8 * mm))

        story.append(Paragraph("1. Final Recommendation", styles["HeadingJ"]))
        story.append(self._key_value_table([
            ("判断", decision.get("label", "-")),
            ("スコア", self._fmt_num(decision.get("score"))),
            ("結論", decision.get("headline", "-")),
        ], styles))
        story.append(Paragraph(self._text(review.get("executive_summary", "-")), styles["BodyJ"]))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("2. Best Scenario Snapshot", styles["HeadingJ"]))
        story.append(self._key_value_table([
            ("最有力シナリオ", best.get("scenario", "-")),
            ("売却銘柄", best.get("sold_names", "-")),
            ("税引後売却資金", self._yen(best.get("net_proceeds"))),
            ("配当減少/年", self._yen(best.get("dividend_loss"))),
            ("取得初期必要資金", self._yen(best.get("initial_cash_required"))),
            ("取得後現金", self._yen(best.get("after_transaction_cash"))),
            ("安全資金差額", self._yen(best.get("safety_surplus"))),
            ("年間CF差分", self._yen(best.get("annual_cf_delta"))),
            ("取得DSCR", self._fmt_x(best.get("acquisition_dscr"))),
            ("出口IRR", self._fmt_pct(exit_result.get("irr"))),
            ("出口総損益", self._yen(exit_result.get("total_profit"))),
        ], styles))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("3. Decision Factors", styles["HeadingJ"]))
        story.append(self._df_table(pd.DataFrame(review.get("decision_factors", [])), styles, max_rows=10))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("4. Acquisition Summary", styles["HeadingJ"]))
        story.append(self._key_value_table([
            ("物件名", acquisition.get("property_name", best.get("property_name", "-"))),
            ("購入価格", self._yen(acquisition.get("purchase_price"))),
            ("借入額", self._yen(acquisition.get("loan_amount"))),
            ("初期必要資金", self._yen(acquisition.get("initial_cash_required"))),
            ("月額返済", self._yen(acquisition.get("monthly_payment"))),
            ("返済後CF/年", self._yen(acquisition.get("cash_flow_after_debt"))),
            ("DSCR", self._fmt_x(acquisition.get("dscr"))),
            ("表面利回り", self._fmt_pct(acquisition.get("gross_yield_full"))),
            ("NOI利回り", self._fmt_pct(acquisition.get("noi_yield"))),
            ("損益分岐稼働率", self._fmt_pct(acquisition.get("break_even_occupancy"))),
            ("取得判定", acquisition.get("health", "-")),
        ], styles))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("5. Exit / IRR Summary", styles["HeadingJ"]))
        story.append(self._key_value_table([
            ("保有年数", exit_result.get("holding_years", "-")),
            ("売却価格", self._yen(exit_result.get("exit_price"))),
            ("売却時残債", self._yen(exit_result.get("remaining_loan_balance"))),
            ("売却後手残り", self._yen(exit_result.get("sale_cash_after_debt_tax"))),
            ("累積CF", self._yen(exit_result.get("cumulative_cash_flow"))),
            ("総回収額", self._yen(exit_result.get("total_recovery"))),
            ("総損益", self._yen(exit_result.get("total_profit"))),
            ("回収倍率", self._fmt_multiple(exit_result.get("equity_multiple"))),
            ("IRR", self._fmt_pct(exit_result.get("irr"))),
            ("出口判定", exit_result.get("health", "-")),
        ], styles))
        story.append(PageBreak())

        story.append(Paragraph("6. Liquidity & Safety", styles["HeadingJ"]))
        story.append(self._key_value_table([
            ("必要安全資金", self._yen(liquidity_review.get("required_buffer"))),
            ("現在の生活費月数", self._fmt_months(liquidity_review.get("current_months_covered"))),
        ], styles))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("7. Scenario Comparison", styles["HeadingJ"]))
        scenario_review = liquidity_review.get("scenario_review", pd.DataFrame())
        if isinstance(scenario_review, pd.DataFrame) and not scenario_review.empty:
            cols = [
                "scenario",
                "status",
                "net_proceeds",
                "after_transaction_cash",
                "safety_surplus",
                "annual_cf_delta",
                "liquidity_score",
            ]
            df = scenario_review[[c for c in cols if c in scenario_review.columns]].copy()
            story.append(self._df_table(df, styles, max_rows=8))
        else:
            story.append(Paragraph("シナリオ比較データがありません。", styles["BodyJ"]))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("8. Must Check Before Action", styles["HeadingJ"]))
        for item in review.get("must_check", []):
            story.append(Paragraph(f"- {self._text(item)}", styles["BodyJ"]))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("9. CFO Note", styles["HeadingJ"]))
        story.append(Paragraph(
            "この投資判断メモはPhoenix 140のルールベース計算に基づくドラフトです。"
            "実行前には、税務、融資承認、物件調査、修繕見積、火災保険、レントロール、"
            "売却時税金、生活資金を必ず別途確認してください。",
            styles["BodyJ"],
        ))

        doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        return buffer.getvalue()

    def _styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()

        return {
            "TitleJ": ParagraphStyle(
                "TitleJ",
                parent=base["Title"],
                fontName=self.font_bold,
                fontSize=18,
                leading=24,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
            "HeadingJ": ParagraphStyle(
                "HeadingJ",
                parent=base["Heading2"],
                fontName=self.font_bold,
                fontSize=12,
                leading=16,
                spaceBefore=8,
                spaceAfter=5,
            ),
            "BodyJ": ParagraphStyle(
                "BodyJ",
                parent=base["BodyText"],
                fontName=self.font_regular,
                fontSize=9,
                leading=13,
                alignment=TA_LEFT,
                spaceAfter=3,
            ),
            "Small": ParagraphStyle(
                "Small",
                parent=base["BodyText"],
                fontName=self.font_regular,
                fontSize=8,
                leading=11,
                alignment=TA_LEFT,
            ),
        }

    def _key_value_table(self, rows: list[tuple[Any, Any]], styles: dict[str, ParagraphStyle]) -> Table:
        data = [[Paragraph("項目", styles["Small"]), Paragraph("内容", styles["Small"])]]
        for key, value in rows:
            data.append([
                Paragraph(self._text(key), styles["Small"]),
                Paragraph(self._text(value), styles["Small"]),
            ])

        table = Table(data, colWidths=[46 * mm, 116 * mm], repeatRows=1)
        table.setStyle(self._table_style())
        return table

    def _df_table(self, df: pd.DataFrame, styles: dict[str, ParagraphStyle], max_rows: int = 10) -> Table:
        if df is None or df.empty:
            return self._key_value_table([("データ", "ありません")], styles)

        df = df.head(max_rows).copy()

        for col in df.columns:
            if col in {
                "net_proceeds",
                "dividend_loss",
                "initial_cash_required",
                "after_transaction_cash",
                "safety_surplus",
                "annual_cf_delta",
                "monthly_cf_delta",
                "tax",
            }:
                df[col] = df[col].map(self._yen)
            elif col in {"acquisition_dscr"}:
                df[col] = df[col].map(self._fmt_x)
            elif col in {"liquidity_score", "score"}:
                df[col] = df[col].map(self._fmt_num)

        data = [[Paragraph(self._text(c), styles["Small"]) for c in df.columns]]
        for _, row in df.iterrows():
            data.append([Paragraph(self._text(row[c]), styles["Small"]) for c in df.columns])

        usable_width = 170 * mm
        col_width = usable_width / max(len(df.columns), 1)
        table = Table(data, colWidths=[col_width] * len(df.columns), repeatRows=1)
        table.setStyle(self._table_style())
        return table

    def _table_style(self) -> TableStyle:
        return TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), self.font_regular),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDBDBD")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])

    def _footer(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont(self.font_regular, 8)
        canvas.drawRightString(195 * mm, 10 * mm, f"Phoenix 140 | page {doc.page}")
        canvas.restoreState()

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return "-"
        try:
            if pd.isna(value):
                return "-"
        except Exception:
            pass
        text = str(value)
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

    @staticmethod
    def _yen(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"¥{float(value):,.0f}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_pct(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2%}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_x(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2f}x"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_multiple(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2f}x"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_num(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.1f}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_months(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.1f}か月"
        except Exception:
            return "-"
