---
doc_id: RB-002
title: Projected stockout response
category: inventory
revision: 5
effective: 2026-02-20
owner: Supply Planning
---

# RB-002 — Projected stockout response

## 1. Risk criteria

A SKU is at stockout risk when on-hand falls below safety stock and days-of-cover is under
fourteen.

Both conditions must hold. A SKU below safety stock with ample cover is a policy question for
planning, not an operational exception.

## 2. Standard response

The standard response is to raise a replenishment request against the primary supplier at the
standard lead time.

Only escalate to expedited freight where cover is under seven days.

## 3. Duplicate suppression

Always check for in-transit quantity before raising a new request. Duplicate replenishment is
the most common error in this workflow, and an in-transit quantity sufficient to restore cover
means no new request is warranted.

## 4. Single-sourced materials

Where the SKU is single-sourced, notify planning even if cover is adequate, because recovery
time is longer.

## 5. Authority

Inventory positions are internal records. A replenishment request commits spend and a delivery
slot, so automation may prepare and recommend the request but a human must release it. This is
not a statement about confidence in the recommendation; it is a statement about who owns the
commitment.
