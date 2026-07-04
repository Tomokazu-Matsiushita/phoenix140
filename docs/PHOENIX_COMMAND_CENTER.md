# Sprint 5.1 Phoenix Command Center

## Purpose

Phoenix 140 started as a one-glance dashboard for:

- financial assets
- real estate
- health

As detailed simulators increased, the app needed a simpler top page again.

## New Page

```text
Phoenix Command Center
```

File:

```text
pages/00_Phoenix_Command_Center.py
```

## Role

The Command Center is the home dashboard.

It does not replace detailed pages.
It summarizes them.

## Sources

```text
Scenario Assumptions Center
  ↓
Integrated AI CFO
  ↓
Phoenix Command Center
```

```text
Moneytree Manual Import
  ↓
Moneytree Dashboard
  ↓
Phoenix Command Center
```

Health is prepared as a placeholder for future sprints.

## Design Principles

- one-glance overview
- immediate alerts
- no deep parameter editing
- links/guide to detailed pages
- simple traffic-light risk flags
- data flow trace visible

## Future Enhancements

- direct page navigation buttons
- automatic refresh status
- real Moneytree API sync status
- health data model
- net worth trend
- goal progress toward Phoenix 140
- daily AI brief
