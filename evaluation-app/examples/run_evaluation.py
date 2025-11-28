#!/usr/bin/env python3
"""Evaluation run example for the evaluation application.

This example demonstrates how to start an evaluation run.
"""

import httpx


def main():
    """Run evaluation example."""
    base_url = "http://localhost:8001"

    # Example: Start a new evaluation run
    response = httpx.post(
        f"{base_url}/api/runs",
        json={
            "name": "Example Evaluation",
            "description": "Demonstration of evaluation functionality",
        },
        timeout=30.0,
    )

    run_data = response.json()
    print(f"Created run: {run_data['run_id']}")

    # Example: Check run status
    run_id = run_data["run_id"]
    status_response = httpx.get(f"{base_url}/api/runs/{run_id}", timeout=30.0)
    print(f"Run status: {status_response.json()}")


if __name__ == "__main__":
    main()
