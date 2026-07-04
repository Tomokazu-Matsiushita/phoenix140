# Sprint 2.5 AI CFO Commentary

## Purpose

Sprint 2.5 adds rule-based Phoenix AI CFO commentary to the Auto Sell Planner.

The goal is to explain:
- which scenario is recommended
- whether the target net cash is achieved
- why a scenario is attractive
- tax impact
- dividend impact
- operational caution points

## Current Version

This version is rule-based.

It does not call an external AI API.

## Recommendation Logic

Achieved scenarios are preferred.

Among achieved scenarios, the service prefers:
- lower annual dividend loss
- lower tax
- smaller excess sale amount
- fewer sale positions

If no scenario achieves the target, the service explains the shortfall.

## Future

Later versions can connect to:
- OpenAI API
- Moneytree
- full tax model
- real estate cash requirement
- monthly CFO report
