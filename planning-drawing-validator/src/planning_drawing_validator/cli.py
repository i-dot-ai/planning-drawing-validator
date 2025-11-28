import asyncio
import json
import logging
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from planning_drawing_validator.logging import setup_logging
from planning_drawing_validator.models import Document, ValidationResult
from planning_drawing_validator.validator import DocumentValidator

__all__ = ["app", "validate", "main"]

logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(help="Planning Document Validator")


def create_results_table(results: list[ValidationResult]) -> Table:
    """Create formatted table of validation results.

    Args:
        results: List of validation results.

    Returns:
        Formatted Rich Table.
    """
    table = Table(title="Validation Results", show_header=True, header_style="bold cyan")

    table.add_column("Document", style="dim", width=30)
    table.add_column("Type", style="magenta")
    table.add_column("Validity", style="green")
    table.add_column("Confidence", justify="center")
    table.add_column("Time", justify="right")

    for result in results:
        validity_style = "green" if result.validity == "VALID" else "red"
        validity_text = f"[{validity_style}]{result.validity}[/{validity_style}]"

        table.add_row(
            result.document_id[:27] + "..." if len(result.document_id) > 30 else result.document_id,
            result.document_type,
            validity_text,
            result.confidence,
            f"{result.execution_time:.2f}s",
        )

    return table


def create_summary_panel(results: list[ValidationResult]) -> Panel:
    """Create summary panel of validation results.

    Args:
        results: List of validation results.

    Returns:
        Formatted Rich Panel.
    """
    total = len(results)
    successful = sum(1 for r in results if r.success)
    valid_count = sum(1 for r in results if r.validity == "VALID" and r.success)
    invalid_count = sum(1 for r in results if r.validity == "INVALID" and r.success)
    avg_time = sum(r.execution_time for r in results) / total if total > 0 else 0

    summary_text = f"""
Total Documents: {total}
Successful: [green]{successful}[/green]
Errors: [red]{total - successful}[/red]

Valid: [green]{valid_count}[/green]
Invalid: [red]{invalid_count}[/red]

Average Time: {avg_time:.2f}s
"""

    return Panel(summary_text.strip(), title="Summary", border_style="blue")


def display_detailed_result(result: ValidationResult) -> None:
    """Display detailed validation result with stages and reasoning.

    Args:
        result: Validation result to display.
    """
    console.print(f"\n[bold cyan]═══ {result.document_id} ═══[/bold cyan]")

    # Classification Stage
    console.print("\n[bold yellow]📋 Classification Stage[/bold yellow]")
    console.print(f"  Document Type: [magenta]{result.document_type}[/magenta]")
    console.print(f"  Confidence: {result.classification_confidence or 'UNKNOWN'}")
    console.print(f"  Prompt Type: [dim]{result.prompt_type}[/dim]")

    if result.classification_reasoning:
        console.print("\n[bold]Classification Reasoning:[/bold]")
        console.print(Panel(result.classification_reasoning, border_style="yellow", padding=(0, 2)))

    # Validation Stage
    console.print("\n[bold yellow]✓ Validation Stage[/bold yellow]")
    validity_style = "green" if result.validity == "VALID" else "red"
    console.print(f"  Validity: [{validity_style}]{result.validity}[/{validity_style}]")
    console.print(f"  Confidence: {result.confidence}")
    console.print(f"  Execution Time: {result.execution_time:.2f}s")

    if result.reasoning:
        console.print("\n[bold]Reasoning:[/bold]")
        console.print(Panel(result.reasoning, border_style="blue", padding=(0, 2)))

    # Requirements Checked
    if result.requirements_checked:
        console.print("\n[bold]Requirements Checked:[/bold]")
        req_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        req_table.add_column("Requirement", style="cyan", no_wrap=False)
        req_table.add_column("Status", justify="center", width=15)
        req_table.add_column("Details", style="dim", no_wrap=False)

        for req in result.requirements_checked:
            status_style = (
                "green" if req.status == "PASS" else ("red" if req.status == "FAIL" else "yellow")
            )
            status_symbol = "✓" if req.status == "PASS" else ("✗" if req.status == "FAIL" else "○")
            status_text = f"[{status_style}]{status_symbol} {req.status}[/{status_style}]"
            req_table.add_row(req.requirement, status_text, req.details or "")

        console.print(req_table)

    # Constituent Drawings (for mixed plans)
    if result.is_mixed_drawing and result.constituent_drawings:
        console.print("\n[bold]Constituent Drawings:[/bold]")

        for idx, const in enumerate(result.constituent_drawings, 1):
            tree = Tree(f"[bold]{idx}. {const.drawing_type}[/bold]")

            validity_style = "green" if const.validity == "VALID" else "red"
            tree.add(f"Validity: [{validity_style}]{const.validity}[/{validity_style}]")
            tree.add(f"Confidence: {const.confidence}")

            if const.reasoning:
                reasoning_node = tree.add("[bold]Reasoning:[/bold]")
                reasoning_node.add(const.reasoning)

            if const.requirements_checked:
                reqs_node = tree.add(
                    f"[bold]Requirements ({len(const.requirements_checked)}):[/bold]"
                )
                for req in const.requirements_checked:
                    status_style = (
                        "green"
                        if req.status == "PASS"
                        else ("red" if req.status == "FAIL" else "yellow")
                    )
                    status_symbol = (
                        "✓" if req.status == "PASS" else ("✗" if req.status == "FAIL" else "○")
                    )
                    req_text = f"[{status_style}]{status_symbol}[/{status_style}] {req.requirement}"
                    if req.details:
                        req_text += f": [dim]{req.details}[/dim]"
                    reqs_node.add(req_text)

            console.print(tree)

    console.print()


