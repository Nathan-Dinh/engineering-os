# Phase 6: Data and interface discovery

If the product handles persistent data, invoke `simple-eng:database-engineering` before any final schema decision: entities, cardinality, ownership and tenancy, access patterns, consistency, privacy, retention, audit, migration, and recovery.

If the product has a user interface, invoke `simple-eng:ui-ux-design`: primary journeys, navigation, design consistency, responsive behavior, interaction states, and accessibility expectations.

If either does not apply, record `Not applicable: <reason>` in the matching area (`simple-eng status` lists `data-model` and `ui`), so it is not asked again.
