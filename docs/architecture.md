# ExtractAI Architecture (Phase 1.1)

This document summarizes the approved platform architecture. Implementation follows the phased roadmap in the root README.

## Positioning

ExtractAI is an **Intelligent Web Data Extraction Platform**, not a simple scraper. Every job:

1. Builds a `WebsiteProfile` (Website Intelligence Engine)
2. Runs Discovery (APIs, GraphQL, RSS, sitemaps, metadata, …)
3. Scores strategies via the Strategy Engine
4. Executes plugins → Normalization → Validation
5. Persists versioned outputs, network captures, and snapshots

## Core planes

- **Intelligence:** `website_intelligence/`, `discovery/`
- **Execution:** `strategy/`, `plugins/`, `network/`, `snapshots/`
- **Quality:** `normalization/`, `validation/`
- **Platform:** `services/`, `storage/`, `observability/`, `extractors/`

## Version pins (every job)

`pipeline_version`, `strategy_version`, `plugin_set_version`, `schema_version`, `profile_version`, `discovery_version`

## Future AI

`LLMExtractionEngine`, Agent Engine, Planner/Extraction/Validation/Research/Browser agents plug into existing Strategy + Plugin + ExtractionEngine interfaces — no rewrites.

## Database (extended)

users, refresh_tokens, guest_sessions, jobs, job_events, extracted_data, exports, api_keys, user_settings, website_profiles, strategy_decisions, pipeline_logs, network_requests, snapshots, performance_metrics, plugin_registry, pipeline_versions
