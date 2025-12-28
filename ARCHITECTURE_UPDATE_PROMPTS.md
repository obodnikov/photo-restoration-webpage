# Architecture Update Prompts

**Purpose:** Ready-to-use prompts for updating ARCHITECTURE.md when the project evolves

---

## Table of Contents

1. [General Update Prompt](#general-update-prompt)
2. [Scenario-Specific Prompts](#scenario-specific-prompts)
3. [Validation After Update](#validation-after-update)
4. [Common Update Patterns](#common-update-patterns)

---

## General Update Prompt

### Standard Update Template

```
The project architecture has changed. I need to update ARCHITECTURE.md to reflect these changes.

Changes made:
[DESCRIBE CHANGES IN DETAIL]

Files affected:
[LIST MODIFIED/ADDED/REMOVED FILES]

Impact:
[DESCRIBE WHAT CHANGED: new component, moved stability zone, new integration, etc.]

––––––––––––––––––––
YOUR TASK:

1. Read the current ARCHITECTURE.md
2. Identify which sections need updates based on the changes above
3. Update ONLY the affected sections
4. Preserve the 9-section structure
5. Keep total length under 300 lines (may need to compress other sections)
6. Update "Last Updated" date at the top
7. If stability zones changed, update Section 7
8. If new AI rules added, update Section 8

––––––––––––––––––––
GUIDELINES:

- Be surgical: update only what changed
- Maintain existing style and formatting
- Use same emoji markers (✅🔄⚠️🔮)
- Keep ASCII diagrams consistent
- Preserve line budget for each section
- If a section grows, compress another section

––––––––––––––––––––
OUTPUT:

Provide the updated sections with clear markers:
- "Section [N]: [TITLE] - UPDATED"
- Show the new content
- Explain what changed and why
```

---

## Scenario-Specific Prompts

### 1. New Feature Added

```
SCENARIO: New Feature Added

Feature: [FEATURE NAME]
Location: [PATH TO NEW CODE]
Stability: [✅ Stable / 🔄 Semi-Stable / ⚠️ Experimental]

Context:
- [What does this feature do?]
- [Which components does it touch?]
- [Is it user-facing or internal?]

Update ARCHITECTURE.md:

1. Section 3 (Repository Structure)
   - Add new directories if created
   - Update directory tree

2. Section 4 (Core Components)
   - Add new component description if it's a major subsystem
   - Update relevant subsection (4.1, 4.2, 4.3, or 4.4)

3. Section 5 (Data Flow)
   - Add new data flow diagram if it's a critical flow
   - Update existing flow if modified

4. Section 7 (Stability Zones)
   - Add new feature to appropriate stability zone
   - Use [EMOJI] marker

5. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: New Feature Added

Feature: Real-time WebSocket Notifications
Location: backend/app/services/websocket.py, frontend/src/features/notifications/
Stability: ⚠️ Experimental (new, may change API)

Context:
- Real-time push notifications for restoration completion
- Backend WebSocket server + Frontend WebSocket client
- User-facing feature

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 2. Component Moved to Different Stability Zone

```
SCENARIO: Component Stability Changed

Component: [COMPONENT NAME]
Path: [FILE PATH]
Previous Stability: [OLD EMOJI] [OLD ZONE]
New Stability: [NEW EMOJI] [NEW ZONE]

Reason for change:
[Why did stability change? Production tested? Deprecated? Refactored?]

Update ARCHITECTURE.md:

1. Section 7 (Stability Zones)
   - Move component from [OLD ZONE] to [NEW ZONE]
   - Add brief note about why it moved
   - Update emoji marker

2. Section 4 (Core Components)
   - Update component description if responsibilities changed

3. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: Component Stability Changed

Component: AI Provider System
Path: backend/app/services/huggingface.py, backend/app/services/replicate.py
Previous Stability: 🔄 Semi-Stable
New Stability: ✅ Stable

Reason for change:
- 6 months in production without issues
- Well-tested (100% coverage)
- API stable, no breaking changes planned

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 3. Major Architectural Decision

```
SCENARIO: Major Architectural Decision

Decision: [DECISION TITLE]
Date: [DATE]
Impact: [High / Medium / Low]

What changed:
[Describe the architectural change]

Why:
[Rationale for the decision]

Affected components:
[List components that changed]

Update ARCHITECTURE.md:

1. Section 2 (High-Level System Overview)
   - Update architecture diagram if topology changed
   - Update key characteristics if pattern changed

2. Section 4 (Core Components)
   - Update affected component descriptions
   - Add/remove subsections if components were added/removed

3. Section 5 (Data Flow)
   - Update flow diagrams if data paths changed

4. Section 7 (Stability Zones)
   - Mark new components with appropriate stability
   - Move affected components if stability changed

5. Section 8 (AI Coding Rules)
   - Add new architectural decision to "Key Architectural Decisions"
   - Include brief rationale

6. Update "Last Updated" date

Keep total length under 300 lines. Consider compressing less critical sections.
```

**Example Usage:**

```
SCENARIO: Major Architectural Decision

Decision: Migration from SQLite to PostgreSQL
Date: 2025-12-28
Impact: High

What changed:
- Database engine changed from SQLite to PostgreSQL
- Connection pooling added (pgbouncer)
- Async driver changed (asyncpg instead of aiosqlite)

Why:
- Scalability: Need concurrent connections for production load
- Features: Need advanced PostgreSQL features (JSON columns, full-text search)
- Performance: Better query optimization for complex queries

Affected components:
- backend/app/db/database.py (connection setup)
- backend/alembic/ (migration scripts)
- docker-compose.yml (new postgres service)
- TECHNICAL_DEBTS.md (SQLite migration item resolved)

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 4. External Integration Added

```
SCENARIO: New External Integration

Integration: [SERVICE/API NAME]
Type: [AI Provider / Payment Gateway / Storage / Auth / Monitoring / etc.]
Location: [CODE PATH]
Documentation: [LINK TO INTEGRATION DOCS]

Purpose:
[What does this integration do?]

Configuration:
[Environment variables, API keys, etc.]

Update ARCHITECTURE.md:

1. Section 2 (High-Level System Overview)
   - Add to architecture diagram if it's a major integration

2. Section 4.4 (External Integrations)
   - Add new integration with:
     - Name
     - Purpose
     - Authentication method
     - Client location

3. Section 6 (Configuration & Environment Assumptions)
   - Add new environment variables
   - Update configuration section

4. Section 7 (Stability Zones)
   - Add integration client code to appropriate stability zone

5. Section 8 (AI Coding Rules)
   - Add new AI_[PROVIDER].md file if created

6. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: New External Integration

Integration: Stripe Payment API
Type: Payment Gateway
Location: backend/app/services/stripe_client.py
Documentation: docs/integrations/stripe.md

Purpose:
- Process payments for premium features
- Manage subscriptions
- Handle webhooks for payment events

Configuration:
- STRIPE_API_KEY (secret)
- STRIPE_WEBHOOK_SECRET (secret)
- STRIPE_PUBLISHABLE_KEY (public)

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 5. Directory Structure Reorganization

```
SCENARIO: Directory Structure Changed

Changes:
[LIST BEFORE/AFTER DIRECTORY STRUCTURE]

Example:
Before:
  backend/app/services/ (all services mixed)

After:
  backend/app/services/
    ├── ai_providers/    (HuggingFace, Replicate)
    ├── integrations/    (Stripe, SendGrid)
    └── internal/        (Session manager, file handler)

Reason:
[Why was this reorganization necessary?]

Update ARCHITECTURE.md:

1. Section 3 (Repository Structure)
   - Update directory tree to reflect new structure
   - Update "Purpose of each major directory" descriptions

2. Section 4 (Core Components)
   - Update file paths in component descriptions
   - Keep logical component organization the same

3. Section 8 (AI Coding Rules)
   - Update file paths in "Key Architectural Decisions" if mentioned

4. Update "Last Updated" date

Keep total length under 300 lines.
```

---

### 6. New AI*.md Rule File Added

```
SCENARIO: New AI Rule File Created

File: [AI_*.md]
Purpose: [What coding rules does it define?]
Scope: [Which part of codebase? Frontend/Backend/Infra/Provider?]

Update ARCHITECTURE.md:

1. Section 8 (AI Coding Rules and Behavioral Contracts)
   - Add new file to "Authoritative AI Rule Files" list
   - Place in appropriate category (Backend Rules / Frontend Rules / etc.)
   - Update rule precedence if needed

2. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: New AI Rule File Created

File: AI_POSTGRESQL.md
Purpose: PostgreSQL-specific patterns, query optimization, migration rules
Scope: Backend database layer (after migration from SQLite)

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 7. Technology Stack Change

```
SCENARIO: Technology Replaced

What changed:
- Old: [OLD TECHNOLOGY]
- New: [NEW TECHNOLOGY]

Where: [COMPONENT/LAYER]

Reason:
[Why the change?]

Migration status:
[✅ Complete / 🔄 In Progress / 🔮 Planned]

Update ARCHITECTURE.md:

1. Section 2 (High-Level System Overview)
   - Update tech stack table
   - Update architecture diagram if topology changed

2. Section 4 (Core Components)
   - Update component technology descriptions
   - Update file paths if changed

3. Section 6 (Configuration & Environment Assumptions)
   - Update environment variables
   - Update configuration assumptions

4. Section 7 (Stability Zones)
   - Mark new implementation with appropriate stability
   - Move to experimental if it's a new migration

5. Section 8 (AI Coding Rules)
   - Add/update AI_*.md file for new technology
   - Update key architectural decisions

6. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: Technology Replaced

What changed:
- Old: Zustand (global state)
- New: Redux Toolkit (global state + data caching)

Where: Frontend state management (frontend/src/services/)

Reason:
- Need better DevTools integration
- RTK Query provides data caching and sync
- Team more familiar with Redux patterns

Migration status:
🔄 In Progress (auth migrated, restoration pending)

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 8. Deprecation / Removal

```
SCENARIO: Component Deprecated or Removed

Component: [COMPONENT NAME]
Path: [FILE PATH]
Status: [⚠️ Deprecated / ❌ Removed]

Reason:
[Why deprecated/removed?]

Replacement:
[What replaces it? Or "None" if just removed]

Update ARCHITECTURE.md:

1. Section 3 (Repository Structure)
   - Remove from directory tree if deleted
   - Add note if deprecated but still present

2. Section 4 (Core Components)
   - Remove component description if deleted
   - Add deprecation note if still present
   - Add replacement component if applicable

3. Section 5 (Data Flow)
   - Update flow diagrams if data paths changed

4. Section 7 (Stability Zones)
   - Remove from stability zones if deleted
   - Move to "Deprecated" subsection if still present

5. Update "Last Updated" date

Keep total length under 300 lines.
```

**Example Usage:**

```
SCENARIO: Component Deprecated or Removed

Component: Flask Backend (legacy)
Path: backend_legacy/ (entire directory)
Status: ❌ Removed

Reason:
- Migration to FastAPI complete
- All endpoints ported
- No longer needed

Replacement:
FastAPI backend (backend/app/)

Update ARCHITECTURE.md:
[... rest of template ...]
```

---

### 9. Deployment Model Changed

```
SCENARIO: Deployment Architecture Changed

What changed:
[Describe deployment change]

Examples:
- Added Kubernetes manifests
- Switched from Docker Compose to Helm
- Added CI/CD pipeline
- Moved from external proxy to embedded nginx
- Added service mesh (Istio)

Impact:
[How does this affect the architecture?]

Update ARCHITECTURE.md:

1. Section 2 (High-Level System Overview)
   - Update architecture diagram if topology changed
   - Update deployment pattern description

2. Section 6 (Configuration & Environment Assumptions)
   - Update deployment assumptions
   - Add new configuration requirements

3. Section 7 (Stability Zones)
   - Mark new infrastructure code with appropriate stability

4. Section 8 (AI Coding Rules)
   - Add new AI_*.md file if created (e.g., AI_KUBERNETES.md)
   - Update key architectural decisions

5. Update "Last Updated" date

Keep total length under 300 lines.
```

---

### 10. Minor Update (Documentation Links, Typos)

```
SCENARIO: Minor Update

Changes:
[LIST MINOR CHANGES]

Examples:
- Fixed typo in Section X
- Updated link to docs/configuration.md
- Corrected file path
- Updated "Last Updated" date only

Update ARCHITECTURE.md:

1. Make the specific change
2. Update "Last Updated" date
3. Keep everything else unchanged

No need to analyze or compress. Simple fix.
```

---

## Validation After Update

### Post-Update Checklist

After updating ARCHITECTURE.md, validate:

```
[ ] Still under 300 lines (use `wc -l ARCHITECTURE.md`)
[ ] All 9 sections still present
[ ] "Last Updated" date changed
[ ] Section numbering intact (1-9)
[ ] Emoji markers consistent (✅🔄⚠️🔮)
[ ] ASCII diagrams still formatted correctly
[ ] Links still work (relative paths)
[ ] No coding rules added (still only references AI*.md)
[ ] Changes are in appropriate sections
[ ] Style consistent with original
```

### Length Management

If update pushes length over 300 lines:

```
The update has increased ARCHITECTURE.md to [XXX] lines (over 300 limit).

Please compress the document:

1. Look for redundant descriptions in Section 4
2. Shorten bullet points in Section 3
3. Remove less critical details in Section 6
4. Consider linking to docs/ for detailed information
5. Use tables instead of paragraphs where possible

Target: Get back under 300 lines while preserving all critical information.
Priority: Keep Sections 7 (Stability Zones) and 8 (AI Rules) complete.
```

---

## Common Update Patterns

### Pattern 1: Feature Addition (Experimental → Stable)

**Initial State:** New feature added as ⚠️ Experimental

**Update 1 (After testing):**
```
Move component from ⚠️ Experimental to 🔄 Semi-Stable in Section 7.
Reason: Tested, but API may still evolve based on user feedback.
```

**Update 2 (After 3-6 months):**
```
Move component from 🔄 Semi-Stable to ✅ Stable in Section 7.
Reason: Production-proven, API stable, no issues reported.
```

### Pattern 2: Technology Migration

**Phase 1: Parallel Systems**
```
Section 7: Both old and new systems present
- Old: ✅ Stable (still in use)
- New: ⚠️ Experimental (migration in progress)
```

**Phase 2: Migration Complete**
```
Section 7: Remove old system, promote new
- Old: ❌ Removed
- New: 🔄 Semi-Stable (recently migrated)
```

**Phase 3: Stabilization**
```
Section 7: New system proven
- New: ✅ Stable (production-proven)
```

### Pattern 3: Architectural Evolution

**Evolution Tracking:**

```
Section 8: Key Architectural Decisions

Update the list to include:

7. [NEW DECISION] (2025-XX-XX)
   - Decision: [What was decided]
   - Rationale: [Why]
   - Replaces: [Old decision #N] (if applicable)
```

### Pattern 4: Configuration Changes

**When config system evolves:**

```
Section 6: Configuration & Environment Assumptions

Add note:
"Updated in [VERSION/DATE]: [What changed in config system]"

Update:
- Environment variables list
- Config file structure
- Loading priority (if changed)
```

---

## Quick Reference Card

### "Which Section Should I Update?"

| Change Type | Sections to Update |
|-------------|-------------------|
| New feature added | 3, 4, 5 (if flow), 7 |
| Component stability changed | 7, (4 if responsibilities changed) |
| Major architectural decision | 2, 4, 5, 7, 8 |
| External integration added | 2 (diagram), 4.4, 6, 7, 8 (if AI rules) |
| Directory restructure | 3, 4 (paths) |
| New AI*.md file | 8 only |
| Tech stack change | 2, 4, 6, 7, 8 |
| Deprecation/removal | 3, 4, 5 (if flow), 7 |
| Deployment change | 2, 6, 7 (if infra code), 8 (if AI rules) |
| Minor fix (typo, link) | Specific section only |

---

## Git Commit Message Examples

After updating ARCHITECTURE.md:

```bash
# Feature addition
git commit -m "docs(arch): add WebSocket notifications to experimental zone"

# Stability promotion
git commit -m "docs(arch): promote AI provider system to stable"

# Major decision
git commit -m "docs(arch): document PostgreSQL migration decision"

# Integration
git commit -m "docs(arch): add Stripe payment integration"

# Restructure
git commit -m "docs(arch): update directory structure after services reorganization"

# Tech change
git commit -m "docs(arch): update frontend stack to Redux Toolkit"

# Removal
git commit -m "docs(arch): remove deprecated Flask backend from architecture"

# Minor update
git commit -m "docs(arch): fix typo in Section 4"
```

---

## Integration with Project Workflow

### Add to CLAUDE.md

```markdown
## Updating Architecture Documentation

When you make architectural changes, update ARCHITECTURE.md:

1. Identify the type of change (see tmp/ARCHITECTURE_UPDATE_PROMPTS.md)
2. Use the appropriate scenario-specific prompt
3. Update only affected sections
4. Validate with post-update checklist
5. Keep total length under 300 lines

Common changes:
- New feature → Update Sections 3, 4, 7
- Stability change → Update Section 7
- New integration → Update Sections 4.4, 6, 7
- Major decision → Update Sections 2, 4, 5, 7, 8
```

### Create Update Script (Optional)

```bash
#!/bin/bash
# scripts/update_architecture.sh

echo "What type of change?"
echo "1) New feature"
echo "2) Stability zone change"
echo "3) Major architectural decision"
echo "4) External integration"
echo "5) Other"
read -p "Select (1-5): " choice

case $choice in
  1) cat tmp/ARCHITECTURE_UPDATE_PROMPTS.md | sed -n '/### 1. New Feature Added/,/^---$/p' ;;
  2) cat tmp/ARCHITECTURE_UPDATE_PROMPTS.md | sed -n '/### 2. Component Moved/,/^---$/p' ;;
  3) cat tmp/ARCHITECTURE_UPDATE_PROMPTS.md | sed -n '/### 3. Major Architectural/,/^---$/p' ;;
  4) cat tmp/ARCHITECTURE_UPDATE_PROMPTS.md | sed -n '/### 4. External Integration/,/^---$/p' ;;
  5) cat tmp/ARCHITECTURE_UPDATE_PROMPTS.md | sed -n '/## General Update Prompt/,/^---$/p' ;;
esac

echo ""
echo "Copy the prompt above and customize it with your changes."
echo "Then paste to Claude/AI assistant to update ARCHITECTURE.md"
```

---

## Examples from This Project

### Example 1: When Phase 2.5 Admin Config UI is Complete

```
SCENARIO: New Feature Added

Feature: Admin Configuration UI for JSON Model Settings
Location: frontend/src/features/admin/configuration/, backend/app/api/v1/routes/config.py
Stability: 🔄 Semi-Stable (newly implemented, API may evolve)

Context:
- Admin-only UI for editing model configurations
- Real-time JSON validation and preview
- Saves to config/local.json with highest priority
- See docs/chats/admin-configuration-interface-for-json-model-settings-2025-12-25.md

Update ARCHITECTURE.md:

1. Section 3 (Repository Structure)
   - Add frontend/src/features/admin/configuration/
   - Add backend/app/api/v1/routes/config.py

2. Section 4.1 (Frontend)
   - Add to admin feature: "Configuration management (admin-only)"

3. Section 4.2 (Backend)
   - Add to API Routes: "/api/v1/admin/config - Model configuration CRUD (admin-only)"

4. Section 7 (Stability Zones)
   - Add to "🔄 Semi-Stable" zone:
     "Admin configuration UI (features/admin/configuration/) - newly implemented, may evolve"

5. Update "Last Updated" date

Keep total length under 300 lines.
```

### Example 2: When SQLite → PostgreSQL Migration Happens

```
SCENARIO: Major Architectural Decision + Technology Replaced

Decision: Migration from SQLite to PostgreSQL
Date: [FUTURE DATE]
Impact: High

What changed:
- Database engine: SQLite → PostgreSQL
- Driver: aiosqlite → asyncpg
- Added: Connection pooling (pgbouncer)
- Added: docker-compose service for PostgreSQL

Why:
- Scalability: Production load requires concurrent connections
- Features: Need JSON columns, full-text search
- Performance: Better query optimization

Affected components:
- backend/app/db/database.py (connection setup)
- docker-compose.yml (new postgres service)
- TECHNICAL_DEBTS.md (resolved SQLite migration item)

Update ARCHITECTURE.md:

1. Section 2 (High-Level System Overview)
   - Update tech stack table: SQLite → PostgreSQL
   - Update stability: "Database: PostgreSQL (production-ready)"

2. Section 4.2 (Backend - Database)
   - Current: "SQLite (file-based)" → "PostgreSQL (production database)"
   - Update database location from /data/*.db to connection string

3. Section 6 (Configuration)
   - Update DATABASE_URL format
   - Add PostgreSQL-specific env vars (if any)

4. Section 7 (Stability Zones)
   - Move database from "⚠️ Experimental" to "🔄 Semi-Stable"
   - Note: "Recently migrated from SQLite, stabilizing"

5. Section 8 (AI Coding Rules)
   - Update: AI_SQLite.md → AI_POSTGRESQL.md
   - Add to Key Architectural Decisions:
     "6. SQLite → PostgreSQL Migration - Scalability and production features"

6. Update "Last Updated" date

Keep total length under 300 lines.
```

---

**End of ARCHITECTURE_UPDATE_PROMPTS.md**
