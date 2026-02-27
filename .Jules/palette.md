## 2026-03-01 - [Added Progress Bar for Ingestion]
**Learning:** Users lack visibility into the overall progress of batch operations when only individual item statuses are shown.
**Action:** Added a `ProgressBar` widget to the main action bar. It initializes with the total count of selected tracks and advances as each track reaches a terminal state (COMPLETE, FAILED, NO MATCH). This provides immediate visual feedback on the mission's overall completion status.
**Technical Insight:** When adding UI components to a Textual app, ensuring  layouts are updated to  or  containers is crucial for proper rendering.
**Correction:** Initially missed adding  to , which would have caused stacking issues.
**Technical Insight:** When adding UI components to a Textual app, ensuring `CSS` layouts are updated to `horizontal` or `vertical` containers is crucial for proper rendering.
**Correction:** Initially missed adding `layout: horizontal` to `#action-bar`, which would have caused stacking issues.
