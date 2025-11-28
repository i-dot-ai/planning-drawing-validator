#!/usr/bin/env python3
"""
Ground Truth Management Example

This example demonstrates how to manage ground truth labels for evaluation.

Requirements:
    - evaluation-app installed
    - Database configured

Usage:
    # Import ground truth from JSON
    python manage_ground_truth.py import ground_truth.json

    # Export ground truth to JSON
    python manage_ground_truth.py export ground_truth_export.json

    # List all ground truth labels
    python manage_ground_truth.py list
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from backend.config import Config
from backend.database.connection import get_sessionmaker
from backend.database.models import GroundTruth


async def import_ground_truth(json_file: Path) -> None:
    """
    Import ground truth labels from JSON file.

    Args:
        json_file: Path to JSON file with ground truth data
    """
    print(f"📥 Importing ground truth from: {json_file}")
    print("=" * 60)

    # Load JSON data
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    # Initialise database
    config = Config.load()
    sessionmaker = get_sessionmaker(config.database.url)

    imported_count = 0
    updated_count = 0

    with sessionmaker() as session:
        for item in data:
            # Check if ground truth already exists
            stmt = select(GroundTruth).where(GroundTruth.document_id == item["document_id"])
            existing = session.scalars(stmt).first()

            if existing:
                # Update existing
                existing.expected_validity = item["expected_validity"]
                existing.expected_document_type = item.get("expected_document_type")
                existing.notes = item.get("notes")
                updated_count += 1
                print(f"  📝 Updated: {item['document_id']}")
            else:
                # Create new
                ground_truth = GroundTruth(
                    document_id=item["document_id"],
                    filename=item["filename"],
                    expected_validity=item["expected_validity"],
                    expected_document_type=item.get("expected_document_type"),
                    notes=item.get("notes"),
                )
                session.add(ground_truth)
                imported_count += 1
                print(f"  ✅ Imported: {item['document_id']}")

        session.commit()

    print("\n" + "=" * 60)
    print("✅ Import complete!")
    print(f"  New labels: {imported_count}")
    print(f"  Updated labels: {updated_count}")
    print(f"  Total: {imported_count + updated_count}")


async def export_ground_truth(json_file: Path) -> None:
    """
    Export all ground truth labels to JSON file.

    Args:
        json_file: Path to output JSON file
    """
    print(f"📤 Exporting ground truth to: {json_file}")
    print("=" * 60)

    # Initialise database
    config = Config.load()
    sessionmaker = get_sessionmaker(config.database.url)

    data = []

    with sessionmaker() as session:
        stmt = select(GroundTruth).order_by(GroundTruth.document_id)
        ground_truths = session.scalars(stmt).all()

        for gt in ground_truths:
            data.append(
                {
                    "document_id": gt.document_id,
                    "filename": gt.filename,
                    "expected_validity": gt.expected_validity,
                    "expected_document_type": gt.expected_document_type,
                    "notes": gt.notes,
                }
            )
            print(f"  ✅ Exported: {gt.document_id}")

    # Write to JSON file
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("✅ Export complete!")
    print(f"  Labels exported: {len(data)}")
    print(f"  Output file: {json_file}")


async def list_ground_truth() -> None:
    """List all ground truth labels."""
    print("📋 Ground Truth Labels")
    print("=" * 60)

    # Initialise database
    config = Config.load()
    sessionmaker = get_sessionmaker(config.database.url)

    with sessionmaker() as session:
        stmt = select(GroundTruth).order_by(GroundTruth.document_id)
        ground_truths = session.scalars(stmt).all()

        if not ground_truths:
            print("\n⚠️  No ground truth labels found")
            return

        print(f"\nTotal labels: {len(ground_truths)}\n")

        for gt in ground_truths:
            valid_str = "✅ Valid" if gt.expected_validity else "❌ Invalid"
            print(f"Document ID: {gt.document_id}")
            print(f"  Filename: {gt.filename}")
            print(f"  Expected: {valid_str}")
            if gt.expected_document_type:
                print(f"  Type: {gt.expected_document_type}")
            if gt.notes:
                print(f"  Notes: {gt.notes}")
            print()


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_ground_truth.py import <json_file>")
        print("  python manage_ground_truth.py export <json_file>")
        print("  python manage_ground_truth.py list")
        print("\nExamples:")
        print("  python manage_ground_truth.py import labels.json")
        print("  python manage_ground_truth.py export all_labels.json")
        print("  python manage_ground_truth.py list")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "import":
        if len(sys.argv) != 3:
            print("❌ Error: Import command requires JSON file path")
            sys.exit(1)
        json_file = Path(sys.argv[2])
        if not json_file.exists():
            print(f"❌ Error: File not found: {json_file}")
            sys.exit(1)
        asyncio.run(import_ground_truth(json_file))

    elif command == "export":
        if len(sys.argv) != 3:
            print("❌ Error: Export command requires output file path")
            sys.exit(1)
        json_file = Path(sys.argv[2])
        asyncio.run(export_ground_truth(json_file))

    elif command == "list":
        asyncio.run(list_ground_truth())

    else:
        print(f"❌ Error: Unknown command: {command}")
        print("Valid commands: import, export, list")
        sys.exit(1)


if __name__ == "__main__":
    main()
