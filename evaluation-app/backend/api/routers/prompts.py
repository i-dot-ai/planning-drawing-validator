import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from planning_drawing_validator.types import PromptName, VersionID

from backend.api.dependencies import get_prompt_manager
from backend.api.error_handlers import bad_request, handle_error, not_found
from backend.api.models.requests import (
    ActivateVersionRequest,
    PromptUpdateRequest,
    SnapshotRequest,
)
from backend.api.models.responses import (
    PromptActivateResponse,
    PromptBranchResponse,
    PromptDeleteResponse,
    PromptDetailResponse,
    PromptListResponse,
    PromptSnapshotResponse,
    PromptUpdateResponse,
    PromptVersionInfo,
    PromptVersionResponse,
)
from backend.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("")
async def list_prompts(
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptListResponse:
    """Retrieve list of all prompts with version information.

    Args:
        pm: Prompt manager dependency for accessing prompt data.

    Returns:
        PromptListResponse containing summary of all prompts and their versions.

    Raises:
        HTTPException: When prompt retrieval fails (500).
    """
    try:
        summary = pm.get_all_prompts_summary()
        return PromptListResponse(prompts=summary)
    except Exception as e:
        raise handle_error(e, context={"operation": "list_prompts"})


@router.get("/{prompt_name}")
async def get_prompt_details(
    prompt_name: PromptName, pm: PromptManager = Depends(get_prompt_manager)
) -> PromptDetailResponse:
    """Retrieve detailed information about a specific prompt.

    Automatically creates an initial v0 snapshot if the prompt exists but has no
    version history. This ensures all prompts have at least one versioned state.

    Args:
        prompt_name: Name of the prompt to retrieve details for.
        pm: Prompt manager dependency for accessing prompt data.

    Returns:
        PromptDetailResponse containing prompt details, version history, and active version.

    Raises:
        HTTPException: When prompt is not found (404) or retrieval fails (500).
    """
    try:
        # Get version history
        versions = pm.get_version_history(prompt_name)
        active_version = pm.get_active_version(prompt_name)

        if not versions:
            # Prompt exists but no versions yet - create initial v0 snapshot
            current_content = pm.get_current_content(prompt_name)
            if current_content is None:
                raise not_found(f"Prompt not found: {prompt_name}")

            # Create initial version (v0)
            pm.create_snapshot(
                prompt_name=prompt_name,
                content=current_content,
                author="system",
                description="Initial version (original prompt)",
            )

            # Now fetch the versions again
            versions = pm.get_version_history(prompt_name)
            active_version = pm.get_active_version(prompt_name)

        version_infos = [
            PromptVersionInfo(
                version_id=v.version_id,
                version_number=v.version_number,
                timestamp=v.timestamp.isoformat(),
                author=v.author,
                description=v.description,
                is_active=v.is_active,
                parent_version_id=v.parent_version_id,
                metadata=v.metadata,
            )
            for v in versions
        ]

        active_version_dict = None
        if active_version:
            active_version_dict = {
                "version_id": active_version.version_id,
                "timestamp": active_version.timestamp.isoformat(),
                "author": active_version.author,
                "description": active_version.description,
            }

        return PromptDetailResponse(
            name=prompt_name,
            type=versions[0].prompt_type if versions else "unknown",
            current_content=active_version.content if active_version else None,
            versions=version_infos,
            active_version=active_version_dict,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(e, context={"operation": "get_prompt_details", "prompt_name": prompt_name})


@router.get("/{prompt_name}/versions/{version_id}")
async def get_prompt_version(
    prompt_name: PromptName,
    version_id: VersionID,
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptVersionResponse:
    """Retrieve a specific version of a prompt.

    Args:
        prompt_name: Name of the prompt.
        version_id: Unique identifier of the version to retrieve.
        pm: Prompt manager dependency for accessing prompt data.

    Returns:
        PromptVersionResponse containing complete version details including content,
        metadata, and lineage information.

    Raises:
        HTTPException: When version is not found (404) or retrieval fails (500).
    """
    try:
        version = pm.get_version(prompt_name, version_id)
        if not version:
            raise not_found(f"Version not found: {version_id}")

        return PromptVersionResponse(
            version_id=version.version_id,
            prompt_name=version.prompt_name,
            prompt_type=version.prompt_type,
            content=version.content,
            timestamp=version.timestamp.isoformat(),
            author=version.author,
            description=version.description,
            parent_version_id=version.parent_version_id,
            is_active=version.is_active,
            metadata=version.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "get_prompt_version",
                "prompt_name": prompt_name,
                "version_id": version_id,
            },
        )


@router.put("/{prompt_name}")
async def update_prompt(
    prompt_name: PromptName,
    request: PromptUpdateRequest,
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptUpdateResponse:
    """Update a prompt with new content, creating a new version.

    Creates a new version in the version history and updates the filesystem
    to reflect the new active content.

    Args:
        prompt_name: Name of the prompt to update.
        request: Update request containing new content, author, description, and metadata.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptUpdateResponse containing status, new version ID, and confirmation message.

    Raises:
        HTTPException: When update operation fails (500).
    """
    try:
        new_version = pm.update_prompt(
            prompt_name=prompt_name,
            new_content=request.content,
            author=request.author,
            description=request.description,
            metadata=request.metadata,
        )

        return PromptUpdateResponse(
            status="updated",
            version_id=new_version.version_id,
            message=f"Prompt {prompt_name} updated successfully",
        )
    except Exception as e:
        raise handle_error(e, context={"operation": "update_prompt", "prompt_name": prompt_name})


@router.delete("/{prompt_name}/versions/{version_id}")
async def delete_prompt_version(
    prompt_name: PromptName,
    version_id: VersionID,
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptDeleteResponse:
    """Delete a specific version of a prompt.

    Version 0 (initial version) and the currently active version cannot be deleted
    to maintain version history integrity and prevent accidental removal of the
    active prompt state.

    Args:
        prompt_name: Name of the prompt containing the version.
        version_id: Unique identifier of the version to delete.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptDeleteResponse containing status, deleted version ID, and confirmation message.

    Raises:
        HTTPException: When attempting to delete v0 or active version (400),
                      or when deletion fails (500).
    """
    try:
        pm.delete_version(
            prompt_name=prompt_name,
            version_id=version_id,
        )

        return PromptDeleteResponse(
            status="deleted",
            version_id=version_id,
            message=f"Deleted version {version_id} of {prompt_name}",
        )
    except ValueError as e:
        raise bad_request(str(e))
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "delete_prompt_version",
                "prompt_name": prompt_name,
                "version_id": version_id,
            },
        )


@router.post("/{prompt_name}/versions/{version_id}/activate")
async def activate_prompt_version(
    prompt_name: PromptName,
    version_id: VersionID,
    request: ActivateVersionRequest = ActivateVersionRequest(),
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptActivateResponse:
    """Activate a specific version of a prompt.

    Rolls back to a previous version, making it the active prompt content.
    Optionally updates the filesystem to reflect the activated version.

    Args:
        prompt_name: Name of the prompt.
        version_id: Unique identifier of the version to activate.
        request: Activation request with filesystem update flag.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptActivateResponse containing status, activated version ID, and confirmation message.

    Raises:
        HTTPException: When version is not found (404) or activation fails (500).
    """
    try:
        version = pm.activate_version(
            prompt_name=prompt_name,
            version_id=version_id,
            update_filesystem=request.update_filesystem,
        )

        return PromptActivateResponse(
            status="activated",
            version_id=version.version_id,
            message=f"Activated version {version_id} of {prompt_name}",
        )
    except ValueError:
        raise not_found(f"Version not found: {version_id}")
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "activate_prompt_version",
                "prompt_name": prompt_name,
                "version_id": version_id,
            },
        )


@router.get("/{prompt_name}/compare")
async def compare_prompt_versions(
    prompt_name: PromptName,
    version_a: VersionID,
    version_b: VersionID,
    pm: PromptManager = Depends(get_prompt_manager),
) -> dict[str, Any]:
    """Compare two versions of a prompt.

    Generates a detailed comparison showing differences between two versions,
    including content changes and metadata variations.

    Args:
        prompt_name: Name of the prompt.
        version_a: Unique identifier of the first version.
        version_b: Unique identifier of the second version.
        pm: Prompt manager dependency for accessing prompt versions.

    Returns:
        Dictionary containing detailed comparison data including diffs and metadata.

    Raises:
        HTTPException: When either version is not found (404) or comparison fails (500).
    """
    try:
        diff = pm.compare_versions(prompt_name, version_a, version_b)
        return diff
    except ValueError:
        raise not_found(f"Version comparison not found: {version_a} or {version_b}")
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "compare_prompt_versions",
                "prompt_name": prompt_name,
                "version_a": version_a,
                "version_b": version_b,
            },
        )


