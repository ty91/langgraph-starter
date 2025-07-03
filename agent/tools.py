import logging
import os
import shutil
import tarfile
import tempfile
from typing import Any, Dict

import aiofiles
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool(description="Initialize a new version for the app")
async def setup_new_version() -> Dict[str, Any]:
    try:
        current_version = 0
        new_version = current_version + 1

        version_dir = f"/tmp/agentflow/v{new_version}"
        os.makedirs(version_dir, exist_ok=True)

        logger.info(f"Created version directory: {version_dir}")

        return {
            "success": True,
            "version": new_version,
            "path": version_dir,
        }
    except Exception as e:
        logger.error(f"Error setting up new version: {e}")
        return {"error": str(e)}


@tool(description="Create a file in the specified version directory")
async def create_file(path: str, content: str, version: int) -> Dict[str, Any]:
    try:
        version_dir = f"/tmp/agentflow/v{version}"
        full_path = os.path.join(version_dir, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)

        logger.info(f"Created file: {full_path}")

        return {
            "success": True,
            "path": path,
            "fullPath": full_path,
        }
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        return {"error": str(e)}


@tool(description="Save the version by creating a tar.gz and uploading to storage")
async def save_version(version: int) -> Dict[str, Any]:
    try:
        version_dir = f"/tmp/agentflow/v{version}"

        if not os.path.exists(version_dir):
            return {"error": f"Version directory not found: {version_dir}"}

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
            tar_path = tmp_file.name

        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(version_dir, arcname=".")

        storage_path = f"v{version}.tar.gz"

        os.unlink(tar_path)

        shutil.rmtree(version_dir)

        logger.info(f"Saved version {version}")

        return {
            "success": True,
            "version": version,
            "storage_path": storage_path,
        }
    except Exception as e:
        logger.error(f"Error saving version: {e}")
        return {"error": str(e)}


tools = [
    setup_new_version,
    create_file,
    save_version,
]
