# Implementation Plan: Neo Brutalism Skew

**Branch**: `033-neo-brutalist-skew` | **Date**: 2026-07-10
**Spec**: [specs/033-neo-brutalist-skew/spec.md](specs/033-neo-brutalist-skew/spec.md)

## Goal

Apply Neo-Brutalist tilt (`transform: rotate()`) to headers and buttons globally via `static/style.css`.

## Task Breakdown

| ID | Task | Deps | Status |
|---|---|---|---|
| 1.1 | [style.css] Inject `-1deg` rotation on `h1`, `h2`, `h3` | None | Completed |
| 1.2 | [style.css] Inject `-1deg` rotation on primary buttons | None | Completed |
| 1.3 | [style.css] Inject `1deg` rotation on secondary buttons | None | Completed |
