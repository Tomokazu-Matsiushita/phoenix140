# Scenario Assumptions Trace

## Purpose

This patch makes the data flow visible on the Integrated AI CFO page.

## Flow

```text
config/scenario_assumptions.json
  ↓
ScenarioAssumptionsService.load()
  ↓
components/scenario_sidebar.render_integrated_scenario_sidebar()
  ↓
IntegratedCFOInput
  ↓
IntegratedAICFOService.review()
  ↓
Final Recommendation
```

## Added to Integrated AI CFO

- Current assumptions table
- Source display
- Last saved timestamp
- Calculation trace
- Explanation of which parameters affect which decision factors

## Rule

Scenario Assumptions Center provides saved defaults.
The Integrated AI CFO sidebar can temporarily override them.
Press "このページの条件をCenterに保存" to persist those temporary values.
