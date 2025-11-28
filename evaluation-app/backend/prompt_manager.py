import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, cast

from planning_drawing_validator.config import PathConfig
from planning_drawing_validator.types import PromptName, VersionID

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PromptVersion:
    """A versioned snapshot of a prompt."""

    version_id: VersionID  # SHA-256 hash of content
    version_number: int  # Sequential version number (0, 1, 2, ...)
    prompt_name: PromptName  # e.g., "validation_floor_plan"
    prompt_type: Literal["classification", "validation"]
    content: str
    timestamp: datetime
    author: str
    description: str
    parent_version_id: VersionID | None  # Previous version for history chain
    is_active: bool  # Currently deployed version
    metadata: dict[str, Any]  # Additional info (tags, performance metrics, etc.)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict for JSON storage."""
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "prompt_name": self.prompt_name,
            "prompt_type": self.prompt_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "description": self.description,
            "parent_version_id": self.parent_version_id,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptVersion":
        """Deserialise from dict."""
        return cls(
            version_id=data["version_id"],
            version_number=data.get("version_number", 0),
            prompt_name=data["prompt_name"],
            prompt_type=data["prompt_type"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            author=data["author"],
            description=data["description"],
            parent_version_id=data.get("parent_version_id"),
            is_active=data.get("is_active", False),
            metadata=data.get("metadata", {}),
        )


class PromptManager:
    """Manages prompt versions with git-like history tracking."""

    def __init__(self, config: PathConfig | None = None):
        self.config = config or PathConfig.default()
        self.prompts_dir = self.config.prompts_dir
        self.versions_dir = self.config.reports_dir / "prompt_versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Version storage
        self.version_index_path = self.versions_dir / "version_index.json"
        self.versions: dict[str, list[PromptVersion]] = self._load_version_index()

        # Run migration for version_number field if needed
        self.migrate_version_numbers()

    def _load_version_index(self) -> dict[str, list[PromptVersion]]:
        """Load all prompt versions from disk."""
        if not self.version_index_path.exists():
            return {}

        try:
            data = json.loads(self.version_index_path.read_text(encoding="utf-8"))
            return {
                prompt_name: [PromptVersion.from_dict(v) for v in versions] for prompt_name, versions in data.items()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse version index JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load version index: {e}", exc_info=True)
            return {}

    def _save_version_index(self) -> None:
        """Save version index to disk."""
        data = {prompt_name: [v.to_dict() for v in versions] for prompt_name, versions in self.versions.items()}
        self.version_index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _compute_version_id(self, content: str) -> VersionID:
        """Generate version ID from content hash."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _infer_prompt_type(self, prompt_name: PromptName) -> Literal["classification", "validation"]:
        """Infer prompt type from name."""
        if "classification" in prompt_name.lower():
            return "classification"
        elif "validation" in prompt_name.lower():
            return "validation"
        return "validation"  # Default

    def discover_prompts(self) -> list[dict[str, Any]]:
        """Discover all prompts in the prompts directory."""
        prompts = []

        # Find all .txt files
        for prompt_file in self.prompts_dir.rglob("*.txt"):
            relative_path = prompt_file.relative_to(self.prompts_dir)
            prompt_name = str(relative_path).replace(".txt", "").replace("/", "_").replace("\\", "_")

            prompts.append(
                {
                    "name": prompt_name,
                    "file_path": str(prompt_file),
                    "type": self._infer_prompt_type(prompt_name),
                    "relative_path": str(relative_path),
                }
            )

        return prompts

    def get_current_content(self, prompt_name: PromptName) -> str | None:
        """Get current active content for a prompt from filesystem."""
        # Try different path variations
        possible_paths = [
            self.prompts_dir / f"{prompt_name}.txt",
            self.prompts_dir / "specialised" / f"{prompt_name}.txt",
            self.prompts_dir / f"{prompt_name.replace('_', '/', 1)}.txt",
        ]

        for path in possible_paths:
            if path.exists():
                return cast(str, path.read_text(encoding="utf-8"))

        return None

    def create_snapshot(
        self,
        prompt_name: PromptName,
        content: str | None = None,
        author: str = "system",
        description: str = "Snapshot created",
        metadata: dict[str, Any] | None = None,
        parent_version_id: VersionID | None = None,
    ) -> PromptVersion:
        """Create a new version snapshot of a prompt.

        If content is None, reads current content from filesystem.
        """
        if content is None:
            content = self.get_current_content(prompt_name)
            if content is None:
                raise ValueError(f"Prompt {prompt_name} not found")

        version_id = self._compute_version_id(content)

        # Check if this exact version already exists
        existing_versions = self.versions.get(prompt_name, [])
        if any(v.version_id == version_id for v in existing_versions):
            # Return existing version
            return next(v for v in existing_versions if v.version_id == version_id)

        # Determine parent version and version number
        version_number = 0
        if parent_version_id is None:
            # If not explicitly provided, use current active version as parent
            if existing_versions:
                active_versions = [v for v in existing_versions if v.is_active]
                if active_versions:
                    parent_version_id = active_versions[0].version_id
                    version_number = active_versions[0].version_number + 1
        else:
            # If parent provided, increment from parent's version
            parent = next(
                (v for v in existing_versions if v.version_id == parent_version_id),
                None,
            )
            if parent:
                version_number = parent.version_number + 1

        # Create new version
        version = PromptVersion(
            version_id=version_id,
            version_number=version_number,
            prompt_name=prompt_name,
            prompt_type=self._infer_prompt_type(prompt_name),
            content=content,
            timestamp=datetime.now(UTC),
            author=author,
            description=description,
            parent_version_id=parent_version_id,
            is_active=True,  # New snapshot becomes active
            metadata=metadata or {},
        )

        # Deactivate previous active versions
        for v in existing_versions:
            if v.is_active:
                v.is_active = False

        # Store version
        if prompt_name not in self.versions:
            self.versions[prompt_name] = []
        self.versions[prompt_name].append(version)
        self._save_version_index()

        return version

    def snapshot_all_prompts(
        self, author: str = "system", description: str = "Initial snapshot"
    ) -> list[PromptVersion]:
        """Create snapshots of all discovered prompts."""
        prompts = self.discover_prompts()
        snapshots = []

        for prompt in prompts:
            try:
                snapshot = self.create_snapshot(
                    prompt_name=prompt["name"],
                    author=author,
                    description=description,
                    metadata={"file_path": prompt["file_path"]},
                )
                snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Failed to snapshot {prompt['name']}: {e}")

        return snapshots

    def get_version_history(self, prompt_name: PromptName) -> list[PromptVersion]:
        """Get all versions of a prompt, sorted by timestamp (newest first)."""
        versions = self.versions.get(prompt_name, [])
        return sorted(versions, key=lambda v: v.timestamp, reverse=True)

    def get_active_version(self, prompt_name: PromptName) -> PromptVersion | None:
        """Get the currently active version of a prompt."""
        versions = self.versions.get(prompt_name, [])
        active = [v for v in versions if v.is_active]
        return active[0] if active else None

    def get_version(self, prompt_name: PromptName, version_id: VersionID) -> PromptVersion | None:
        """Get a specific version by ID."""
        versions = self.versions.get(prompt_name, [])
        return next((v for v in versions if v.version_id == version_id), None)

    def delete_version(self, prompt_name: PromptName, version_id: VersionID) -> bool:
        """Delete a specific version.

        Args:
            prompt_name: Name of the prompt
            version_id: Version ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If trying to delete version 0 or the active version
        """
        version = self.get_version(prompt_name, version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found for {prompt_name}")

        # Never allow deleting version 0 (the original)
        if version.version_number == 0:
            raise ValueError("Cannot delete version 0 (the original version)")

        # Don't allow deleting the active version
        if version.is_active:
            raise ValueError("Cannot delete the active version. Activate another version first.")

        # Remove the version
        versions = self.versions.get(prompt_name, [])
        self.versions[prompt_name] = [v for v in versions if v.version_id != version_id]
        self._save_version_index()

        return True

    def activate_version(
        self,
        prompt_name: PromptName,
        version_id: VersionID,
        update_filesystem: bool = True,
    ) -> PromptVersion:
        """Activate (rollback to) a specific version.

        Args:
            prompt_name: Name of the prompt
            version_id: Version ID to activate
            update_filesystem: If True, updates the actual prompt file

        Returns:
            The activated version
        """
        version = self.get_version(prompt_name, version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found for {prompt_name}")

        # Deactivate all other versions
        for v in self.versions.get(prompt_name, []):
            v.is_active = False

        # Activate target version
        version.is_active = True
        self._save_version_index()

        # Update filesystem if requested
        if update_filesystem:
            self._write_prompt_to_filesystem(prompt_name, version.content)

        return version

    def _write_prompt_to_filesystem(self, prompt_name: PromptName, content: str) -> None:
        """Write prompt content to filesystem."""
        # Determine file path (try common patterns)
        possible_paths = [
            self.prompts_dir / f"{prompt_name}.txt",
            self.prompts_dir / "specialised" / f"{prompt_name}.txt",
        ]

        # Find existing file
        target_path = None
        for path in possible_paths:
            if path.exists():
                target_path = path
                break

        # If not found, use first option
        if target_path is None:
            target_path = possible_paths[0]

        # Backup current version before overwriting
        if target_path.exists():
            backup_dir = self.versions_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{prompt_name}_{timestamp}.txt"
            shutil.copy(target_path, backup_path)

        # Write new content
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    def update_prompt(
        self,
        prompt_name: PromptName,
        new_content: str,
        author: str = "user",
        description: str = "Updated prompt",
        metadata: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Update a prompt with new content, creating a new version."""
        # Create new version
        new_version = self.create_snapshot(
            prompt_name=prompt_name,
            content=new_content,
            author=author,
            description=description,
            metadata=metadata,
        )

        # Write to filesystem
        self._write_prompt_to_filesystem(prompt_name, new_content)

        return new_version

    def compare_versions(
        self,
        prompt_name: PromptName,
        version_id_a: VersionID,
        version_id_b: VersionID,
    ) -> dict[str, Any]:
        """Compare two versions and return diff information."""
        version_a = self.get_version(prompt_name, version_id_a)
        version_b = self.get_version(prompt_name, version_id_b)

        if not version_a or not version_b:
            raise ValueError("One or both versions not found")

        # Simple line-by-line diff
        lines_a = version_a.content.splitlines()
        lines_b = version_b.content.splitlines()

        return {
            "version_a": {
                "version_id": version_a.version_id,
                "timestamp": version_a.timestamp.isoformat(),
                "author": version_a.author,
                "description": version_a.description,
            },
            "version_b": {
                "version_id": version_b.version_id,
                "timestamp": version_b.timestamp.isoformat(),
                "author": version_b.author,
                "description": version_b.description,
            },
            "diff": {
                "lines_added": len(lines_b) - len(lines_a),
                "content_a": version_a.content,
                "content_b": version_b.content,
            },
        }

    def get_all_prompts_summary(self) -> list[dict[str, Any]]:
        """Get summary of all prompts with version counts."""
        discovered = self.discover_prompts()

        summary = []
        for prompt in discovered:
            name = prompt["name"]
            versions = self.get_version_history(name)
            active_version = self.get_active_version(name)

            summary.append(
                {
                    "name": name,
                    "type": prompt["type"],
                    "file_path": prompt["file_path"],
                    "version_count": len(versions),
                    "active_version_id": active_version.version_id if active_version else None,
                    "last_updated": versions[0].timestamp.isoformat() if versions else None,
                    "last_author": versions[0].author if versions else None,
                }
            )

        return sorted(summary, key=lambda x: x["name"])

    def migrate_version_numbers(self) -> dict[str, Any]:
        """Migrate existing versions to add version_number field.

        For prompts with versions missing version_number, assign them based on timestamp order.
        The oldest version gets 0, then increments from there.

        Returns:
            Dictionary with migration statistics
        """
        migrated_count = 0
        prompt_count = 0

        for _prompt_name, versions in self.versions.items():
            # Check if migration is needed (version_number is 0 for all due to default in from_dict)
            # We need to assign proper sequential numbers based on timestamp
            if len(versions) > 0:
                # Sort by timestamp (oldest first)
                versions_sorted = sorted(versions, key=lambda v: v.timestamp)

                # Check if version numbers are sequential (0, 1, 2, ...)
                expected_numbers = list(range(len(versions_sorted)))
                actual_numbers = sorted([v.version_number for v in versions_sorted])

                needs_migration = actual_numbers != expected_numbers

                if needs_migration:
                    prompt_count += 1
                    # Assign version numbers based on timestamp order
                    for i, version in enumerate(versions_sorted):
                        if version.version_number != i:
                            version.version_number = i
                            migrated_count += 1

                    self._save_version_index()

        return {
            "migrated_versions": migrated_count,
            "migrated_prompts": prompt_count,
        }

    def validate_prompt_sync(self, prompt_name: PromptName) -> dict[str, Any]:
        """Validate that filesystem and version index are in sync.

        Returns:
            Dictionary with sync status and details
        """
        filesystem_content = self.get_current_content(prompt_name)
        active_version = self.get_active_version(prompt_name)

        if not filesystem_content:
            return {
                "in_sync": False,
                "error": "Prompt not found on filesystem",
                "prompt_name": prompt_name,
            }

        if not active_version:
            return {
                "in_sync": False,
                "error": "No active version in index",
                "prompt_name": prompt_name,
                "filesystem_hash": self._compute_version_id(filesystem_content),
            }

        filesystem_hash = self._compute_version_id(filesystem_content)
        in_sync = filesystem_hash == active_version.version_id

        return {
            "in_sync": in_sync,
            "prompt_name": prompt_name,
            "filesystem_hash": filesystem_hash,
            "active_version_hash": active_version.version_id,
            "active_version": {
                "timestamp": active_version.timestamp.isoformat(),
                "author": active_version.author,
                "description": active_version.description,
            }
            if active_version
            else None,
        }
