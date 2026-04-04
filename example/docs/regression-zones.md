# Regression Risk Zones

<!-- List areas with complex cross-dependencies. Read before modifying. -->

These areas have complex cross-dependencies. **Read this file before modifying any of them.**

## [Zone 1: e.g. Pricing]

- **Path**: `src/...`
- **Risk**: [describe what can break — e.g. rounding issues, frontend/backend coherence]
- **Dependencies**: [what other areas are affected]

## [Zone 2: e.g. Auth]

- **Path**: `src/...`
- **Risk**: [e.g. token invalidation propagation, session handling]
- **Dependencies**: [middleware, guards, refresh flow]

## [Zone 3: e.g. Checkout]

- **Path**: `src/...`
- **Risk**: [e.g. multi-step flow, partial failure handling]
- **Dependencies**: [orders, payments, notifications]