async def validate_documents(
    documents: list[Document],
    max_concurrent: int = 5,
) -> list[ValidationResult]:
    """Validate documents with progress tracking.

    Args:
        documents: List of documents to validate.
        max_concurrent: Maximum concurrent validations.

    Returns:
        List of validation results.
    """
    validator = DocumentValidator(max_concurrent=max_concurrent)

    total = len(documents)
    completed = 0
    semaphore = asyncio.Semaphore(max_concurrent)

    async def validate_with_progress(doc: Document, index: int) -> ValidationResult:
        nonlocal completed

        async with semaphore:
            if total > 1:
                console.print(f"[dim]Validating {index}/{total}: {doc.filename}[/dim]")

            result = await validator.validate(doc)
            completed += 1

            if total > 1:
                status = "✓" if result.success else "✗"
                style = "green" if result.success else "red"
                console.print(
                    f"[{style}]{status}[/{style}] Completed {completed}/{total}: {doc.filename}"
                )

            return result

    tasks = [validate_with_progress(doc, idx) for idx, doc in enumerate(documents, 1)]
    return await asyncio.gather(*tasks)


@app.command()
def validate(
    path: Path = typer.Argument(
        ..., help="Path to document file or directory of documents", exists=True
    ),
    concurrent: int = typer.Option(5, "--concurrent", "-c", help="Maximum concurrent validations"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Validate planning documents.

    Validates one or more planning documents and outputs results.

    Examples:
        # Single document
        validate-drawing site-plan.pdf

        # Directory of documents
        validate-drawing documents/ --concurrent 10

        # Save results to file
        validate-drawing documents/ --output results.json
    """
    setup_logging("DEBUG" if verbose else "INFO")

    console.print(
        Panel.fit(
            "[bold cyan]Planning Document Validator[/bold cyan]",
            border_style="cyan",
        )
    )

    # Load documents
    doc_list: list[Document] = []

    if path.is_file():
        doc_list = [
            Document(
                document_id=path.stem,
                filename=path.name,
                file_path=str(path.absolute()),
            )
        ]
        console.print(f"[green]✓[/green] Processing: {path.name}")
    elif path.is_dir():
        pdf_files = list(path.glob("**/*.pdf"))
        doc_list = [
            Document(document_id=f.stem, filename=f.name, file_path=str(f.absolute()))
            for f in pdf_files
        ]
        console.print(f"[green]✓[/green] Found {len(doc_list)} PDF files")
    else:
        console.print(f"[red]✗[/red] Invalid path: {path}")
        raise typer.Exit(1)

    if not doc_list:
        console.print("[red]✗[/red] No documents to validate")
        raise typer.Exit(1)

    console.print(f"[bold]Max concurrent:[/bold] {concurrent}\n")

    # Run validation
    try:
        results = asyncio.run(validate_documents(doc_list, concurrent))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Interrupted by user")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Validation failed: {e}")
        logger.exception("Validation failed")
        raise typer.Exit(1)

    # Display detailed results for each document
    console.print()
    for result in results:
        display_detailed_result(result)

    # Display summary table
    console.print()
    console.print(create_results_table(results))
    console.print()
    console.print(create_summary_panel(results))

    # Display details for failed validations
    failed = [r for r in results if not r.success]
    if failed:
        console.print("\n[bold red]Failed Validations:[/bold red]")
        for result in failed:
            console.print(
                Panel(
                    f"[red]{result.error_message or 'Unknown error'}[/red]",
                    title=f"[red]{result.document_id}[/red]",
                    border_style="red",
                )
            )

    # Save to JSON if requested
    if output:
        results_dict = [asdict(r) for r in results]
        with output.open("w") as f:
            json.dump(results_dict, f, indent=2, default=str)
        console.print(f"\n[green]✓[/green] Results saved to {output}")

    # Exit with error if any validation failed
    if failed:
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
