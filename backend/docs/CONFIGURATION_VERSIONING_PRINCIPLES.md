# Configuration Versioning Principles

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Target Audience**: Developers, DevOps, System Administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Two Types of Versioning](#two-types-of-versioning)
3. [Config Version vs. Backup Timestamps](#config-version-vs-backup-timestamps)
4. [When Does Config Version Change?](#when-does-config-version-change)
5. [When Are Backups Created?](#when-are-backups-created)
6. [Understanding Backup Filenames](#understanding-backup-filenames)
7. [Real-World Scenarios](#real-world-scenarios)
8. [Common Misconceptions](#common-misconceptions)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Photo Restoration API implements a **dual-tracking system** for configuration management:

1. **Schema Versioning** (`config_version` field) - Tracks structural changes to the configuration format
2. **Change History** (backup timestamps) - Tracks every individual change made to configuration data

These two systems serve **different purposes** and operate **independently**. Understanding the distinction is crucial for effective configuration management.

---

## Two Types of Versioning

### 1. Schema Versioning (Semantic Versioning)

**What it is:**
- A version number in the format `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)
- Stored in the `config_version` field of each JSON config file
- Represents the **structure/schema** of the configuration file

**What it tracks:**
- Changes to required fields
- Changes to field types or validation rules
- Addition/removal of configuration sections
- Breaking changes in how config is interpreted

**Who controls it:**
- **Developers** define schema versions
- **Migration scripts** upgrade configs between versions
- **Application code** validates compatibility

**Example:**
```json
{
  "config_version": "1.0.0",
  "application": { ... },
  "models": [ ... ]
}
```

### 2. Change History (Timestamp-based)

**What it is:**
- Microsecond-precision timestamps in backup filenames
- Format: `YYYYMMDD_HHMMSS_microseconds` (e.g., `20251231_175709_381628`)
- Creates a complete audit trail of every configuration change

**What it tracks:**
- Every save operation (UI, API, scripts)
- Every delete operation
- Every migration operation
- Exact time each change was made

**Who controls it:**
- **Automatic**: The backup system creates timestamps
- **No manual intervention** required
- **Cannot be disabled** (safety feature)

**Example:**
```
local.v1.0.0.20251231_175709_381628.json
            ^^^^^^^^^^^^^^^^^^^^^^^^
            Timestamp: Dec 31, 2025 at 17:57:09.381628
```

---

## Config Version vs. Backup Timestamps

### Side-by-Side Comparison

| Aspect | Config Version | Backup Timestamp |
|--------|---------------|------------------|
| **Purpose** | Track schema evolution | Track change history |
| **Format** | Semantic version (1.0.0) | Timestamp (20251231_175709) |
| **Changes when** | Schema structure changes | Every config save/delete |
| **Frequency** | Rarely (months/years) | Often (daily/hourly) |
| **Controlled by** | Developers | Automatic system |
| **Stored in** | config_version field | Backup filename |
| **Example** | 1.0.0 → 1.1.0 | Multiple backups per day |

### Visual Example

```
Timeline of Config Changes:

Day 1 (App Release):
  config_version: 1.0.0
  No backups yet

Day 1 @ 10:00 - User adds Model A via UI:
  config_version: 1.0.0  (unchanged - same schema)
  Backup: local.v1.0.0.20251231_100000_123456.json

Day 1 @ 14:00 - User modifies Model A:
  config_version: 1.0.0  (unchanged - same schema)
  Backup: local.v1.0.0.20251231_140000_789012.json

Day 30 (App Upgrade to 1.1.0):
  config_version: 1.0.0 → 1.1.0  (schema changed!)
  Backup: local.v1.0.0.20260130_120000_000000.json
  Migration applied, new field added

Day 30 @ 15:00 - User adds Model B:
  config_version: 1.1.0  (unchanged - same schema)
  Backup: local.v1.1.0.20260130_150000_456789.json
```

Notice:
- Config version changed **once** (1.0.0 → 1.1.0) in 30 days
- Backups created **four times** (every config change)
- Version stays constant between schema changes
- Each backup preserves the version at that time

---

## When Does Config Version Change?

### ✅ Config Version DOES Change When:

#### 1. **New Required Fields Added**
```python
# Migration from 1.0.0 → 1.1.0
class Migration_1_0_to_1_1(ConfigMigration):
    def migrate(self, config):
        # Add new required field
        config["model_configuration"]["presets"] = []
        config["config_version"] = "1.1.0"
        return config
```

**Why**: The schema structure changed - old configs lack the `presets` field.

#### 2. **Field Types or Validation Rules Change**
```python
# Migration from 1.1.0 → 1.2.0
# Change: session.cleanup_hours (int) → session.cleanup_seconds (int)
class Migration_1_1_to_1_2(ConfigMigration):
    def migrate(self, config):
        hours = config["session"].pop("cleanup_hours", 24)
        config["session"]["cleanup_seconds"] = hours * 3600
        config["config_version"] = "1.2.0"
        return config
```

**Why**: Field renamed/restructured - requires migration logic.

#### 3. **Configuration Sections Added/Removed**
```python
# Migration from 1.2.0 → 2.0.0 (major version - breaking change)
class Migration_1_2_to_2_0(ConfigMigration):
    def migrate(self, config):
        # Remove deprecated section
        config.pop("legacy_settings", None)
        # Add new section
        config["feature_flags"] = {"new_ui": False}
        config["config_version"] = "2.0.0"
        return config
```

**Why**: Breaking change - old configs won't work without migration.

#### 4. **Semantic Changes in How Config is Interpreted**
```python
# Migration from 2.0.0 → 2.1.0
# Change: cors.origins from string → array
class Migration_2_0_to_2_1(ConfigMigration):
    def migrate(self, config):
        origins = config["cors"]["origins"]
        if isinstance(origins, str):
            config["cors"]["origins"] = [origins]
        config["config_version"] = "2.1.0"
        return config
```

**Why**: Application now expects array, not string.

### ❌ Config Version Does NOT Change When:

#### 1. **Model Data Modified**
```json
// Before
{"models": [{"id": "model-1", "enabled": true}]}

// After - NO VERSION CHANGE
{"models": [{"id": "model-1", "enabled": false}]}
```

**Why**: Schema structure unchanged - only data values changed.

#### 2. **Models Added or Removed**
```json
// Before
{"models": [{"id": "model-1"}]}

// After - NO VERSION CHANGE
{"models": [{"id": "model-1"}, {"id": "model-2"}]}
```

**Why**: Schema allows any number of models - no structural change.

#### 3. **Configuration Values Changed**
```json
// Before
{"application": {"log_level": "INFO"}}

// After - NO VERSION CHANGE
{"application": {"log_level": "DEBUG"}}
```

**Why**: Changing a value doesn't change the schema.

#### 4. **Optional Fields Populated**
```json
// Before
{"server": {"host": "0.0.0.0"}}

// After - NO VERSION CHANGE
{"server": {"host": "0.0.0.0", "workers": 4}}
```

**Why**: Optional fields can be added/removed without schema change (if schema allows it).

---

## When Are Backups Created?

Backups are created **automatically** in the following scenarios:

### 1. **Application Startup (Migration)**
```
Trigger: Application starts with outdated config
Action:
  1. Detect config_version < CURRENT_VERSION
  2. Create backup: config.v{old_version}.{timestamp}.json
  3. Apply migrations
  4. Save updated config with new version
```

**Example:**
```
Before startup:
  local.json has config_version: 0.9.0

On startup:
  Backup created: local.v0.9.0.20251231_163112_857356.json
  Migration applied: 0.9.0 → 1.0.0
  local.json now has config_version: 1.0.0
```

### 2. **Runtime Configuration Changes (UI/API)**
```
Trigger: User modifies config via Admin UI or API
Action:
  1. Load current config from disk
  2. Create backup: config.v{current_version}.{timestamp}.json
  3. Apply changes
  4. Save updated config (same version)
```

**Example:**
```
User clicks "Save" in Admin UI:
  Current: local.json (config_version: 1.0.0)
  Backup: local.v1.0.0.20251231_175709_381628.json
  Updated: local.json (config_version: 1.0.0, new model added)
```

### 3. **Delete Operations**
```
Trigger: User deletes model config via Admin UI or API
Action:
  1. Load current config from disk
  2. Create backup: config.v{current_version}.{timestamp}.json
  3. Remove model from config
  4. Save updated config
```

**Example:**
```
User deletes model "replicate-restore":
  Backup: local.v1.0.0.20251231_180000_123456.json
  (Backup contains deleted model - can be restored)
```

### 4. **Manual Restore Operations**
```
Trigger: Admin runs restore script
Action:
  1. Create backup of current config
  2. Copy backup file to current config location
  3. Log restoration
```

**Example:**
```bash
python scripts/restore_config.py config/local.json --latest

# Creates safety backup before restoring
Backup: local.v1.0.0.20251231_181500_999999.json
Restored from: local.v1.0.0.20251231_175709_381628.json
```

### 5. **Manual Migration Scripts**
```
Trigger: Admin runs migration script
Action:
  1. Detect version mismatch
  2. Create backup
  3. Apply migrations
  4. Save with new version
```

---

## Understanding Backup Filenames

### Filename Format

```
{stem}.v{major}.{minor}.{patch}.{date}_{time}_{microseconds}.json
  │      │      │      │       │      │        │
  │      │      │      │       │      │        └─ Microseconds (000000-999999)
  │      │      │      │       │      └─ Time (HHMMSS)
  │      │      │      │       └─ Date (YYYYMMDD)
  │      │      │      └─ Patch version
  │      │      └─ Minor version
  │      └─ Major version
  └─ Config file name (default, local, production)
```

### Real Example Breakdown

```
local.v1.0.0.20251231_175709_381628.json
│     │ │ │  │        │      │
│     │ │ │  │        │      └─ 381,628 microseconds
│     │ │ │  │        └─ 17:57:09 (5:57:09 PM)
│     │ │ │  └─ December 31, 2025
│     │ │ └─ Patch: 0
│     │ └─ Minor: 0
│     └─ Major: 1
└─ Filename stem: local
```

**What this tells you:**
- **Config file**: `local.json` (model overrides)
- **Schema version at backup time**: 1.0.0
- **Exact moment created**: Dec 31, 2025 at 5:57:09.381628 PM
- **What's inside**: Config state at that exact moment

### Why Microsecond Precision?

Without microseconds, rapid changes could overwrite backups:

```
❌ Without microseconds (second precision):
  18:57:09 - User saves Model A
    Backup: local.v1.0.0.20251231_175709.json
  18:57:09 - User saves Model B (same second!)
    Backup: local.v1.0.0.20251231_175709.json ← OVERWRITES!
    Result: Lost Model A backup!

✅ With microseconds:
  18:57:09.123456 - User saves Model A
    Backup: local.v1.0.0.20251231_175709_123456.json
  18:57:09.789012 - User saves Model B
    Backup: local.v1.0.0.20251231_175709_789012.json
    Result: Both backups preserved!
```

### Backup Retention Policy

```python
MAX_BACKUPS_PER_FILE = 10  # Keep last 10 backups per config file
```

**How it works:**
1. System creates backup before every save
2. After saving, checks backup count
3. If more than 10 backups exist, deletes oldest ones
4. Keeps most recent 10 backups

**Example timeline:**
```
# 15 backups created over time
local.v1.0.0.20251201_100000_000000.json ← Deleted (oldest)
local.v1.0.0.20251202_100000_000000.json ← Deleted
local.v1.0.0.20251203_100000_000000.json ← Deleted
local.v1.0.0.20251204_100000_000000.json ← Deleted
local.v1.0.0.20251205_100000_000000.json ← Deleted
local.v1.0.0.20251222_100000_000000.json ← Kept (10th oldest)
local.v1.0.0.20251223_100000_000000.json ← Kept
local.v1.0.0.20251224_100000_000000.json ← Kept
...
local.v1.0.0.20251231_175709_381628.json ← Kept (newest)
```

---

## Real-World Scenarios

### Scenario 1: Daily Operations (No Version Changes)

**Situation**: Normal usage over 30 days

```
Day 1:
  Config: config_version: 1.0.0
  User adds Model A via UI
  Backup: local.v1.0.0.20251201_100000_123456.json

Day 5:
  Config: config_version: 1.0.0 (unchanged)
  User modifies Model A parameters
  Backup: local.v1.0.0.20251205_143000_789012.json

Day 10:
  Config: config_version: 1.0.0 (unchanged)
  User adds Model B via UI
  Backup: local.v1.0.0.20251210_091500_456789.json

Day 15:
  Config: config_version: 1.0.0 (unchanged)
  User deletes Model A
  Backup: local.v1.0.0.20251215_160000_321654.json

Day 30:
  Config: config_version: 1.0.0 (still unchanged)
  Total backups: 4 (one per change)
  Version: Never changed (schema stable)
```

**Key Points:**
- Version stayed `1.0.0` entire month
- 4 backups created (change history)
- Each backup has unique timestamp
- Can restore to any point in time

### Scenario 2: Application Upgrade (Version Changes)

**Situation**: Deploying new application version with schema changes

```
Before Deployment:
  App version: 1.5.0
  Config: config_version: 1.0.0
  File: local.json

Deploy New App Version 2.0.0:
  New app requires config_version: 1.1.0

On First Startup After Deploy:
  1. App detects: config_version (1.0.0) < required (1.1.0)
  2. Creates backup: local.v1.0.0.20260115_120000_000000.json
  3. Runs migration: Migration_1_0_to_1_1
  4. Adds new field: model_configuration.presets = []
  5. Updates: config_version: 1.1.0
  6. Saves migrated config
  7. App starts successfully

After Migration:
  Config: config_version: 1.1.0 (upgraded!)
  Backup contains: Old config with version 1.0.0

User Changes After Migration:
  User adds Model C via UI
  Config: config_version: 1.1.0 (unchanged - no schema change)
  Backup: local.v1.1.0.20260115_150000_123456.json
```

**Key Points:**
- Version changed once: 1.0.0 → 1.1.0 (migration)
- Backup before migration preserves old structure
- Subsequent changes use new version in filename
- Old backup can restore pre-migration state

### Scenario 3: Accidental Config Corruption

**Situation**: User accidentally breaks configuration

```
10:00 AM - Working Config:
  Config: local.json with 4 models
  Last backup: local.v1.0.0.20251231_095000_000000.json

10:30 AM - User Makes Change:
  Tries to add Model E via UI
  Accidentally deletes all models (UI bug? User error?)
  System creates backup: local.v1.0.0.20251231_103000_123456.json
  Config now: Empty models array!

10:31 AM - User Notices Problem:
  "Where did all my models go?!"

10:32 AM - Admin Restores:
  $ python scripts/restore_config.py config/local.json --latest

  Lists available backups:
    1. local.v1.0.0.20251231_103000_123456.json (1 minute ago) - empty!
    2. local.v1.0.0.20251231_095000_000000.json (1 hour ago) - has models!

  Admin selects #2

  Restoration:
    - Creates safety backup: local.v1.0.0.20251231_103200_999999.json
    - Restores from: local.v1.0.0.20251231_095000_000000.json
    - All 4 models back!

10:33 AM - Problem Solved:
  Config restored to 10:00 AM state
  User relieved
  Incident documented for UI bug fix
```

**Key Points:**
- Backup system saved the day
- Multiple restore points available
- Even corrupted state was backed up (safety)
- Can choose which backup to restore
- Version stayed same throughout (1.0.0)

### Scenario 4: Multi-Environment Deployment

**Situation**: Deploying config changes across environments

```
Development Environment:
  Config: config_version: 1.0.0
  User tests new Model F
  Backup: local.v1.0.0.20251231_140000_111111.json (dev)

Staging Environment:
  Config: config_version: 1.0.0
  Deploy same model config
  Backup: local.v1.0.0.20251231_150000_222222.json (staging)
  Test passes

Production Environment:
  Config: config_version: 1.0.0
  Deploy to production
  Backup: local.v1.0.0.20251231_160000_333333.json (prod)
  All environments aligned
```

**Key Points:**
- Same version across all environments
- Each environment has own backup history
- Timestamps differ (deployment times)
- Can rollback any environment independently

---

## Common Misconceptions

### ❌ Misconception 1: "Version should change when I save config"

**Reality**: Version only changes when **schema** changes, not when **data** changes.

```
Wrong expectation:
  Before save: config_version: 1.0.0
  Save model change
  After save: config_version: 1.0.1 ← This doesn't happen!

Actual behavior:
  Before save: config_version: 1.0.0
  Save model change
  After save: config_version: 1.0.0 ← Same version
  Backup created: local.v1.0.0.20251231_180000_123456.json ← Track via timestamp!
```

### ❌ Misconception 2: "I need to manually increment version"

**Reality**: Versions are controlled by **migration scripts**, not manual edits.

```
Wrong approach:
  1. Edit local.json
  2. Change "config_version": "1.0.0" to "1.0.1"
  3. Save
  Result: App may reject config or behave unexpectedly

Right approach:
  1. Developers create migration script (if schema changes)
  2. Migration script updates version
  3. App applies migration on startup
  Result: Version updated consistently with schema changes
```

### ❌ Misconception 3: "Backups only created during migration"

**Reality**: Backups created for **every config change** (UI, API, migration, manual).

```
Wrong belief:
  "Backups only happen at app startup"

Actual behavior:
  ✅ App startup (migration)
  ✅ UI save button
  ✅ Admin API calls
  ✅ Delete operations
  ✅ Manual restore operations
  ✅ Any config modification
```

### ❌ Misconception 4: "Higher version number means newer config"

**Reality**: Version indicates **schema version**, not **recency**.

```
Confusing scenario:
  Backup A: local.v2.0.0.20240101_120000_000000.json (Jan 1, 2024)
  Backup B: local.v1.0.0.20251231_180000_000000.json (Dec 31, 2025)

  Which is "newer"?
  - By version: A (2.0.0 > 1.0.0)
  - By timestamp: B (2025 > 2024) ← This is recency!

  Interpretation:
  - Backup A: Newer schema, older data (from downgrade?)
  - Backup B: Older schema, newer data (current production)
```

### ❌ Misconception 5: "I can delete old backups manually"

**Reality**: Retention policy **automatically** manages backups - manual deletion not recommended.

```
Wrong approach:
  $ rm config/backups/local.v1.0.0.20251201*.json
  Result: Lost recovery points, breaks retention policy

Right approach:
  Let system manage backups automatically
  Retention policy keeps last 10 backups
  Oldest automatically deleted when limit exceeded
  Manual intervention not needed (or recommended)
```

---

## Best Practices

### For Developers

#### 1. **Create Migrations for Schema Changes**

```python
# Bad: Directly change schema without migration
# Just add field to code and hope for the best ❌

# Good: Create migration class ✅
class Migration_1_0_to_1_1(ConfigMigration):
    """Add model presets feature."""
    from_version = "1.0.0"
    to_version = "1.1.0"

    def migrate(self, config: dict) -> dict:
        if "model_configuration" not in config:
            config["model_configuration"] = {}
        config["model_configuration"]["presets"] = []
        config["config_version"] = "1.1.0"
        return config

    def rollback(self, config: dict) -> dict:
        if "model_configuration" in config:
            config["model_configuration"].pop("presets", None)
        config["config_version"] = "1.0.0"
        return config
```

#### 2. **Use Semantic Versioning Correctly**

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (1.x.x → 2.0.0)
  - Remove required fields
  - Change field types incompatibly
  - Restructure config hierarchy

MINOR: Additive changes (1.0.x → 1.1.0)
  - Add new optional fields
  - Add new configuration sections
  - Extend existing enums

PATCH: Bug fixes (1.0.0 → 1.0.1)
  - Rarely used for config schemas
  - Fix migration bugs
  - Correct default values
```

#### 3. **Test Migrations Thoroughly**

```python
def test_migration_1_0_to_1_1():
    """Test migration from 1.0.0 to 1.1.0."""
    old_config = {
        "config_version": "1.0.0",
        "application": {...},
        "models": [...]
    }

    migration = Migration_1_0_to_1_1()
    new_config = migration.migrate(old_config)

    # Verify version updated
    assert new_config["config_version"] == "1.1.0"

    # Verify new field added
    assert "presets" in new_config["model_configuration"]

    # Verify data preserved
    assert new_config["models"] == old_config["models"]

    # Verify rollback works
    rolled_back = migration.rollback(new_config)
    assert rolled_back["config_version"] == "1.0.0"
    assert "presets" not in rolled_back.get("model_configuration", {})
```

#### 4. **Document Schema Changes**

```markdown
# docs/CONFIG_CHANGELOG.md

## Version 1.1.0 (2026-01-15)

### Added
- `model_configuration.presets` - Array of preset configurations

### Migration Notes
- Automatic migration adds empty presets array
- No manual intervention required
- Compatible with 1.0.0 configs

### Breaking Changes
None (backward compatible)
```

### For Operations/DevOps

#### 1. **Monitor Backup Directory Growth**

```bash
# Set up monitoring alert
du -sh /opt/retro/config/backups

# Alert if backup directory exceeds expected size
if [ $(du -s /opt/retro/config/backups | cut -f1) -gt 100000 ]; then
    echo "Backup directory unusually large - investigate"
fi
```

#### 2. **Verify Backups After Deployment**

```bash
#!/bin/bash
# Post-deployment verification script

echo "Checking config version..."
VERSION=$(jq -r '.config_version' /opt/retro/config/local.json)
echo "Current version: $VERSION"

echo "Checking recent backups..."
ls -lt /opt/retro/config/backups/ | head -5

echo "Verifying backup count..."
BACKUP_COUNT=$(ls -1 /opt/retro/config/backups/local.v*.json | wc -l)
if [ $BACKUP_COUNT -lt 1 ]; then
    echo "❌ ERROR: No backups found!"
    exit 1
fi

echo "✅ Config verification passed"
```

#### 3. **Keep External Backups of Critical Configs**

```bash
# Daily backup to external location (cron job)
#!/bin/bash
# /etc/cron.daily/backup-configs

BACKUP_DIR="/backup/photo-restoration/configs/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Backup current configs
cp /opt/retro/config/*.json "$BACKUP_DIR/"

# Backup recent backups directory
tar -czf "$BACKUP_DIR/backup-history.tar.gz" /opt/retro/config/backups/

# Keep 90 days of external backups
find /backup/photo-restoration/configs/ -type d -mtime +90 -exec rm -rf {} \;
```

#### 4. **Document Restore Procedures**

```markdown
# Emergency Config Restore Procedure

## Scenario: Production config corrupted

1. SSH to production server:
   ssh user@prod-server

2. List available backups:
   python /opt/retro/backend/scripts/restore_config.py \
     /opt/retro/config/local.json --list

3. Identify last known good backup:
   Review timestamps and pick backup before corruption

4. Restore (creates safety backup automatically):
   python /opt/retro/backend/scripts/restore_config.py \
     /opt/retro/config/local.json --restore <backup-number>

5. Restart application:
   systemctl restart photo-restoration

6. Verify:
   curl http://localhost:8000/api/v1/models
   (Should return model list)

7. Document incident:
   Update incident log with root cause
```

### For System Administrators

#### 1. **Understand Backup Retention**

```
Retention Policy:
  - Keep: Last 10 backups per config file
  - Delete: Oldest backups when limit exceeded
  - Automatic: No manual intervention needed

Example with 15 backups created:
  Backup 1-5: Deleted (oldest)
  Backup 6-15: Kept (most recent 10)

If you need longer retention:
  - Copy backups to external storage before auto-deletion
  - Use cron job for daily external backups
  - Keep external backups for compliance period (90 days, 1 year, etc.)
```

#### 2. **Monitor for Version Mismatches**

```bash
# Check version consistency across config files
for file in /opt/retro/config/*.json; do
    echo "$file: $(jq -r '.config_version // "NO VERSION"' $file)"
done

# Expected output:
# /opt/retro/config/default.json: 1.0.0
# /opt/retro/config/local.json: 1.0.0
# All should match (unless local.json is minimal)
```

#### 3. **Plan for Schema Upgrades**

```
Before Application Upgrade:
  1. Review release notes for config schema changes
  2. Check current config_version in production
  3. Verify migration path exists (e.g., 1.0.0 → 1.1.0)
  4. Test migration in staging environment
  5. Take manual backup before deployment

During Deployment:
  1. Deploy new application version
  2. Watch logs for migration execution
  3. Verify config_version updated
  4. Check that backup was created

After Deployment:
  1. Validate application starts successfully
  2. Test config-dependent features
  3. Keep manual backup for 24 hours
  4. Document any issues encountered
```

#### 4. **Set Up Alerts for Config Changes**

```bash
# Monitor config file changes
# Add to /etc/rsyslog.d/photo-restoration.conf

# Log all config modifications
/opt/retro/config/*.json {
    postrotate
        echo "Config file modified: $(date)" >> /var/log/config-changes.log
    endscript
}

# Or use inotify for real-time monitoring
inotifywait -m /opt/retro/config/ -e modify,create,delete | \
    while read path action file; do
        echo "$(date): $action on $file" >> /var/log/config-changes.log
        # Send alert if production config changed
        if [[ "$file" =~ (local|production).json ]]; then
            send_alert "Production config modified: $file"
        fi
    done
```

---

## Troubleshooting

### Problem 1: "Why didn't my config version change?"

**Symptom**: You modified config via UI, but version still shows `1.0.0`

**Diagnosis**:
```bash
# Check what changed
grep config_version /opt/retro/config/local.json
# Shows: "config_version": "1.0.0"

# Check if backup was created
ls -lt /opt/retro/config/backups/ | head -2
# Shows recent backup with same version
```

**Explanation**:
This is **expected behavior**. Config version only changes when the **schema** changes (new fields, structure changes), not when **data** changes (model values, settings).

**Solution**:
No action needed. Your change was saved and backed up. Use backup timestamps to track changes, not version numbers.

### Problem 2: "I have no backups in backups/ directory"

**Symptom**: `/opt/retro/config/backups/` is empty

**Diagnosis**:
```bash
# Check if directory exists
ls -la /opt/retro/config/backups/

# Check environment variable
echo $CONFIG_AUTO_MIGRATE

# Check application logs
grep -i "backup" /var/log/photo-restoration/app.log
```

**Possible Causes**:

1. **Auto-migration disabled**:
   ```bash
   # Check .env file
   grep CONFIG_AUTO_MIGRATE /opt/retro/.env

   # If set to false:
   CONFIG_AUTO_MIGRATE=false

   # Fix: Enable it
   CONFIG_AUTO_MIGRATE=true
   # Restart application
   ```

2. **Directory permissions**:
   ```bash
   # Check permissions
   ls -ld /opt/retro/config/backups/

   # Should be writable by application user
   drwxr-xr-x 2 app-user app-user 4096 Dec 31 18:57 backups

   # Fix: Set correct permissions
   chown -R app-user:app-user /opt/retro/config/backups/
   chmod 755 /opt/retro/config/backups/
   ```

3. **First run - no changes yet**:
   ```
   Backups only created when:
   - Config modified (hasn't happened yet)
   - Migration runs (config already at current version)

   Solution: Make a config change via UI to trigger backup
   ```

### Problem 3: "Too many backups filling disk"

**Symptom**: Backup directory growing too large

**Diagnosis**:
```bash
# Check backup count
ls -1 /opt/retro/config/backups/ | wc -l

# Check disk usage
du -sh /opt/retro/config/backups/

# Check retention policy
grep MAX_BACKUPS_PER_FILE /opt/retro/backend/app/core/config_backup.py
# Should show: MAX_BACKUPS_PER_FILE = 10
```

**Possible Causes**:

1. **Multiple config files with separate limits**:
   ```bash
   # Each file type gets 10 backups
   ls /opt/retro/config/backups/ | grep -E '^(default|local|production)' | sort

   # Example:
   # default.v*.json - 10 backups
   # local.v*.json - 10 backups
   # production.v*.json - 10 backups
   # Total: 30 backups (normal!)
   ```

2. **Retention policy not running**:
   ```bash
   # Check logs for cleanup
   grep -i "cleanup" /var/log/photo-restoration/app.log

   # Should see:
   # "Cleaned up X old backups"

   # If not cleaning up, check for errors
   grep -i "error.*cleanup" /var/log/photo-restoration/app.log
   ```

3. **Frequent config changes**:
   ```
   If configs change very frequently (multiple times per minute),
   you may see many recent backups. This is normal - retention
   policy will clean up once count exceeds 10 per file.
   ```

**Solution**:
```bash
# Manual cleanup if needed (emergency only)
cd /opt/retro/config/backups/
ls -t local.v*.json | tail -n +11 | xargs rm -f

# But better: Let automatic retention handle it
# Check why automatic cleanup not working
```

### Problem 4: "Config version mismatch error on startup"

**Symptom**: Application fails to start with version error

**Error Message**:
```
ValueError: Configuration version mismatch:
  default.json (1.1.0) != production.json (1.0.0)
```

**Diagnosis**:
```bash
# Check all config versions
for f in /opt/retro/config/*.json; do
    echo "$f: $(jq -r '.config_version' $f)"
done

# Example output:
# default.json: 1.1.0
# production.json: 1.0.0  ← Mismatch!
# local.json: 1.0.0
```

**Cause**:
Config files have different versions, usually after:
- Partial deployment (some files updated, others not)
- Manual editing (version changed in one file only)
- Failed migration (migrated default.json but not others)

**Solution**:
```bash
# Option 1: Run migration manually
python /opt/retro/backend/scripts/migrate_config.py \
    /opt/retro/config/production.json

# Option 2: Restore all configs to matching version
# Find backup with correct version
ls -lt /opt/retro/config/backups/production.v1.0.0*.json | head -1

# Restore
python /opt/retro/backend/scripts/restore_config.py \
    /opt/retro/config/production.json --latest

# Option 3: Copy version from default.json
VERSION=$(jq -r '.config_version' /opt/retro/config/default.json)
jq ".config_version = \"$VERSION\"" /opt/retro/config/production.json > temp.json
mv temp.json /opt/retro/config/production.json

# Restart application
systemctl restart photo-restoration
```

### Problem 5: "Can't restore - backup file corrupted"

**Symptom**: Restore fails with JSON parse error

**Error Message**:
```
ERROR: Invalid JSON in backup file
JSONDecodeError: Expecting property name enclosed in double quotes
```

**Diagnosis**:
```bash
# Try to parse backup
jq . /opt/retro/config/backups/local.v1.0.0.20251231_180000_123456.json

# If corrupted, shows:
# parse error: Invalid numeric literal at line 42, column 15
```

**Possible Causes**:
- Disk corruption
- Interrupted write operation
- Manual editing gone wrong

**Solution**:
```bash
# Option 1: Try next-most-recent backup
ls -lt /opt/retro/config/backups/local.v*.json

# Option 2: Recover from external backup
cp /backup/photo-restoration/configs/2025-12-30/local.json \
   /opt/retro/config/local.json

# Option 3: Reconstruct from logs if available
# (Last resort - requires analyzing application logs for config state)

# Prevention:
# - Ensure regular external backups
# - Monitor disk health
# - Use file integrity monitoring
```

### Problem 6: "Backup timestamp doesn't match actual time"

**Symptom**: Backup filename shows wrong timestamp

**Example**:
```bash
# Created backup at 3:00 PM local time (Dec 31)
# But filename shows:
local.v1.0.0.20251231_230000_123456.json
                      ^^ 23:00 = 11 PM!
```

**Cause**:
**Timestamps are in UTC**, not local time.

**Diagnosis**:
```bash
# Check server timezone
timedatectl

# Check if timestamps are UTC
TZ=UTC date
# Compare to backup timestamp
```

**Solution**:
This is **correct behavior**. Timestamps are stored in UTC for consistency across deployments.

**Conversion**:
```bash
# Convert UTC to local time
# If backup shows: 20251231_230000
# And server is EST (UTC-5):
# 23:00 UTC = 18:00 EST (6:00 PM local)

# Verify:
date -d "2025-12-31 23:00:00 UTC"
# Shows local time equivalent
```

### Problem 7: "Migration never runs automatically"

**Symptom**: Config stays at old version even after app upgrade

**Diagnosis**:
```bash
# Check current version
jq -r '.config_version' /opt/retro/config/local.json
# Shows: 1.0.0

# Check application requires version
grep CURRENT_CONFIG_VERSION /opt/retro/backend/app/core/config.py
# Shows: CURRENT_CONFIG_VERSION = "1.1.0"

# Check if migration exists
grep "Migration_1_0_to_1_1" /opt/retro/backend/app/core/config_migrations.py
# Should show migration class

# Check logs
grep -i "migration" /var/log/photo-restoration/app.log
```

**Possible Causes**:

1. **Auto-migration disabled**:
   ```bash
   grep CONFIG_AUTO_MIGRATE /opt/retro/.env
   # If shows: CONFIG_AUTO_MIGRATE=false

   # Fix:
   echo "CONFIG_AUTO_MIGRATE=true" >> /opt/retro/.env
   systemctl restart photo-restoration
   ```

2. **Application hasn't restarted since upgrade**:
   ```bash
   # Migrations run on startup
   # Check last restart
   systemctl status photo-restoration

   # Restart to trigger migration
   systemctl restart photo-restoration
   ```

3. **Migration registry not updated**:
   ```python
   # Check in config_migrations.py
   MIGRATIONS = {
       "0.9.0->1.0.0": Migration_0_9_to_1_0(),
       # Missing: "1.0.0->1.1.0": Migration_1_0_to_1_1(),
   }

   # Fix: Add to registry
   ```

**Solution**:
```bash
# Option 1: Enable auto-migration and restart
CONFIG_AUTO_MIGRATE=true systemctl restart photo-restoration

# Option 2: Run migration manually
python /opt/retro/backend/scripts/migrate_config.py \
    /opt/retro/config/local.json

# Verify
jq -r '.config_version' /opt/retro/config/local.json
# Should show: 1.1.0
```

---

## Quick Reference Card

### Config Version

| Aspect | Details |
|--------|---------|
| **What** | Schema version (semantic versioning) |
| **Format** | `MAJOR.MINOR.PATCH` (e.g., `1.0.0`) |
| **Location** | `config_version` field in JSON |
| **Changes when** | Schema structure changes |
| **Frequency** | Rarely (months/years) |
| **Controlled by** | Developers via migrations |

### Backup Timestamps

| Aspect | Details |
|--------|---------|
| **What** | Change history tracking |
| **Format** | `YYYYMMDD_HHMMSS_microseconds` |
| **Location** | Backup filename |
| **Changes when** | Every config save/delete |
| **Frequency** | Often (as needed) |
| **Controlled by** | Automatic system |

### Common Commands

```bash
# Check config version
jq -r '.config_version' /opt/retro/config/local.json

# List backups
ls -lt /opt/retro/config/backups/

# Count backups per file
ls -1 /opt/retro/config/backups/ | grep '^local' | wc -l

# Restore latest backup
python scripts/restore_config.py config/local.json --latest

# Migrate config manually
python scripts/migrate_config.py config/local.json

# Check backup disk usage
du -sh /opt/retro/config/backups/
```

### Decision Tree: Is This Normal?

```
Config changed via UI, version didn't increase?
  ├─ Data changed (model values)? → ✅ NORMAL
  ├─ Backup created? → ✅ NORMAL
  └─ Version changed? → ❌ UNEXPECTED (schema shouldn't change from UI)

Deployed new app version, config version increased?
  ├─ Migration ran? → ✅ NORMAL
  ├─ Backup created? → ✅ NORMAL
  └─ Version didn't change? → ⚠️ Check: auto-migration enabled?

Many backups in directory?
  ├─ Multiple config files × 10 each? → ✅ NORMAL
  ├─ Same file > 10 backups? → ⚠️ Check: retention policy working?
  └─ Disk space ok? → ✅ NORMAL

No backups created?
  ├─ First run? → ✅ NORMAL (no changes yet)
  ├─ Auto-migration disabled? → ⚠️ Enable it
  └─ Permission errors? → ⚠️ Fix permissions
```

---

## Conclusion

The Photo Restoration API's configuration versioning system uses a **dual-tracking approach**:

1. **Schema Versioning** (`config_version`) tracks structural evolution
2. **Backup Timestamps** track every individual change

Understanding this distinction is key to:
- ✅ Correctly interpreting backup filenames
- ✅ Knowing when to expect version changes
- ✅ Effectively using restore capabilities
- ✅ Troubleshooting configuration issues

**Remember**:
- Version changes are **rare** (schema evolution)
- Backups are **frequent** (change tracking)
- Both systems work **together** for complete config management

For questions or issues not covered in this document, consult:
- `docs/CONFIG_VERSIONING_TEST_COVERAGE.md` - Test documentation
- `docs/CONFIG_VERSIONING_PERFORMANCE.md` - Performance characteristics
- `backend/app/core/config_migrations.py` - Migration implementations
- `backend/scripts/` - Management scripts

---

**Document Changelog:**

- **1.0** (2025-12-31): Initial version documenting versioning principles
