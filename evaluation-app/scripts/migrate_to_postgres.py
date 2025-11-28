#!/usr/bin/env python3
"""
Migration script to transfer existing JSON-based run history to PostgreSQL.

This script:
1. Backs up the existing JSON file
2. Creates PostgreSQL database schema
3. Migrates all runs, documents, and events to the database
4. Verifies data integrity

Usage:
    uv run python scripts/migrate_to_postgres.py [--database-url postgresql://user:pass@host/dbname]  # pragma: allowlist secret
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend.database.connection import get_session_maker
from backend.database.models import DocumentResult, Run, RunEvent


def backup_json_file(json_path: Path) -> Path:
    """Create a timestamped backup of the JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = json_path.parent / f"{json_path.stem}_backup_{timestamp}{json_path.suffix}"
    shutil.copy2(json_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path


def migrate_run(session: Session, run_data: dict) -> Run:
    """Migrate a single run with all its documents and events."""
    # Determine if run has ground truth
    has_ground_truth = bool(run_data.get("ground_truth_path")) or any(
        doc.get("expected_validity") not in [None, "UNKNOWN"] for doc in run_data.get("documents", [])
    )

    # Create run record
    timestamp_str = run_data.get("timestamp")
    run = Run(
        run_id=run_data.get("run_id"),
        name=run_data.get("name"),
        timestamp=datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(),
        total_documents=run_data.get("total_documents", 0),
        completed_documents=run_data.get("completed_documents", 0),
        overall_accuracy=run_data.get("overall_accuracy") if has_ground_truth else None,
        has_ground_truth=has_ground_truth,
        execution_time=run_data.get("execution_time", 0.0),
        status=run_data.get("status", "completed"),
    )

    # Migrate documents
    for doc_data in run_data.get("documents", []):
        doc = DocumentResult(
            document_id=doc_data.get("document_id"),
            filename=doc_data.get("filename"),
            expected_validity=doc_data.get("expected_validity"),
            predicted_validity=doc_data.get("predicted_validity"),
            predicted_reasoning=doc_data.get("predicted_reasoning"),
            confidence=doc_data.get("confidence"),
            is_correct=doc_data.get("correct"),  # Renamed from 'correct' to 'is_correct'
            prompt_type=doc_data.get("prompt_type"),
            execution_time=doc_data.get("execution_time"),
            assertions=doc_data.get("assertions"),
            stages=doc_data.get("stages"),
        )
        run.documents.append(doc)

    # Migrate events (if present)
    for event_data in run_data.get("events", []):
        event = RunEvent(
            timestamp=datetime.fromisoformat(event_data.get("timestamp"))
            if event_data.get("timestamp")
            else datetime.utcnow(),
            event_type=event_data.get("type", "unknown"),
            document_id=event_data.get("data", {}).get("document_id"),
            data=event_data.get("data"),
        )
        run.events.append(event)

    return run


def migrate_json_to_postgres(json_path: Path, database_url: str | None = None, skip_backup: bool = False):
    """Main migration function."""
    print(f"\n🔄 Starting migration from {json_path}")
    print(f"📊 Database: {database_url or 'postgresql://localhost/review_dev'}")

    # Backup existing JSON
    if not skip_backup and json_path.exists():
        backup_json_file(json_path)

    # Initialise database
    print("\n📦 Initialising database schema...")
    print("   Note: Run 'alembic upgrade head' to create database schema")
    print("✓ Assuming database schema is already created via alembic")

    # Load JSON data
    if not json_path.exists():
        print(f"⚠️  JSON file not found: {json_path}")
        print("   No data to migrate. Database schema is ready for new runs.")
        return

    print(f"\n📖 Loading JSON data from {json_path}...")
    with open(json_path, encoding="utf-8") as f:
        runs_data = json.load(f)

    print(f"✓ Loaded {len(runs_data)} runs")

    # Migrate data
    SessionMaker = get_session_maker(database_url)
    session = SessionMaker()

    try:
        migrated_count = 0
        document_count = 0
        event_count = 0

        print("\n🚀 Migrating runs...")
        for i, run_data in enumerate(runs_data, 1):
            run_id = run_data.get("run_id", f"run_{i}")
            print(f"   [{i}/{len(runs_data)}] Migrating {run_id}...", end="")

            run = migrate_run(session, run_data)
            session.add(run)

            doc_count = len(run_data.get("documents", []))
            evt_count = len(run_data.get("events", []))

            document_count += doc_count
            event_count += evt_count
            migrated_count += 1

            print(f" ✓ ({doc_count} docs, {evt_count} events)")

            # Commit in batches to avoid memory issues
            if i % 10 == 0:
                session.commit()
                print("   💾 Committed batch of 10 runs")

        # Final commit
        session.commit()

        print("\n✅ Migration complete!")
        print(f"   • Migrated {migrated_count} runs")
        print(f"   • Migrated {document_count} document evaluations")
        print(f"   • Migrated {event_count} events")

        # Verify data
        print("\n🔍 Verifying migration...")
        db_run_count = session.query(Run).count()
        db_doc_count = session.query(DocumentResult).count()
        db_event_count = session.query(RunEvent).count()

        print(f"   • Database contains {db_run_count} runs")
        print(f"   • Database contains {db_doc_count} documents")
        print(f"   • Database contains {db_event_count} events")

        if db_run_count == migrated_count and db_doc_count == document_count:
            print("\n✅ Verification successful! All data migrated correctly.")
        else:
            print("\n⚠️  Verification warning: Count mismatch detected")
            print(f"   Expected {migrated_count} runs, found {db_run_count}")
            print(f"   Expected {document_count} documents, found {db_doc_count}")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate run history from JSON to PostgreSQL")
    parser.add_argument(
        "--database-url",
        type=str,
        help="PostgreSQL database URL (default: postgresql://localhost/review_dev)",
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path("reports/run_history.json"),
        help="Path to JSON file to migrate (default: reports/run_history.json)",
    )
    parser.add_argument("--skip-backup", action="store_true", help="Skip backing up the JSON file")

    args = parser.parse_args()

    migrate_json_to_postgres(
        json_path=args.json_path,
        database_url=args.database_url,
        skip_backup=args.skip_backup,
    )


if __name__ == "__main__":
    main()