@router.post("/{prompt_name}/snapshot")
async def create_prompt_snapshot(
    prompt_name: PromptName,
    request: SnapshotRequest = SnapshotRequest(),
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptSnapshotResponse:
    """Create a snapshot of the current prompt state.

    Captures the current filesystem content as a new version in the version history.
    Useful for manual versioning before making significant changes.

    Args:
        prompt_name: Name of the prompt to snapshot.
        request: Snapshot request containing author and description.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptSnapshotResponse containing status, new version ID, and confirmation message.

    Raises:
        HTTPException: When snapshot creation fails (500).
    """
    try:
        version = pm.create_snapshot(
            prompt_name=prompt_name,
            author=request.author,
            description=request.description,
        )

        return PromptSnapshotResponse(
            status="snapshot_created",
            version_id=version.version_id,
            message=f"Snapshot created for {prompt_name}",
        )
    except Exception as e:
        raise handle_error(
            e,
            context={"operation": "create_prompt_snapshot", "prompt_name": prompt_name},
        )


@router.post("/snapshot-all")
async def snapshot_all_prompts(
    request: SnapshotRequest = SnapshotRequest(),
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptSnapshotResponse:
    """Create snapshots of all prompts.

    Captures the current filesystem state of all prompts as new versions.
    Useful for creating synchronised backup points across the entire prompt library.

    Args:
        request: Snapshot request containing author and description for all snapshots.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptSnapshotResponse containing status, count of created snapshots, and confirmation message.

    Raises:
        HTTPException: When snapshot creation fails (500).
    """
    try:
        snapshots = pm.snapshot_all_prompts(
            author=request.author,
            description=request.description,
        )

        return PromptSnapshotResponse(
            status="snapshots_created",
            count=len(snapshots),
            message=f"Created {len(snapshots)} snapshots",
        )
    except Exception as e:
        raise handle_error(e, context={"operation": "snapshot_all_prompts"})


@router.get("/{prompt_name}/validate")
async def validate_prompt_sync(
    prompt_name: PromptName, pm: PromptManager = Depends(get_prompt_manager)
) -> dict[str, Any]:
    """Validate that prompt filesystem and version index are in sync.

    Checks consistency between the filesystem content and the version control
    system, identifying any discrepancies or drift.

    Args:
        prompt_name: Name of the prompt to validate.
        pm: Prompt manager dependency for accessing prompt data.

    Returns:
        Dictionary containing validation results, sync status, and any identified issues.

    Raises:
        HTTPException: When validation fails (500).
    """
    try:
        validation = pm.validate_prompt_sync(prompt_name)
        return validation
    except Exception as e:
        raise handle_error(e, context={"operation": "validate_prompt_sync", "prompt_name": prompt_name})


@router.post("/{prompt_name}/branch/{version_id}")
async def create_branch_from_version(
    prompt_name: PromptName,
    version_id: VersionID,
    request: PromptUpdateRequest,
    pm: PromptManager = Depends(get_prompt_manager),
) -> PromptBranchResponse:
    """Create a new version branching from a specific parent version.

    Enables non-linear version history by creating a new version that branches from
    a specific parent, rather than the currently active version. Updates the filesystem
    to make the new branch the active content.

    Args:
        prompt_name: Name of the prompt.
        version_id: Unique identifier of the parent version to branch from.
        request: Update request containing new content, author, and description.
        pm: Prompt manager dependency for managing prompt versions.

    Returns:
        PromptBranchResponse containing status, new version ID, parent version ID,
        and confirmation message.

    Raises:
        HTTPException: When parent version is not found (404) or branch creation fails (500).
    """
    try:
        # Get the parent version
        parent_version = pm.get_version(prompt_name, version_id)
        if not parent_version:
            raise not_found(f"Version not found: {version_id}")

        # Create new version with explicit parent
        new_version = pm.create_snapshot(
            prompt_name=prompt_name,
            content=request.content,
            author=request.author,
            description=request.description,
            parent_version_id=version_id,
        )

        # Activate the new version to update filesystem
        pm.activate_version(prompt_name, new_version.version_id, update_filesystem=True)

        return PromptBranchResponse(
            status="branch_created",
            version_id=new_version.version_id,
            parent_version_id=version_id,
            message=f"Created new branch from version {version_id[:8]}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "create_branch_from_version",
                "prompt_name": prompt_name,
                "version_id": version_id,
            },
        )
