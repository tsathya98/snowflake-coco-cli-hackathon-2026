---
doc_id: RB-005
title: Duplicate exception suppression
category: operations
revision: 2
effective: 2025-06-30
owner: Operations Excellence
---

# RB-005 — Duplicate exception suppression

## 1. Uniqueness rule

Only one open exception should exist per metric and entity pair.

If a new detection matches an existing open exception, append evidence to the existing record
rather than creating a second one.

## 2. Rationale

Repeated notification for an unchanged condition is the fastest way to lose an operator's
attention. An exception queue that cries wolf is functionally the same as no queue at all.

## 3. Reasoning is also subject to this rule

An exception that has already been investigated should not be investigated again on the next
pass. Re-reasoning produces a second recommendation for the same condition and, where the first
recommendation was already routed to a human, risks re-queueing an action that person has just
rejected.

## 4. Implementation note

A uniqueness constraint declared on a table is documentation unless the platform enforces it.
Where it does not, the merge predicate that writes the exception is the actual control, and it is
the thing to review.
