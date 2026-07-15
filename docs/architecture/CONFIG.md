# JBK OS

# Configuration System

---

## Directory

JBK-OS/config/

---

# Purpose

The Configuration System centralizes all configurable settings used by JBK OS.

No production component shall rely on hard-coded paths or environment-specific constants.

---

# Configuration Files

company.yaml

paths.yaml

runtime.yaml

logging.yaml

skills.yaml

executives.yaml

---

# company.yaml

Contains:

* Company name
* Version
* Timezone
* CEO
* Country

---

# paths.yaml

Contains:

* JBK Root
* Company directory
* Brain directory
* Skills directory
* Projects directory
* Data directory
* Workspace directory

---

# runtime.yaml

Contains:

* Environment
* Debug mode
* Health check intervals
* Briefing schedule
* Cache policy

---

# logging.yaml

Contains:

* Log level
* Log location
* Rotation policy
* Console output
* File output

---

# skills.yaml

Contains:

* Default execution engine
* Skill discovery directories
* Skill validation rules

---

# executives.yaml

Contains:

* Executive startup settings
* Availability defaults
* Notification preferences
* Workspace preferences

---

# Architectural Rules

Configuration files:

* contain data only.
* contain no executable code.
* are loaded only during startup.
* may be reloaded by future runtime services.

---

# Planned Enhancements (Version 2+)

* Multiple environments.
* Secure secrets management.
* Configuration validation.
* Live configuration reload.
* Cloud configuration providers.

---

# Related Documents

Bootstrap Architecture

Runtime Architecture

BOOT_SEQUENCE.md
