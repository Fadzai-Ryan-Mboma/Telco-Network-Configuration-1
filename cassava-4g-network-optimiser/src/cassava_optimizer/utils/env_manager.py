"""
Environment Variable Manager with .env Persistence.

Provides functionality to read, update, and persist environment variables
to the .env file with backup and restore capabilities.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class EnvManager:
    """
    Manages environment variables with .env file persistence.
    
    Features:
    - Read/write .env file
    - Batch updates with Save button
    - Automatic backup before changes
    - Restore from backup on failure
    - Restart prompt after changes
    """
    
    def __init__(self, env_path: str | Path | None = None) -> None:
        """
        Initialize the env manager.
        
        Args:
            env_path: Path to .env file. Defaults to project root.
        """
        if env_path is None:
            # Look for .env in app directory or project root
            possible_paths = [
                Path("/app/.env"),  # Docker
                Path.cwd() / ".env",
                Path(__file__).parent.parent.parent.parent.parent / ".env",
            ]
            for path in possible_paths:
                if path.exists():
                    self.env_path = path
                    break
            else:
                # Default to project root
                self.env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        else:
            self.env_path = Path(env_path)
        
        self.backup_dir = self.env_path.parent / ".env_backups"
        self._pending_changes: dict[str, str] = {}
        
        logger.info(f"EnvManager initialized with path: {self.env_path}")
    
    def read_env(self) -> dict[str, str]:
        """
        Read all variables from .env file.
        
        Returns:
            Dictionary of environment variables
        """
        env_vars: dict[str, str] = {}
        
        if not self.env_path.exists():
            logger.warning(f".env file not found at {self.env_path}")
            return env_vars
        
        try:
            with open(self.env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Parse KEY=value
                    if "=" in line:
                        key, _, value = line.partition("=")
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        env_vars[key.strip()] = value
            
            logger.debug(f"Read {len(env_vars)} variables from .env")
            return env_vars
            
        except Exception as e:
            logger.error(f"Failed to read .env: {e}")
            return {}
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get a specific environment variable.
        
        Checks pending changes first, then .env file, then os.environ.
        
        Args:
            key: Variable name
            default: Default value if not found
            
        Returns:
            Variable value
        """
        # Check pending changes first
        if key in self._pending_changes:
            return self._pending_changes[key]
        
        # Then check .env file
        env_vars = self.read_env()
        if key in env_vars:
            return env_vars[key]
        
        # Fall back to os.environ
        return os.environ.get(key, default)
    
    def set_pending(self, key: str, value: str) -> None:
        """
        Set a pending change (not yet saved).
        
        Args:
            key: Variable name
            value: New value
        """
        self._pending_changes[key] = value
        logger.debug(f"Pending change: {key}={value[:20]}...")
    
    def set_pending_batch(self, changes: dict[str, str]) -> None:
        """
        Set multiple pending changes.
        
        Args:
            changes: Dictionary of key-value pairs
        """
        self._pending_changes.update(changes)
        logger.debug(f"Pending {len(changes)} changes")
    
    def get_pending_changes(self) -> dict[str, str]:
        """Get all pending changes."""
        return self._pending_changes.copy()
    
    def clear_pending(self) -> None:
        """Clear all pending changes without saving."""
        self._pending_changes.clear()
        logger.debug("Pending changes cleared")
    
    def has_pending_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return len(self._pending_changes) > 0
    
    def create_backup(self) -> Path | None:
        """
        Create a backup of the current .env file.
        
        Returns:
            Path to backup file, or None if failed
        """
        if not self.env_path.exists():
            return None
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f".env.backup_{timestamp}"
            shutil.copy2(self.env_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_path: Path | None = None) -> bool:
        """
        Restore .env from a backup.
        
        Args:
            backup_path: Specific backup to restore. If None, uses most recent.
            
        Returns:
            True if restore successful
        """
        try:
            if backup_path is None:
                # Find most recent backup
                if not self.backup_dir.exists():
                    logger.error("No backup directory found")
                    return False
                
                backups = sorted(self.backup_dir.glob(".env.backup_*"), reverse=True)
                if not backups:
                    logger.error("No backups found")
                    return False
                
                backup_path = backups[0]
            
            shutil.copy2(backup_path, self.env_path)
            logger.info(f"Restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> list[Path]:
        """
        List all available backups.
        
        Returns:
            List of backup file paths, newest first
        """
        if not self.backup_dir.exists():
            return []
        
        return sorted(self.backup_dir.glob(".env.backup_*"), reverse=True)
    
    def save(self) -> tuple[bool, str]:
        """
        Save all pending changes to .env file.
        
        Creates a backup before saving.
        
        Returns:
            Tuple of (success, message)
        """
        if not self._pending_changes:
            return True, "No changes to save"
        
        try:
            # Create backup first
            backup_path = self.create_backup()
            
            # Read existing content
            existing_vars = self.read_env()
            
            # Read file to preserve comments and structure
            lines: list[str] = []
            updated_keys: set[str] = set()
            
            if self.env_path.exists():
                with open(self.env_path, "r") as f:
                    for line in f:
                        original_line = line
                        line_stripped = line.strip()
                        
                        # Preserve comments and empty lines
                        if not line_stripped or line_stripped.startswith("#"):
                            lines.append(original_line)
                            continue
                        
                        # Check if this line should be updated
                        if "=" in line_stripped:
                            key = line_stripped.split("=", 1)[0].strip()
                            if key in self._pending_changes:
                                lines.append(f"{key}={self._pending_changes[key]}\n")
                                updated_keys.add(key)
                            else:
                                lines.append(original_line)
                        else:
                            lines.append(original_line)
            
            # Add new keys that weren't in the file
            for key, value in self._pending_changes.items():
                if key not in updated_keys:
                    lines.append(f"{key}={value}\n")
            
            # Write to file
            with open(self.env_path, "w") as f:
                f.writelines(lines)
            
            # Update os.environ for immediate effect (where possible)
            for key, value in self._pending_changes.items():
                os.environ[key] = value
            
            changes_count = len(self._pending_changes)
            self._pending_changes.clear()
            
            logger.info(f"Saved {changes_count} changes to .env")
            return True, f"Saved {changes_count} changes. Backup created at {backup_path}"
            
        except Exception as e:
            logger.error(f"Failed to save .env: {e}")
            # Attempt restore
            if backup_path:
                self.restore_backup(backup_path)
            return False, f"Failed to save: {e}"
    
    def delete_old_backups(self, keep_count: int = 10) -> int:
        """
        Delete old backups, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        deleted = 0
        
        for backup in backups[keep_count:]:
            try:
                backup.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup}: {e}")
        
        if deleted:
            logger.info(f"Deleted {deleted} old backups")
        
        return deleted


# Singleton instance
_env_manager: EnvManager | None = None


def get_env_manager() -> EnvManager:
    """Get singleton EnvManager instance."""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvManager()
    return _env_manager


# Convenience functions
def get_env(key: str, default: str = "") -> str:
    """Get environment variable."""
    return get_env_manager().get(key, default)


def set_env_pending(key: str, value: str) -> None:
    """Set pending environment change."""
    get_env_manager().set_pending(key, value)


def save_env() -> tuple[bool, str]:
    """Save pending environment changes."""
    return get_env_manager().save()


def restore_env() -> bool:
    """Restore environment from latest backup."""
    return get_env_manager().restore_backup()


def update_env(updates: dict[str, str]) -> bool:
    """
    Update multiple environment variables and save immediately.
    
    Convenience function that sets all pending changes and saves.
    
    Args:
        updates: Dictionary of key-value pairs to update
        
    Returns:
        True if save was successful
    """
    manager = get_env_manager()
    manager.set_pending_batch(updates)
    success, _ = manager.save()
    return success
