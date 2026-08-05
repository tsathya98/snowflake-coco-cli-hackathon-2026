---
doc_id: RB-001
title: Supplier on-time delivery degradation
category: supplier
revision: 7
effective: 2025-11-03
owner: Procurement Operations
---

# RB-001 — Supplier on-time delivery degradation

## 1. Detection threshold

When a supplier's rolling 14-day on-time rate falls more than 20 percentage points below its
90-day baseline, treat it as a performance exception rather than noise.

A detector implementing this clause should require a minimum recent sample before raising —
twenty deliveries in the recent window is the accepted floor. Below that, the rate is too
volatile to distinguish a real shift from ordinary variation.

## 2. Corroboration

The threshold above decides whether an exception exists. It does not establish that the supplier
is an outlier rather than one instance of a market-wide move.

Where a statistical test is used alongside the threshold, it must be robust to the very outlier
being investigated. Use the median and median absolute deviation across the supplier population,
not the mean and standard deviation — an outlier inflates the standard deviation it is then
measured against, which suppresses exactly the signal being sought.

## 3. Confirmation before action

First confirm the drop is not explained by a single bulk order or a site closure. Then open a
supplier performance review task and notify the category buyer.

Do not re-source on a single fortnight of data.

## 4. Escalation by supplier tier

For strategic-tier suppliers, escalate to the commercial owner before any contractual action.
Standard-tier suppliers may proceed through the routine review path.

## 5. Interaction with freight cost

Expedite fees are only justified where the affected SKU has fewer than ten days of cover. A
supplier performance exception is not on its own a reason to expedite.
