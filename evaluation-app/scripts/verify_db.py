#!/usr/bin/env python3
"""
Verify database connection and show stored data.

This script demonstrates that runs, documents, and evaluations
are being stored in and retrieved from PostgreSQL.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_session_maker
from backend.database.models import DocumentResult, Run, RunEvaluation


def verify_database():
    """Verify database connection and display stored data."""
    print("=" * 80)
    print("DATABASE VERIFICATION SCRIPT")
    print("=" * 80)
    print()

    # Get database connection
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://review_user:review_password@localhost:5432/review_dev",  # pragma: allowlist secret
    )
    print(f"📊 Database URL: {database_url.split('@')[1] if '@' in database_url else database_url}")
    print()

    try:
        SessionMaker = get_session_maker(database_url)
        session = SessionMaker()

        # Query runs
        print("🏃 RUNS IN DATABASE:")
        print("-" * 80)
        runs = session.query(Run).order_by(Run.timestamp.desc()).limit(10).all()

        if not runs:
            print("  ⚠️  No runs found in database")
            print("  💡 Tip: Start an evaluation to create database records")
        else:
            print(f"  Found {len(runs)} recent runs\n")
            for i, run in enumerate(runs, 1):
                print(f"  {i}. Run ID: {run.run_id}")
                print(f"     Name: {run.name or 'Unnamed'}")
                print(f"     Timestamp: {run.timestamp}")
                print(f"     Documents: {run.total_documents} total, {run.completed_documents} completed")
                print(f"     Status: {run.status}")
                if run.has_ground_truth:
                    print(f"     Accuracy: {run.overall_accuracy * 100:.1f}%")
                print(f"     Execution time: {run.execution_time:.2f}s")
                print()

        # Query total document results
        print("📄 DOCUMENT RESULTS:")
        print("-" * 80)
        doc_count = session.query(DocumentResult).count()
        print(f"  Total document results stored: {doc_count}")

        if doc_count > 0:
            # Show some examples
            recent_docs = session.query(DocumentResult).limit(5).all()
            print("\n  Recent examples:")
            for doc in recent_docs:
                print(f"    - {doc.filename}")
                print(f"      Predicted: {doc.predicted_validity}")
                if doc.expected_validity:
                    print(f"      Expected: {doc.expected_validity}")
                    print(f"      Correct: {'✓' if doc.is_correct else '✗'}")
        print()

        # Query evaluations
        print("📈 EVALUATIONS (with ground truth):")
        print("-" * 80)
        eval_count = session.query(RunEvaluation).count()
        print(f"  Total evaluations stored: {eval_count}")

        if eval_count > 0:
            evaluations = session.query(RunEvaluation).limit(3).all()
            print("\n  Recent evaluations:")
            for eval in evaluations:
                run = session.query(Run).filter(Run.id == eval.run_id).first()
                print(f"    - Run: {run.run_id if run else 'Unknown'}")
                print(f"      Overall Accuracy: {eval.overall_accuracy * 100:.1f}%")
                print(f"      Precision: {eval.precision * 100:.1f}%" if eval.precision else "      Precision: N/A")
                print(f"      Recall: {eval.recall * 100:.1f}%" if eval.recall else "      Recall: N/A")
                print(f"      F1 Score: {eval.f1_score:.3f}" if eval.f1_score else "      F1 Score: N/A")
                print("      Confusion Matrix:")
                print(f"        TP: {eval.true_positives}, TN: {eval.true_negatives}")
                print(f"        FP: {eval.false_positives}, FN: {eval.false_negatives}")
                print()
        print()

        # Database statistics
        print("📊 DATABASE STATISTICS:")
        print("-" * 80)
        print(f"  Total Runs: {session.query(Run).count()}")
        print(f"  Total Document Results: {doc_count}")
        print(f"  Total Evaluations: {eval_count}")
        print(f"  Runs with Ground Truth: {session.query(Run).filter(Run.has_ground_truth).count()}")
        print(f"  Runs without Ground Truth: {session.query(Run).filter(not Run.has_ground_truth).count()}")
        print()

        session.close()

        print("=" * 80)
        print("✅ Database verification complete!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print()
        print("💡 Troubleshooting:")
        print("  1. Ensure PostgreSQL is running (docker-compose ps)")
        print("  2. Check DATABASE_URL environment variable")
        print("  3. Verify database schema is initialised (alembic upgrade head)")
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
