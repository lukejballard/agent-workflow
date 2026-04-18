"""Idempotent seed script: insert all static templates into the DB templates table.

Usage::

    python scripts/migrate_templates.py

Re-running the script is safe — existing templates (matched by ``template_id``) are skipped.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure project root is on the path when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from pipeline_observe.models.pipeline_studio_catalog import get_pipeline_templates
from pipeline_observe.storage.metadata import Base
from pipeline_observe.storage.template_models import Template, TemplateTag

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def _get_engine():
    url = os.environ.get(
        "DATABASE_URL",
        "sqlite:////data/pipeline_observe.db",
    )
    return create_engine(url, echo=False)


def seed_templates(session: Session) -> tuple[int, int]:
    """Insert static templates that don't already exist.

    Returns (inserted, skipped) counts.
    """
    catalog = get_pipeline_templates()
    inserted = 0
    skipped = 0

    for entry in catalog:
        t_id: str = entry["template_id"]
        existing = session.scalar(select(Template).where(Template.template_id == t_id))
        if existing is not None:
            logger.info("SKIP   %-40s (already exists, id=%s)", t_id, existing.id)
            skipped += 1
            continue

        pipeline_data = dict(entry.get("pipeline") or {})
        # Serialize pipeline JSON to text for storage in pipeline_json column
        pipeline_json_text = json.dumps(pipeline_data, default=str)

        row = Template(
            template_id=t_id,
            name=entry.get("name", t_id),
            category=entry.get("category", ""),
            description=entry.get("description", ""),
            author=entry.get("author", ""),
            version=entry.get("version", "1.0.0"),
            thumbnail_url=entry.get("thumbnail_url"),
            pipeline_json=pipeline_json_text,
        )
        for tag in entry.get("tags", []):
            row.tags.append(TemplateTag(tag=tag))

        session.add(row)
        inserted += 1
        logger.info("INSERT %-40s", t_id)

    session.commit()
    return inserted, skipped


def main() -> None:
    engine = _get_engine()

    # Ensure tables exist (safe no-op if already present).
    Base.metadata.create_all(engine, checkfirst=True)

    with Session(engine) as session:
        inserted, skipped = seed_templates(session)

    total = inserted + skipped
    logger.info(
        "Done — %d template(s) processed: %d inserted, %d skipped.",
        total,
        inserted,
        skipped,
    )


if __name__ == "__main__":
    main()
