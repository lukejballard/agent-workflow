#!/usr/bin/env python3
"""Refresh and validate canonical agent-platform metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

EXPECTED_ARTIFACT_PATHS = {
    "repoMap": ".github/agent-platform/repo-map.json",
    "skillRegistry": ".github/agent-platform/skill-registry.json",
    "contextPacketSchema": ".github/agent-platform/context-packet.schema.json",
    "runArtifactSchema": ".github/agent-platform/run-artifact-schema.json",
}

TOP_LEVEL_AREAS = [
    {
        "path": ".github/",
        "role": "Agent workflow, prompts, skills, hooks, and CI governance",
        "guide": "AGENTS.md",
    },
    {
        "path": "src/",
        "role": "Backend or shared application code when present",
        "guide": "src/AGENTS.md",
    },
    {
        "path": "frontend/",
        "role": "React + TypeScript + Vite dashboard",
        "guide": "frontend/AGENTS.md",
    },
    {
        "path": "tests/",
        "role": "Python unit and integration tests",
        "guide": "tests/AGENTS.md",
    },
    {
        "path": "docs/",
        "role": "Architecture, setup, specs, and contributor runbooks",
        "guide": "docs/AGENTS.md",
    },
    {
        "path": "deploy/",
        "role": "Deployment manifests and operational assets",
        "guide": "AGENTS.md",
    },
    {
        "path": "openspec/",
        "role": "Brownfield change proposals",
        "guide": "AGENTS.md",
    },
    {
        "path": ".specify/",
        "role": "Greenfield planning artifacts",
        "guide": "AGENTS.md",
    },
]

DOMAIN_SURFACES = [
    {
        "path": "src/",
        "kind": "backend",
        "guide": "src/AGENTS.md",
        "instructions": [
            ".github/instructions/python.instructions.md",
            ".github/instructions/api.instructions.md",
            ".github/instructions/database.instructions.md",
            ".github/instructions/security.instructions.md",
            ".github/instructions/performance.instructions.md",
        ],
        "tests": ["tests/"],
        "knownSubpaths": {
            "src/api/": "Route or handler modules if present",
            "src/services/": "Service or orchestration modules if present",
            "src/storage/": "Storage or repository helpers if present",
            "src/analysis/": "Pure analysis or transformation modules if present",
            "src/models/": "Shared request, response, or domain models if present",
            "src/config/": "Environment-driven configuration if present",
        },
        "highRiskPaths": [
            "src/api/",
            "src/services/",
            "src/storage/",
        ],
        "notes": [
            "Route and handler modules should stay thin.",
            "Analysis code should stay pure and free of database I/O.",
            "Do not document runtime surfaces that are not present in the workspace.",
        ],
    },
    {
        "path": "frontend/",
        "kind": "frontend",
        "guide": "frontend/AGENTS.md",
        "instructions": [
            ".github/instructions/react.instructions.md",
            ".github/instructions/typescript.instructions.md",
            ".github/instructions/accessibility.instructions.md",
            ".github/instructions/security.instructions.md",
            ".github/instructions/performance.instructions.md",
        ],
        "tests": ["frontend/src/__tests__/", "frontend/tests/"],
        "observedBasePath": "frontend/src/",
        "knownSubpaths": {
            "frontend/src/api/": "Typed API helpers",
            "frontend/src/components/": "Shared and reusable UI components",
            "frontend/src/context/": "React context providers",
            "frontend/src/hooks/": "Custom hooks for data loading and derived state",
            "frontend/src/pages/": "Top-level page components mounted by the router",
            "frontend/src/types/": "Shared TypeScript interfaces mirroring API responses",
            "frontend/src/__tests__/": "Vitest unit and component tests",
        },
        "highRiskPaths": [
            "frontend/src/pages/",
            "frontend/src/api/",
            "frontend/src/components/",
        ],
        "notes": [
            "No direct fetch() belongs in pages or components.",
            "Pages should stay thin and business logic should live in hooks, context, or API helpers.",
            "Accessibility review remains required for user-facing UI changes.",
        ],
    },
    {
        "path": "tests/",
        "kind": "tests",
        "guide": "tests/AGENTS.md",
        "instructions": [".github/instructions/testing.instructions.md"],
        "highRiskPaths": ["tests/integration/"],
        "notes": [
            "Unit tests should stay isolated from external I/O.",
            "Integration tests that require live services should be marked explicitly.",
        ],
    },
    {
        "path": "docs/",
        "kind": "docs",
        "guide": "docs/AGENTS.md",
        "instructions": [],
        "highRiskPaths": ["docs/specs/active/", "docs/runbooks/"],
        "notes": [
            "Workflow and contributor docs should update in the same change set as workflow metadata.",
            "Do not invent behavior that is not confirmed by code or repo metadata.",
        ],
    },
    {
        "path": ".github/",
        "kind": "agent-platform",
        "guide": "AGENTS.md",
        "instructions": [],
        "highRiskPaths": [
            ".github/agents/",
            ".github/prompts/",
            ".github/skills/",
            ".github/hooks/",
            ".github/workflows/",
            ".github/agent-platform/",
        ],
        "notes": [
            "Keep workflow-manifest.json, repo-map.json, and skill-registry.json aligned.",
            "Workflow or skill changes should update docs/runbooks/agent-mode.md and docs/copilot-setup.md.",
        ],
    },
]

SKILL_NAME_OVERRIDES = {
    "adr": "ADR",
    "visual-qa": "Visual QA",
}

RUN_ARTIFACT_TASK_CLASSES = {
    "trivial",
    "research-only",
    "review-only",
    "brownfield-improvement",
    "greenfield-feature",
    "implement-from-existing-spec",
    "test-only",
    "docs-only",
}
RUN_ARTIFACT_STATUSES = {"in-progress", "blocked", "review-needed", "done"}
VERIFICATION_STATUSES = {"passed", "failed", "not-run", "advisory"}
RUN_ARTIFACT_ALLOWED_FIELDS = {
    "schemaVersion",
    "runId",
    "createdAtUtc",
    "taskClass",
    "objective",
    "linkedSpec",
    "linkedResearch",
    "status",
    "confidence",
    "summary",
    "assumptions",
    "touchedPaths",
    "artifacts",
    "evidence",
    "taskLedger",
    "verification",
    "residualRisks",
}
RUN_ARTIFACT_ARTIFACT_FIELDS = {"kind", "path", "notes"}
RUN_ARTIFACT_EVIDENCE_FIELDS = {"kind", "summary", "source", "timestampUtc"}
RUN_ARTIFACT_VERIFICATION_FIELDS = {"kind", "status", "details"}
RUN_ARTIFACT_TASK_LEDGER_FIELDS = {
    "taskId",
    "route",
    "tokensIn",
    "tokensOut",
    "contextSizeKb",
    "contextUtilizationPct",
    "completionStatus",
    "notes",
}
TASK_LEDGER_STATUSES = {"done", "blocked", "failed", "skipped", "in-progress"}
CONTEXT_PACKET_ALLOWED_FIELDS = {
    "schemaVersion",
    "classification",
    "goal",
    "constraints",
    "completed_steps",
    "current_step",
    "current_phase",
    "task_graph",
    "available_tools",
    "working_memory",
    "episodic_memory",
    "semantic_memory",
    "run_artifact",
    "context_health",
    "self_check",
    "allowed_paths",
}
CONTEXT_PACKET_RUN_ARTIFACT_FIELDS = {
    "mode",
    "path",
    "task_ledger_policy",
    "last_recorded_task_id",
}
CONTEXT_PACKET_LOADED_MEMORY_FIELDS = {"scope", "source", "summary", "applied_tasks"}
CONTEXT_HEALTH_STATUSES = {"ok", "trim", "compress", "over-budget"}
SPEC_PATTERN = re.compile(
    r"^(docs/specs/(active|done)/[A-Za-z0-9._/-]+\.md|\[no-spec\])$"
)
RESEARCH_PATTERN = re.compile(r"^docs/specs/research/[A-Za-z0-9._/-]+\.md$")


class AgentPlatformValidationError(Exception):
    """Raised when agent-platform metadata does not validate."""


def repo_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2) + "\n"


def rel_dir(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix().rstrip("/") + "/"


def existing_relative_file(repo_root: Path, relative_path: str) -> bool:
    return (repo_root / relative_path).exists()


def child_directories(repo_root: Path, relative_path: str) -> list[str]:
    base_path = repo_root / relative_path.rstrip("/")
    if not base_path.exists():
        return []
    ignored_names = {"__pycache__", "node_modules", "dist", "build"}
    return sorted(
        rel_dir(repo_root, child)
        for child in base_path.iterdir()
        if child.is_dir()
        and child.name not in ignored_names
        and not child.name.startswith(".")
    )


def load_make_targets(repo_root: Path) -> set[str]:
    makefile_path = repo_root / "Makefile"
    if not makefile_path.exists():
        return set()
    targets: set[str] = set()
    target_pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    for line in makefile_path.read_text(encoding="utf-8").splitlines():
        match = target_pattern.match(line)
        if match:
            targets.add(match.group(1))
    return targets


def load_frontend_scripts(repo_root: Path) -> set[str]:
    package_json_path = repo_root / "frontend" / "package.json"
    if not package_json_path.exists():
        return set()
    package_data = load_json(package_json_path)
    scripts = package_data.get("scripts", {})
    if not isinstance(scripts, dict):
        return set()
    return {str(key) for key in scripts}


def humanize_skill_name(skill_id: str) -> str:
    if skill_id in SKILL_NAME_OVERRIDES:
        return SKILL_NAME_OVERRIDES[skill_id]
    words = []
    for token in skill_id.split("-"):
        if token == "qa":
            words.append("QA")
        else:
            words.append(token.capitalize())
    return " ".join(words)


def build_skill_registry(
    repo_root: Path, workflow_manifest: dict[str, Any]
) -> dict[str, Any]:
    manifest_skills = workflow_manifest.get("skills", {})
    if not isinstance(manifest_skills, dict):
        raise AgentPlatformValidationError(
            "workflow-manifest.json is missing a valid skills map"
        )

    skill_dir = repo_root / ".github" / "skills"
    github_skill_ids = sorted(
        child.name
        for child in skill_dir.iterdir()
        if child.is_dir() and (child / "SKILL.md").exists()
    )
    manifest_skill_ids = set(manifest_skills.keys())
    # All .github/skills/ directories must be covered by the manifest.
    # Additional entries (e.g. from root skills/) are allowed.
    missing_from_manifest = sorted(set(github_skill_ids) - manifest_skill_ids)
    if missing_from_manifest:
        raise AgentPlatformValidationError(
            "workflow-manifest.json is missing skill entries that exist in "
            f".github/skills/: {', '.join(missing_from_manifest)}"
        )

    registry_skills: list[dict[str, Any]] = []
    trigger_index: dict[str, list[str]] = {}

    for skill_id, metadata in manifest_skills.items():
        if not isinstance(metadata, dict):
            raise AgentPlatformValidationError(
                f"workflow manifest entry for {skill_id} must be an object"
            )
        path_value = metadata.get("path")
        triggers_value = metadata.get("triggers", [])
        if not isinstance(path_value, str) or not path_value:
            raise AgentPlatformValidationError(
                f"workflow manifest entry for {skill_id} is missing a valid path"
            )
        if not existing_relative_file(repo_root, path_value):
            raise AgentPlatformValidationError(
                f"manifest references missing skill file: {path_value}"
            )
        if not isinstance(triggers_value, list) or not all(
            isinstance(item, str) for item in triggers_value
        ):
            raise AgentPlatformValidationError(
                f"workflow manifest triggers for {skill_id} must be a list of strings"
            )

        registry_skills.append(
            {
                "id": skill_id,
                "displayName": humanize_skill_name(skill_id),
                "path": path_value,
                "artifactType": "skill-markdown",
                "triggerTags": list(triggers_value),
            }
        )
        for trigger in triggers_value:
            trigger_index.setdefault(trigger, []).append(skill_id)

    return {
        "version": 1,
        "canonical": True,
        "description": "Canonical inventory of agent-discoverable skills and their trigger tags. This registry mirrors workflow-manifest.json for skill discovery and coverage review.",
        "sourceManifest": ".github/agent-platform/workflow-manifest.json",
        "skills": registry_skills,
        "triggerIndex": trigger_index,
    }


def build_domain_surface(
    repo_root: Path, metadata: dict[str, Any]
) -> dict[str, Any] | None:
    base_path = repo_root / metadata["path"].rstrip("/")
    if not base_path.exists():
        return None

    result: dict[str, Any] = {
        "path": metadata["path"],
        "kind": metadata["kind"],
        "guide": metadata["guide"],
        "instructions": metadata["instructions"],
        "highRiskPaths": metadata["highRiskPaths"],
        "notes": metadata["notes"],
    }

    tests_value = metadata.get("tests")
    if tests_value:
        result["tests"] = tests_value

    known_subpaths: list[dict[str, str]] = []
    known_subpath_map: dict[str, str] = metadata.get("knownSubpaths", {})
    for path_value, role in known_subpath_map.items():
        if existing_relative_file(repo_root, path_value.rstrip("/")):
            known_subpaths.append({"path": path_value, "role": role})
    if known_subpaths:
        result["knownSubpaths"] = known_subpaths

    if known_subpath_map:
        known_paths = set(known_subpath_map.keys())
        observed_base_path = str(metadata.get("observedBasePath", metadata["path"]))
        observed_paths = [
            item
            for item in child_directories(repo_root, observed_base_path)
            if item not in known_paths
        ]
        if observed_paths:
            result["observedAdditionalPaths"] = observed_paths

    return result


def build_backend_verification_routes(repo_root: Path) -> list[str]:
    routes: list[str] = []
    # Dynamic routes derived from discovered test layout
    if existing_relative_file(repo_root, "tests/unit") or existing_relative_file(
        repo_root, "tests/integration"
    ):
        routes.append("pytest tests/ -v")
    if existing_relative_file(repo_root, "tests/unit"):
        routes.append(
            "pytest tests/unit/ --cov=src --cov-report=term-missing"
        )
    # Static fallback routes: always applicable when src/ is present
    if existing_relative_file(repo_root, "src"):
        routes.append("ruff check src/")
        routes.append("python -m mypy src/")
    return routes


def build_frontend_verification_routes(repo_root: Path) -> list[str]:
    routes: list[str] = []
    # Only include npm routes when frontend/package.json actually exists;
    # the frontend/ dir may be a scaffold-only placeholder.
    package_json = repo_root / "frontend" / "package.json"
    if not package_json.is_file():
        return routes
    scripts = load_frontend_scripts(repo_root)
    for script_name in ("lint", "typecheck", "test", "test:e2e"):
        if script_name in scripts:
            routes.append(f"cd frontend && npm run {script_name}")
    return routes


def build_contract_verification_routes(repo_root: Path) -> list[str]:
    routes: list[str] = []
    make_targets = load_make_targets(repo_root)
    for target_name in ("validate-specs", "test-contract"):
        if target_name in make_targets:
            routes.append(f"make {target_name}")
    # Static fallback: schema validation is always available
    if not routes and existing_relative_file(repo_root, ".github/agent-platform"):
        routes.append(
            "python scripts/agent/sync_agent_platform.py --check"
        )
    return routes


def build_repo_map(
    repo_root: Path, workflow_manifest: dict[str, Any]
) -> dict[str, Any]:
    top_level_areas = [
        item
        for item in TOP_LEVEL_AREAS
        if existing_relative_file(repo_root, item["path"].rstrip("/"))
    ]
    domain_surfaces = [
        surface
        for surface in (
            build_domain_surface(repo_root, item) for item in DOMAIN_SURFACES
        )
        if surface
    ]

    backend_routes = build_backend_verification_routes(repo_root)
    frontend_routes = build_frontend_verification_routes(repo_root)
    contract_routes = build_contract_verification_routes(repo_root)
    sensitive_paths = workflow_manifest.get("approval", {}).get("sensitivePaths", [])
    if not isinstance(sensitive_paths, list):
        sensitive_paths = []

    return {
        "version": 1,
        "canonical": True,
        "description": "Canonical repository topology, scoped-guide, and verification metadata for large-codebase agent work.",
        "repository": {
            "name": "agent-workflow",
            "summary": "Reusable repository scaffold for agent-driven software delivery with docs, workflow metadata, helper scripts, and optional runtime areas.",
        },
        "defaultReadOrder": [
            "AGENTS.md",
            ".github/copilot-instructions.md",
            ".github/agent-platform/workflow-manifest.json",
            ".github/agent-platform/repo-map.json",
            ".github/agent-platform/skill-registry.json",
        ],
        "requirementsSources": [
            "docs/specs/active/",
            "openspec/changes/",
            ".specify/",
            "specs/",
            "plan/",
        ],
        "topLevelAreas": top_level_areas,
        "domainSurfaces": domain_surfaces,
        "changeRouting": [
            {
                "whenPathMatches": ["src/**"],
                "readBeforeEditing": [
                    "AGENTS.md",
                    "src/AGENTS.md",
                    ".github/agent-platform/repo-map.json",
                ],
                "verifyWith": backend_routes,
            },
            {
                "whenPathMatches": ["frontend/**"],
                "readBeforeEditing": [
                    "AGENTS.md",
                    "frontend/AGENTS.md",
                    ".github/agent-platform/repo-map.json",
                ],
                "verifyWith": [
                    route for route in frontend_routes if not route.endswith("test:e2e")
                ],
            },
            {
                "whenPathMatches": ["tests/**"],
                "readBeforeEditing": [
                    "AGENTS.md",
                    "tests/AGENTS.md",
                    ".github/agent-platform/repo-map.json",
                ],
                "verifyWith": backend_routes,
            },
            {
                "whenPathMatches": ["docs/**"],
                "readBeforeEditing": [
                    "AGENTS.md",
                    "docs/AGENTS.md",
                    ".github/agent-platform/repo-map.json",
                ],
                "verifyWith": [],
            },
            {
                "whenPathMatches": [".github/**", "scripts/agent/**"],
                "readBeforeEditing": [
                    "AGENTS.md",
                    ".github/agent-platform/workflow-manifest.json",
                    ".github/agent-platform/repo-map.json",
                    ".github/agent-platform/skill-registry.json",
                ],
                "verifyWith": ["python scripts/agent/sync_agent_platform.py --check"],
            },
        ],
        "verificationRoutes": {
            "backend": backend_routes,
            "frontend": frontend_routes,
            "contracts": contract_routes,
            "agentPlatform": ["python scripts/agent/sync_agent_platform.py --check"],
        },
        "sensitiveSurfaces": sensitive_paths,
    }


def validate_iso_datetime(value: Any, field_name: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field_name} must be an ISO-8601 timestamp")


def validate_string_list(
    value: Any, field_name: str, errors: list[str], *, unique: bool = False
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return []
    if not all(isinstance(item, str) and item for item in value):
        errors.append(f"{field_name} must contain non-empty strings")
        return []
    if unique and len(value) != len(set(value)):
        errors.append(f"{field_name} must not contain duplicates")
    return list(value)


def validate_run_artifact_instance(
    repo_root: Path, artifact_path: Path, artifact: Any
) -> list[str]:
    errors: list[str] = []
    label = artifact_path.relative_to(repo_root).as_posix()
    if not isinstance(artifact, dict):
        return [f"{label} must contain a JSON object"]

    unknown_fields = sorted(set(artifact.keys()) - RUN_ARTIFACT_ALLOWED_FIELDS)
    if unknown_fields:
        errors.append(f"{label} contains unknown fields: {', '.join(unknown_fields)}")

    required_fields = {
        "schemaVersion",
        "taskClass",
        "objective",
        "status",
        "summary",
        "touchedPaths",
        "verification",
        "residualRisks",
    }
    missing_fields = sorted(field for field in required_fields if field not in artifact)
    if missing_fields:
        errors.append(
            f"{label} is missing required fields: {', '.join(missing_fields)}"
        )
        return errors

    if artifact.get("schemaVersion") != 1:
        errors.append(f"{label} schemaVersion must equal 1")
    if artifact.get("taskClass") not in RUN_ARTIFACT_TASK_CLASSES:
        errors.append(f"{label} taskClass is invalid")
    if (
        not isinstance(artifact.get("objective"), str)
        or not artifact["objective"].strip()
    ):
        errors.append(f"{label} objective must be a non-empty string")
    if artifact.get("status") not in RUN_ARTIFACT_STATUSES:
        errors.append(f"{label} status is invalid")
    if not isinstance(artifact.get("summary"), str) or not artifact["summary"].strip():
        errors.append(f"{label} summary must be a non-empty string")

    if "runId" in artifact and (
        not isinstance(artifact["runId"], str) or not artifact["runId"].strip()
    ):
        errors.append(f"{label} runId must be a non-empty string when provided")
    if "createdAtUtc" in artifact:
        validate_iso_datetime(artifact["createdAtUtc"], f"{label} createdAtUtc", errors)

    linked_spec = artifact.get("linkedSpec")
    if linked_spec is not None:
        if not isinstance(linked_spec, str) or not SPEC_PATTERN.match(linked_spec):
            errors.append(
                f"{label} linkedSpec must reference an active or done spec path or [no-spec]"
            )
        elif linked_spec != "[no-spec]" and not existing_relative_file(
            repo_root, linked_spec
        ):
            errors.append(
                f"{label} linkedSpec does not exist in the repo: {linked_spec}"
            )

    linked_research = artifact.get("linkedResearch")
    if linked_research is not None:
        values = validate_string_list(
            linked_research, f"{label} linkedResearch", errors, unique=True
        )
        for value in values:
            if not RESEARCH_PATTERN.match(value):
                errors.append(
                    f"{label} linkedResearch contains an invalid path: {value}"
                )
            elif not existing_relative_file(repo_root, value):
                errors.append(f"{label} linkedResearch path does not exist: {value}")

    if "assumptions" in artifact:
        validate_string_list(artifact["assumptions"], f"{label} assumptions", errors)

    touched_paths = validate_string_list(
        artifact.get("touchedPaths"), f"{label} touchedPaths", errors, unique=True
    )
    for value in touched_paths:
        if not existing_relative_file(repo_root, value):
            errors.append(f"{label} touchedPaths entry does not exist: {value}")

    artifact_entries = artifact.get("artifacts", [])
    if not isinstance(artifact_entries, list):
        errors.append(f"{label} artifacts must be a list when provided")
    else:
        for index, entry in enumerate(artifact_entries):
            if not isinstance(entry, dict):
                errors.append(f"{label} artifacts[{index}] must be an object")
                continue
            unknown_entry_fields = sorted(
                set(entry.keys()) - RUN_ARTIFACT_ARTIFACT_FIELDS
            )
            if unknown_entry_fields:
                errors.append(
                    f"{label} artifacts[{index}] contains unknown fields: {', '.join(unknown_entry_fields)}"
                )
            kind = entry.get("kind")
            path_value = entry.get("path")
            if not isinstance(kind, str) or not kind:
                errors.append(
                    f"{label} artifacts[{index}].kind must be a non-empty string"
                )
            if not isinstance(path_value, str) or not path_value:
                errors.append(
                    f"{label} artifacts[{index}].path must be a non-empty string"
                )
            elif not existing_relative_file(repo_root, path_value):
                errors.append(
                    f"{label} artifacts[{index}].path does not exist: {path_value}"
                )
            notes = entry.get("notes")
            if notes is not None and not isinstance(notes, str):
                errors.append(
                    f"{label} artifacts[{index}].notes must be a string when provided"
                )

    evidence_entries = artifact.get("evidence", [])
    if not isinstance(evidence_entries, list):
        errors.append(f"{label} evidence must be a list when provided")
    else:
        for index, entry in enumerate(evidence_entries):
            if not isinstance(entry, dict):
                errors.append(f"{label} evidence[{index}] must be an object")
                continue
            unknown_entry_fields = sorted(
                set(entry.keys()) - RUN_ARTIFACT_EVIDENCE_FIELDS
            )
            if unknown_entry_fields:
                errors.append(
                    f"{label} evidence[{index}] contains unknown fields: {', '.join(unknown_entry_fields)}"
                )
            for key in ("kind", "summary", "source"):
                value = entry.get(key)
                if not isinstance(value, str) or not value:
                    errors.append(
                        f"{label} evidence[{index}].{key} must be a non-empty string"
                    )
            if "timestampUtc" in entry:
                validate_iso_datetime(
                    entry["timestampUtc"],
                    f"{label} evidence[{index}].timestampUtc",
                    errors,
                )

    validate_task_ledger_entries(artifact.get("taskLedger"), label, errors)

    verification_entries = artifact.get("verification")
    if not isinstance(verification_entries, list) or not verification_entries:
        errors.append(f"{label} verification must be a non-empty list")
    else:
        for index, entry in enumerate(verification_entries):
            if not isinstance(entry, dict):
                errors.append(f"{label} verification[{index}] must be an object")
                continue
            unknown_entry_fields = sorted(
                set(entry.keys()) - RUN_ARTIFACT_VERIFICATION_FIELDS
            )
            if unknown_entry_fields:
                errors.append(
                    f"{label} verification[{index}] contains unknown fields: {', '.join(unknown_entry_fields)}"
                )
            kind = entry.get("kind")
            status = entry.get("status")
            details = entry.get("details")
            if not isinstance(kind, str) or not kind:
                errors.append(
                    f"{label} verification[{index}].kind must be a non-empty string"
                )
            if status not in VERIFICATION_STATUSES:
                errors.append(f"{label} verification[{index}].status is invalid")
            if not isinstance(details, str) or not details:
                errors.append(
                    f"{label} verification[{index}].details must be a non-empty string"
                )

    validate_string_list(
        artifact.get("residualRisks"), f"{label} residualRisks", errors
    )
    return errors


def validate_task_ledger_entries(value: Any, label: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{label} taskLedger must be a list when provided")
        return

    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            errors.append(f"{label} taskLedger[{index}] must be an object")
            continue
        unknown_fields = sorted(set(entry.keys()) - RUN_ARTIFACT_TASK_LEDGER_FIELDS)
        if unknown_fields:
            errors.append(
                f"{label} taskLedger[{index}] contains unknown fields: {', '.join(unknown_fields)}"
            )
        task_id = entry.get("taskId")
        completion_status = entry.get("completionStatus")
        if not isinstance(task_id, str) or not task_id:
            errors.append(
                f"{label} taskLedger[{index}].taskId must be a non-empty string"
            )
        if completion_status not in TASK_LEDGER_STATUSES:
            errors.append(f"{label} taskLedger[{index}].completionStatus is invalid")
        validate_optional_number(
            entry.get("tokensIn"),
            f"{label} taskLedger[{index}].tokensIn",
            errors,
            integer=True,
        )
        validate_optional_number(
            entry.get("tokensOut"),
            f"{label} taskLedger[{index}].tokensOut",
            errors,
            integer=True,
        )
        validate_optional_number(
            entry.get("contextSizeKb"),
            f"{label} taskLedger[{index}].contextSizeKb",
            errors,
        )
        validate_optional_number(
            entry.get("contextUtilizationPct"),
            f"{label} taskLedger[{index}].contextUtilizationPct",
            errors,
            minimum=0,
            maximum=100,
        )
        for key in ("route", "notes"):
            value = entry.get(key)
            if value is not None and (not isinstance(value, str) or not value):
                errors.append(
                    f"{label} taskLedger[{index}].{key} must be a non-empty string when provided"
                )


def validate_optional_number(
    value: Any,
    field_name: str,
    errors: list[str],
    *,
    integer: bool = False,
    minimum: float | None = 0,
    maximum: float | None = None,
) -> None:
    if value is None:
        return
    valid_type = (
        isinstance(value, int) and not isinstance(value, bool)
        if integer
        else isinstance(value, (int, float))
    )
    if not valid_type:
        errors.append(
            f"{field_name} must be a {'integer' if integer else 'number'} when provided"
        )
        return
    if minimum is not None and value < minimum:
        errors.append(f"{field_name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        errors.append(f"{field_name} must be <= {maximum}")


def validate_context_packet_mapping(
    value: Any, field_name: str, errors: list[str], required_fields: set[str]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{field_name} must be an object")
        return {}
    missing_fields = sorted(field for field in required_fields if field not in value)
    if missing_fields:
        errors.append(
            f"{field_name} is missing required fields: {', '.join(missing_fields)}"
        )
    return value


def validate_context_packet_example(
    repo_root: Path, packet_path: Path, packet: Any
) -> list[str]:
    errors: list[str] = []
    label = packet_path.relative_to(repo_root).as_posix()
    if not isinstance(packet, dict):
        return [f"{label} must contain a JSON object"]

    unknown_fields = sorted(set(packet.keys()) - CONTEXT_PACKET_ALLOWED_FIELDS)
    if unknown_fields:
        errors.append(f"{label} contains unknown fields: {', '.join(unknown_fields)}")

    required_fields = CONTEXT_PACKET_ALLOWED_FIELDS - {"task_graph", "allowed_paths"}
    missing_fields = sorted(field for field in required_fields if field not in packet)
    if missing_fields:
        errors.append(
            f"{label} is missing required fields: {', '.join(missing_fields)}"
        )
        return errors

    if packet.get("schemaVersion") != 2:
        errors.append(f"{label} schemaVersion must equal 2")
    for key in ("classification", "goal", "self_check"):
        value = packet.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label} {key} must be a non-empty string")

    validate_string_list(
        packet.get("constraints"), f"{label} constraints", errors, unique=True
    )
    validate_context_packet_steps(
        packet.get("completed_steps"), f"{label} completed_steps", errors
    )
    validate_context_packet_task(
        packet.get("current_step"),
        f"{label} current_step",
        errors,
        allow_missing_depends_on=True,
    )
    validate_context_packet_tasks(
        packet.get("task_graph"), f"{label} task_graph", errors
    )
    validate_string_list(
        packet.get("available_tools"), f"{label} available_tools", errors, unique=True
    )
    validate_context_packet_memory(
        packet.get("working_memory"), f"{label} working_memory", errors
    )
    validate_context_packet_episode(
        packet.get("episodic_memory"), f"{label} episodic_memory", errors
    )
    validate_context_packet_semantic(
        packet.get("semantic_memory"), f"{label} semantic_memory", errors
    )
    validate_context_packet_run_artifact(
        repo_root, packet.get("run_artifact"), f"{label} run_artifact", errors
    )
    validate_context_packet_health(
        packet.get("context_health"), f"{label} context_health", errors
    )
    return errors


def validate_context_packet_steps(
    value: Any, field_name: str, errors: list[str]
) -> None:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return
    required_fields = {"task_id", "summary", "output", "verification"}
    for index, entry in enumerate(value):
        entry_value = validate_context_packet_mapping(
            entry, f"{field_name}[{index}]", errors, required_fields
        )
        for key in required_fields:
            value = entry_value.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"{field_name}[{index}].{key} must be a non-empty string")


def validate_context_packet_task(
    value: Any,
    field_name: str,
    errors: list[str],
    *,
    allow_missing_depends_on: bool = False,
) -> None:
    required_fields = {
        "task_id",
        "title",
        "input_contract",
        "output_contract",
        "done_condition",
        "route",
    }
    if not allow_missing_depends_on:
        required_fields = required_fields | {"depends_on"}
    entry_value = validate_context_packet_mapping(
        value, field_name, errors, required_fields
    )
    for key in required_fields - {"depends_on"}:
        text = entry_value.get(key)
        if text is not None and (not isinstance(text, str) or not text.strip()):
            errors.append(f"{field_name}.{key} must be a non-empty string")
    depends_on = entry_value.get("depends_on")
    if depends_on is not None:
        validate_string_list(
            depends_on, f"{field_name}.depends_on", errors, unique=True
        )
    if "evidence_refs" in entry_value:
        validate_string_list(
            entry_value.get("evidence_refs"),
            f"{field_name}.evidence_refs",
            errors,
            unique=True,
        )


def validate_context_packet_tasks(
    value: Any, field_name: str, errors: list[str]
) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return
    for index, entry in enumerate(value):
        validate_context_packet_task(entry, f"{field_name}[{index}]", errors)


def validate_context_packet_memory(
    value: Any, field_name: str, errors: list[str]
) -> None:
    entry_value = validate_context_packet_mapping(
        value, field_name, errors, {"focus", "scratchpad", "stale_data_policy"}
    )
    for key in ("focus", "stale_data_policy"):
        text = entry_value.get(key)
        if text is not None and (not isinstance(text, str) or not text.strip()):
            errors.append(f"{field_name}.{key} must be a non-empty string")
    validate_string_list(
        entry_value.get("scratchpad"), f"{field_name}.scratchpad", errors
    )


def validate_context_packet_episode(
    value: Any, field_name: str, errors: list[str]
) -> None:
    entry_value = validate_context_packet_mapping(
        value, field_name, errors, {"episode_summary", "retained_facts"}
    )
    summary = entry_value.get("episode_summary")
    if summary is not None and (not isinstance(summary, str) or not summary.strip()):
        errors.append(f"{field_name}.episode_summary must be a non-empty string")
    validate_string_list(
        entry_value.get("retained_facts"), f"{field_name}.retained_facts", errors
    )


def validate_context_packet_semantic(
    value: Any, field_name: str, errors: list[str]
) -> None:
    entry_value = validate_context_packet_mapping(
        value, field_name, errors, {"retrieval_policy", "scopes"}
    )
    policy = entry_value.get("retrieval_policy")
    if policy is not None and (not isinstance(policy, str) or not policy.strip()):
        errors.append(f"{field_name}.retrieval_policy must be a non-empty string")
    validate_string_list(
        entry_value.get("scopes"), f"{field_name}.scopes", errors, unique=True
    )
    if "retrieval_queries" in entry_value:
        validate_string_list(
            entry_value.get("retrieval_queries"),
            f"{field_name}.retrieval_queries",
            errors,
        )
    loaded_memories = entry_value.get("loaded_memories")
    if loaded_memories is not None:
        validate_context_packet_loaded_memories(
            loaded_memories, f"{field_name}.loaded_memories", errors
        )
    if "deferred_queries" in entry_value:
        validate_string_list(
            entry_value.get("deferred_queries"),
            f"{field_name}.deferred_queries",
            errors,
        )


def validate_context_packet_loaded_memories(
    value: Any, field_name: str, errors: list[str]
) -> None:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return
    for index, entry in enumerate(value):
        entry_value = validate_context_packet_mapping(
            entry,
            f"{field_name}[{index}]",
            errors,
            {"scope", "source", "summary"},
        )
        unknown_fields = sorted(
            set(entry_value.keys()) - CONTEXT_PACKET_LOADED_MEMORY_FIELDS
        )
        if unknown_fields:
            errors.append(
                f"{field_name}[{index}] contains unknown fields: {', '.join(unknown_fields)}"
            )
        for key in ("scope", "source", "summary"):
            text = entry_value.get(key)
            if text is not None and (not isinstance(text, str) or not text.strip()):
                errors.append(f"{field_name}[{index}].{key} must be a non-empty string")
        if "applied_tasks" in entry_value:
            validate_string_list(
                entry_value.get("applied_tasks"),
                f"{field_name}[{index}].applied_tasks",
                errors,
                unique=True,
            )


def validate_context_packet_run_artifact(
    repo_root: Path, value: Any, field_name: str, errors: list[str]
) -> None:
    entry_value = validate_context_packet_mapping(
        value, field_name, errors, {"mode", "task_ledger_policy"}
    )
    unknown_fields = sorted(
        set(entry_value.keys()) - CONTEXT_PACKET_RUN_ARTIFACT_FIELDS
    )
    if unknown_fields:
        errors.append(
            f"{field_name} contains unknown fields: {', '.join(unknown_fields)}"
        )

    mode = entry_value.get("mode")
    if mode not in {"not-needed", "active", "required"}:
        errors.append(f"{field_name}.mode is invalid")

    path_value = entry_value.get("path")
    if path_value is not None:
        if not isinstance(path_value, str) or not path_value.strip():
            errors.append(f"{field_name}.path must be a non-empty string when provided")
        elif not existing_relative_file(repo_root, path_value):
            errors.append(f"{field_name}.path does not exist: {path_value}")
    elif mode in {"active", "required"}:
        errors.append(f"{field_name}.path must be provided when mode is {mode}")

    for key in ("task_ledger_policy", "last_recorded_task_id"):
        text = entry_value.get(key)
        if text is not None and (not isinstance(text, str) or not text.strip()):
            errors.append(
                f"{field_name}.{key} must be a non-empty string when provided"
            )


def validate_context_packet_health(
    value: Any, field_name: str, errors: list[str]
) -> None:
    entry_value = validate_context_packet_mapping(
        value,
        field_name,
        errors,
        {"max_utilization_pct", "trim_strategy", "stale_output_policy"},
    )
    validate_optional_number(
        entry_value.get("max_utilization_pct"),
        f"{field_name}.max_utilization_pct",
        errors,
        minimum=1,
        maximum=100,
    )
    validate_optional_number(
        entry_value.get("current_utilization_pct"),
        f"{field_name}.current_utilization_pct",
        errors,
        minimum=0,
        maximum=100,
    )
    status = entry_value.get("status")
    if status is not None and status not in CONTEXT_HEALTH_STATUSES:
        errors.append(f"{field_name}.status is invalid")
    for key in ("trim_strategy", "stale_output_policy", "last_action"):
        text = entry_value.get(key)
        if text is not None and (not isinstance(text, str) or not text.strip()):
            errors.append(
                f"{field_name}.{key} must be a non-empty string when provided"
            )


def validate_with_optional_jsonschema(
    schema: dict[str, Any], artifact: Any, label: str, errors: list[str]
) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return

    try:
        jsonschema.validate(instance=artifact, schema=schema)
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        errors.append(f"{label} failed jsonschema validation: {exc.message}")


def validate_examples(
    repo_root: Path,
    run_artifact_schema: dict[str, Any],
    context_packet_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    examples_dir = repo_root / ".github" / "agent-platform" / "examples"
    expected_files = [
        examples_dir / "brownfield-run-artifact.json",
        examples_dir / "bugfix-run-artifact.json",
        examples_dir / "review-run-artifact.json",
    ]
    for path in expected_files:
        if not path.exists():
            errors.append(
                f"Missing run-artifact example: {path.relative_to(repo_root).as_posix()}"
            )
            continue
        artifact = load_json(path)
        errors.extend(validate_run_artifact_instance(repo_root, path, artifact))
        validate_with_optional_jsonschema(
            run_artifact_schema,
            artifact,
            path.relative_to(repo_root).as_posix(),
            errors,
        )

    context_packet_files = [
        examples_dir / "context-packet.example.json",
        examples_dir / "brownfield-context-packet.example.json",
    ]
    for context_packet_path in context_packet_files:
        if not context_packet_path.exists():
            errors.append(
                f"Missing context-packet example: {context_packet_path.relative_to(repo_root).as_posix()}"
            )
            continue

        context_packet = load_json(context_packet_path)
        errors.extend(
            validate_context_packet_example(
                repo_root, context_packet_path, context_packet
            )
        )
        validate_with_optional_jsonschema(
            context_packet_schema,
            context_packet,
            context_packet_path.relative_to(repo_root).as_posix(),
            errors,
        )
    return errors


def validate_agent_platform(repo_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = repo_root / ".github" / "agent-platform" / "workflow-manifest.json"
    repo_map_path = repo_root / ".github" / "agent-platform" / "repo-map.json"
    skill_registry_path = (
        repo_root / ".github" / "agent-platform" / "skill-registry.json"
    )
    context_packet_schema_path = (
        repo_root / ".github" / "agent-platform" / "context-packet.schema.json"
    )
    run_artifact_schema_path = (
        repo_root / ".github" / "agent-platform" / "run-artifact-schema.json"
    )

    workflow_manifest = load_json(manifest_path)
    current_repo_map = load_json(repo_map_path)
    current_skill_registry = load_json(skill_registry_path)
    context_packet_schema = load_json(context_packet_schema_path)
    run_artifact_schema = load_json(run_artifact_schema_path)

    artifact_paths = workflow_manifest.get("artifacts", {})
    if artifact_paths != EXPECTED_ARTIFACT_PATHS:
        errors.append(
            "workflow-manifest.json artifacts block does not match the canonical agent-platform file paths"
        )
    else:
        for relative_path in artifact_paths.values():
            if not existing_relative_file(repo_root, relative_path):
                errors.append(
                    f"workflow-manifest.json references a missing artifact: {relative_path}"
                )

    context_engineering = workflow_manifest.get("contextEngineering")
    if not isinstance(context_engineering, dict):
        errors.append(
            "workflow-manifest.json contextEngineering block must be an object"
        )
    else:
        for field_name in (
            "packetSchema",
            "goalAnchorPolicy",
            "memoryTiers",
            "rollingWindow",
            "healthGate",
            "subtaskExecution",
            "ambiguousSubtaskPolicy",
            "observability",
            "memoryHydration",
            "runArtifactPolicy",
        ):
            if field_name not in context_engineering:
                errors.append(
                    f"workflow-manifest.json contextEngineering is missing `{field_name}`"
                )
        if (
            context_engineering.get("packetSchema")
            != EXPECTED_ARTIFACT_PATHS["contextPacketSchema"]
        ):
            errors.append(
                "workflow-manifest.json contextEngineering.packetSchema must match the canonical context packet artifact path"
            )

    try:
        expected_skill_registry = build_skill_registry(repo_root, workflow_manifest)
    except AgentPlatformValidationError as exc:
        errors.append(str(exc))
        expected_skill_registry = None

    try:
        expected_repo_map = build_repo_map(repo_root, workflow_manifest)
    except AgentPlatformValidationError as exc:
        errors.append(str(exc))
        expected_repo_map = None

    if (
        expected_skill_registry is not None
        and current_skill_registry != expected_skill_registry
    ):
        errors.append(
            "skill-registry.json is out of date; run `python scripts/agent/sync_agent_platform.py --write`"
        )

    if expected_repo_map is not None and current_repo_map != expected_repo_map:
        errors.append(
            "repo-map.json is out of date; run `python scripts/agent/sync_agent_platform.py --write`"
        )

    errors.extend(
        validate_examples(repo_root, run_artifact_schema, context_packet_schema)
    )
    return errors


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def refresh_agent_platform(repo_root: Path) -> list[str]:
    manifest_path = repo_root / ".github" / "agent-platform" / "workflow-manifest.json"
    workflow_manifest = load_json(manifest_path)
    skill_registry = build_skill_registry(repo_root, workflow_manifest)
    repo_map = build_repo_map(repo_root, workflow_manifest)

    changed_files: list[str] = []
    skill_registry_path = (
        repo_root / ".github" / "agent-platform" / "skill-registry.json"
    )
    repo_map_path = repo_root / ".github" / "agent-platform" / "repo-map.json"

    if write_if_changed(skill_registry_path, dump_json(skill_registry)):
        changed_files.append(skill_registry_path.relative_to(repo_root).as_posix())
    if write_if_changed(repo_map_path, dump_json(repo_map)):
        changed_files.append(repo_map_path.relative_to(repo_root).as_posix())
    return changed_files


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root_from_script(Path(__file__)),
        help="Repository root to operate on. Defaults to the current repository.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Refresh canonical metadata files in place.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Validate metadata and fail if files drift.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = args.repo_root.resolve()

    if args.write:
        try:
            changed_files = refresh_agent_platform(repo_root)
            validation_errors = validate_agent_platform(repo_root)
        except (
            AgentPlatformValidationError,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        if validation_errors:
            for error in validation_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if changed_files:
            for path in changed_files:
                print(f"updated {path}")
        else:
            print("agent-platform metadata already up to date")
        return 0

    try:
        validation_errors = validate_agent_platform(repo_root)
    except (
        AgentPlatformValidationError,
        FileNotFoundError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("agent-platform metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
