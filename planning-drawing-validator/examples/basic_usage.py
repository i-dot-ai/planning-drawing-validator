#!/usr/bin/env python3
"""Basic usage example for planning-drawing-validator.

This example demonstrates how to use the core validation functionality.
"""

from planning_drawing_validator import validate_drawing


def main():
    """Run basic validation example."""
    # Example: Validate a planning drawing
    result = validate_drawing("path/to/drawing.pdf")

    print(f"Validity: {result.validity}")
    print(f"Confidence: {result.confidence}")

    if result.issues:
        print("Issues found:")
        for issue in result.issues:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
