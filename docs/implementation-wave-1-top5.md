# Implementation Wave 1 Top 5

This page replaces an inherited roadmap that assumed a different, pipeline-oriented
product. The priorities below are aligned to the stated goal of helping baseball players
and practitioners improve biomechanics.

## 1. Restore Verified Runtime Surfaces

Reintroduce the actual backend, frontend, tests, and deployment assets that correspond to
the intended biomechanics application.

## 2. Establish Core Domain Language

Create validated shared definitions for the core domain entities the product needs, such as:
- athlete
- session
- assessment
- comparison
- prescription
- report

## 3. Define The First End-To-End User Workflow

Pick one validated practitioner workflow and specify it fully. For example:
- capture or upload a session
- review the resulting assessment
- compare against baseline or prior sessions
- record practitioner guidance
- produce a shareable output

## 4. Rebuild Product Contracts From Code

Replace inherited placeholder contracts and historical specs with contracts derived from the
restored application code and real user workflows.

## 5. Add Trustworthy Quality Gates

Once runtime code exists, add the testing and release gates needed for a production
biomechanics product, including backend, frontend, accessibility, and end-to-end coverage.
