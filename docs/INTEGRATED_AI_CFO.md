# Sprint 4.2 Integrated AI CFO Final Recommendation

## Purpose

Sprint 4.2 adds the final integrated Phoenix CFO recommendation layer.

It combines:

- stock sale plan
- after-tax proceeds
- dividend loss
- property acquisition CF
- liquidity safety buffer
- DSCR
- exit IRR

## New Page

```text
Integrated AI CFO Final Recommendation
```

## Decision Labels

- 実行候補
- 条件付き実行
- 待つ
- 見送り
- 要データ確認

## Decision Factors

The final decision checks:

- whether sale proceeds fund acquisition
- whether safety buffer remains
- whether annual CF improves
- whether acquisition DSCR is acceptable
- whether exit IRR is acceptable

## Current Design

This version is rule-based and does not call external AI APIs.

## Future Enhancements

- connect Moneytree actual balances
- tax-aware final recommendation
- scenario memory
- monthly CFO report
- OpenAI API commentary
- one-click PDF investment memo
