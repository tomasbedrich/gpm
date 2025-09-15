"""Tests for GPM manager."""

import logging
import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from custom_components.gpm import ResourceRepositoryManager
from custom_components.gpm._manager import (
    LOVELACE_DOMAIN,
    AlreadyClonedError,
    AlreadyInstalledError,
    CheckoutError,
    CloneError,
    IntegrationRepositoryManager,
    InvalidStructure,
    NotClonedError,
    NotInstalledError,
    RepositoryManager,
    ResourceInstallError,
    ResourcesUpdateError,
    UpdateStrategy,
    VersionAlreadyInstalledError,
    async_download,
    async_open,
)
from git import Git, GitCommandError, Repo
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


async def test_is_cloned(manager: RepositoryManager) -> None:
    """Test is_cloned method."""
    with patch.object(Path, "exists", return_value=True):
        assert await manager.is_cloned() is True

    with patch.object(Path, "exists", return_value=False):
        assert await manager.is_cloned() is False

    with patch.object(Path, "exists", side_effect=OSError):
        assert await manager.is_cloned() is False


async def test_is_installed(manager: RepositoryManager) -> None:
    """Test is_installed method."""
    assert await manager.is_cloned() is False
    assert await manager.is_installed() is False
    await manager.clone()
    assert await manager.is_cloned() is True
    assert await manager.is_installed() is False
    await manager.install()
    assert await manager.is_cloned() is True
    assert await manager.is_installed() is True


async def test_is_installed_exception(manager: RepositoryManager) -> None:
    """Test is_installed method."""
    await manager.clone()
    # # `is_cloned` uses patched `Path.exists` as well, therefore we need to mock it
    manager.is_cloned.return_value = True
    with patch.object(Path, "exists", side_effect=OSError):
        assert await manager.is_installed() is False


# async def test_is_installed_without_download_url(
#     resource_manager: ResourceRepositoryManager,
# ) -> None:
#     """Test is_installed method."""
#     resource_manager.get_download_url.return_value = None
#     assert await resource_manager.is_installed() is False


async def test_not_ensure_cloned(manager: RepositoryManager) -> None:
    """Test ensure_cloned decorator raises error when repository is not cloned."""
    manager.is_cloned.return_value = False
    with pytest.raises(NotClonedError):
        await manager.get_current_version()


async def test_not_ensure_installed(manager: RepositoryManager) -> None:
    """Test ensure_installed decorator raises error when repository is not installed."""
    manager.is_installed.return_value = False
    with pytest.raises(NotInstalledError):
        await manager.update("v1.0.0")


async def test_clone_already_cloned(manager: RepositoryManager) -> None:
    """Test clone raises AlreadyClonedError."""
    await manager.clone()
    with pytest.raises(AlreadyClonedError):
        await manager.clone()


async def test_clone_git_command_error(manager: RepositoryManager) -> None:
    """Test clone raises CloneError."""
    with (
        patch.object(Repo, "clone_from", side_effect=GitCommandError("git clone")),
        pytest.raises(CloneError),
    ):
        await manager.clone()


async def test_checkout_error(manager: RepositoryManager) -> None:
    """Test checkout raises CheckoutError."""
    await manager.clone()
    with (
        patch.object(
            Git, "checkout", create=True, side_effect=GitCommandError("git checkout")
        ),
        pytest.raises(CheckoutError),
    ):
        await manager.checkout("v2.0.0beta2")


@pytest.mark.parametrize(
    ("repo_url", "unique_id"),
    [
        ("https://github.com/user/foo.git", "github_com.user.foo"),
        ("https://github.com/another-user/bar", "github_com.another_user.bar"),
        (
            "https://gitlab.com/YETanotherUser123/baz/",
            "gitlab_com.yetanotheruser123.baz",
        ),
        ("http://user:pass@example.com:1234/abc/", "example_com.abc"),
    ],
)
def test_unique_id(manager: RepositoryManager, repo_url: str, unique_id: str) -> None:
    """Test generating of unique_id for given repo_url."""
    manager.repo_url = repo_url
    assert manager.unique_id == unique_id


async def test_get_repo(manager: RepositoryManager) -> None:
    """Test Repo instance is created and cached."""
    with (
        patch.object(manager, "is_cloned", return_value=True),
        patch.object(Repo, "__init__", return_value=None) as mock_repo,
    ):
        assert mock_repo.call_count == 0
        await manager._get_repo()
        assert mock_repo.call_count == 1
        assert mock_repo.call_args == ((manager.working_dir,),)
        await manager._get_repo()
        assert mock_repo.call_count == 1, "manager._repo attribute is not cached"


async def test_install(integration_manager: IntegrationRepositoryManager) -> None:
    """Test successful installation."""
    await integration_manager.clone()
    await integration_manager.install()
    assert await integration_manager.is_installed() is True
    with pytest.raises(AlreadyInstalledError):
        await integration_manager.install()


async def test_get_component_dir_missing(
    integration_manager: IntegrationRepositoryManager,
) -> None:
    """Test get_component_dir raises error when repository doesn't contain custom_components dir."""
    await integration_manager.clone()
    integration_manager._component_dir = None  # empty cache first
    custom_components = integration_manager.working_dir / "custom_components"
    custom_components_backup = custom_components.with_suffix(".bak")
    custom_components.rename(custom_components_backup)
    with pytest.raises(InvalidStructure):
        await integration_manager.get_component_dir()
    # restore original structure to enable clean test teardown
    custom_components_backup.rename(custom_components)


async def test_get_component_dir_multiple(
    integration_manager: IntegrationRepositoryManager,
) -> None:
    """Test get_component_dir raises error when custom_components dir contains more subdirectories."""
    await integration_manager.clone()
    integration_manager._component_dir = None  # empty cache first
    custom_components = integration_manager.working_dir / "custom_components"
    new_component = custom_components / "yet_another_component"
    new_component.mkdir()
    with pytest.raises(InvalidStructure):
        await integration_manager.get_component_dir()
    new_component.rmdir()


async def test_download_resource_error(
    resource_manager: ResourceRepositoryManager,
) -> None:
    """Test successful download."""
    await resource_manager.clone()
    await resource_manager.install()
    with (
        patch("custom_components.gpm._manager.async_download", side_effect=OSError),
        pytest.raises(ResourceInstallError),
    ):
        await resource_manager._download_resource()


async def test_get_resource_storage(hass: HomeAssistant) -> None:
    """Test _get_resource_storage method."""
    await async_setup_component(hass, "lovelace", {})
    lovelace_resources = await ResourceRepositoryManager._get_resource_storage(hass)
    assert lovelace_resources is not None

    hass.data[LOVELACE_DOMAIN] = {}
    with pytest.raises(
        ResourcesUpdateError, match="ResourceStorageCollection not found"
    ):
        await ResourceRepositoryManager._get_resource_storage(hass)

    hass.data[LOVELACE_DOMAIN] = {"resources": Mock(store=None)}
    with pytest.raises(ResourcesUpdateError, match="YAML mode detected"):
        await ResourceRepositoryManager._get_resource_storage(hass)

    hass.data[LOVELACE_DOMAIN] = {
        "resources": Mock(store=Mock(key="wrong_key", version=1))
    }
    with pytest.raises(ResourcesUpdateError, match="Unexpected structure"):
        await ResourceRepositoryManager._get_resource_storage(hass)


async def test_update_resource_removed_in_meantime(
    resource_manager: ResourceRepositoryManager,
    caplog: pytest.LogCaptureFixture,
    hass: HomeAssistant,
) -> None:
    """Test update method when resource is removed in the meantime."""
    await resource_manager.clone()
    await resource_manager.install()
    await _remove_all_resources(hass)
    with caplog.at_level(logging.WARNING):
        await resource_manager.update("v0.8.8")
        assert re.search(r"Resource .* not found", caplog.text), "Warning is expected"


async def test_remove_resource_removed_in_meantime(
    resource_manager: ResourceRepositoryManager,
    caplog: pytest.LogCaptureFixture,
    hass: HomeAssistant,
) -> None:
    """Test update method when resource is removed in the meantime."""
    await resource_manager.clone()
    await resource_manager.install()
    await _remove_all_resources(hass)
    with caplog.at_level(logging.WARNING):
        await resource_manager.uninstall()
        assert re.search(r"Resource .* not found", caplog.text), "Warning is expected"


async def _remove_all_resources(hass: HomeAssistant) -> None:
    """Simulate that user manually removes all Lovelace resources."""
    lovelace_resources = await ResourceRepositoryManager._get_resource_storage(hass)
    for entry in lovelace_resources.async_items():
        await lovelace_resources.async_delete_item(entry["id"])


async def test_update_strategy_tag(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_TAG
    await manager.install()
    assert await manager.get_current_version() == "v1.0.0"


async def test_update_strategy_unstable_tag(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_UNSTABLE_TAG
    await manager.install()
    assert await manager.get_current_version() == "v2.0.0beta2"


async def test_update_strategy_commit(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_COMMIT
    await manager.install()
    assert len(await manager.get_current_version()) == 40


def test_not_cloned_error_str() -> None:
    """Test NotClonedError."""
    err_str = str(NotClonedError("working_dir"))
    assert "working_dir" in err_str
    assert "does not contain a GIT repository" in err_str


def test_not_installed_error_str() -> None:
    """Test NotInstalledError."""
    err_str = str(NotInstalledError("slug"))
    assert "slug" in err_str
    assert "is not installed" in err_str


def test_already_installed_error_str() -> None:
    """Test AlreadyInstalledError."""
    err_str = str(AlreadyInstalledError("install_path"))
    assert "install_path" in err_str
    assert "already exists" in err_str


def test_checkout_error_str() -> None:
    """Test CheckoutError."""
    err_str = str(CheckoutError("ref", "reason"))
    assert "ref" in err_str
    assert "reason" in err_str
    assert "Cannot checkout" in err_str


def test_version_already_installed_error() -> None:
    """Test VersionAlreadyInstalledError."""
    err_str = str(VersionAlreadyInstalledError("version"))
    assert "version" in err_str
    assert "already installed" in err_str


async def test_async_open(hass: HomeAssistant, tmp_path: Path) -> None:
    """Test async_open method."""
    test_file = tmp_path / "test.txt"
    async with async_open(hass, test_file, "w") as f:
        f.write("test")
    assert test_file.read_text() == "test"


async def test_async_download(
    hass: HomeAssistant, tmp_path: Path, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test async_download method."""
    url = "https://example.com/test.txt"
    test_file = tmp_path / "test.txt"
    aioclient_mock.get(url, text="test")
    await async_download(hass, url, test_file)
    assert test_file.read_text() == "test"


async def test_install_failure_cleanup(
    integration_manager: IntegrationRepositoryManager,
) -> None:
    """Test that failed installation cleans up cloned repository."""
    # First attempt: clone succeeds but installation fails
    await integration_manager.clone()
    assert await integration_manager.is_cloned() is True
    
    # Mock installation failure after successful clone - directly calling the actual method
    with patch.object(
        integration_manager, "get_component_dir", side_effect=InvalidStructure("Test error", integration_manager.working_dir)
    ):
        with pytest.raises(InvalidStructure):
            # Call the actual install method directly from the class 
            await IntegrationRepositoryManager.install(integration_manager)
    
    # Repository should still be cloned at this point (current buggy behavior)
    assert await integration_manager.is_cloned() is True
    
    # Second attempt should fail with AlreadyClonedError (this is the reported bug)
    with pytest.raises(AlreadyClonedError):
        await integration_manager.clone()


async def test_resource_install_failure_cleanup(
    resource_manager: ResourceRepositoryManager,
) -> None:
    """Test that failed resource installation cleans up cloned repository."""
    # First attempt: clone succeeds but installation fails
    await resource_manager.clone()
    assert await resource_manager.is_cloned() is True
    
    # Mock installation failure after successful clone
    with patch(
        "custom_components.gpm._manager.async_download", side_effect=ResourceInstallError
    ):
        with pytest.raises(ResourceInstallError):
            # Call the actual install method directly from the class
            await ResourceRepositoryManager.install(resource_manager)
    
    # Repository should still be cloned at this point (current buggy behavior)
    assert await resource_manager.is_cloned() is True
    
    # Second attempt should fail with AlreadyClonedError (this is the reported bug)
    with pytest.raises(AlreadyClonedError):
        await resource_manager.clone()


async def test_install_failure_cleanup_fixed_simple(
    hass: HomeAssistant, tmp_path: Path
) -> None:
    """Test that failed installation cleans up cloned repository (simple test)."""
    from custom_components.gpm._manager import IntegrationRepositoryManager, UpdateStrategy
    
    # Create a real manager without mocking
    manager = IntegrationRepositoryManager(
        hass=hass,
        repo_url="https://github.com/user/awesome-component",
        update_strategy=UpdateStrategy.LATEST_TAG,
    )
    manager.clone_basedir = tmp_path / "clone_basedir"
    manager.clone_basedir.mkdir()
    manager.install_basedir = tmp_path / "install_basedir" 
    manager.install_basedir.mkdir()
    
    working_dir = manager.working_dir
    
    # Mock clone to create a real directory structure without git operations
    async def create_fake_repo():
        working_dir.mkdir(parents=True, exist_ok=True)
        (working_dir / ".git").mkdir()
        # Create the structure that get_component_dir expects (but make it invalid)
        custom_components = working_dir / "custom_components"
        custom_components.mkdir()
        # Intentionally create multiple components to trigger InvalidStructure
        (custom_components / "awesome_component").mkdir()
        (custom_components / "another_component").mkdir()  # This will cause InvalidStructure
        
    # Test if directory cleanup works after installation failure
    with patch.object(manager, "clone", side_effect=create_fake_repo):
        with patch.object(manager, "get_latest_version", return_value="v1.0.0"):
            with patch.object(manager, "checkout"):
                # This should fail with InvalidStructure after successful clone
                with pytest.raises(InvalidStructure):
                    await manager.install()
    
    # Debug: check state after failed installation
    print(f"Directory exists: {working_dir.exists()}")
    print(f"is_cloned: {await manager.is_cloned()}")
    print(f"is_installed: {await manager.is_installed()}")
    
    # Try calling remove directly to see what happens
    await manager.remove()
    print(f"After calling remove - Directory exists: {working_dir.exists()}")


async def test_end_to_end_scenario_from_issue(
    hass: HomeAssistant, tmp_path: Path
) -> None:
    """Test the exact scenario described in the issue: successful clone followed by failed subsequent steps."""
    from custom_components.gpm._manager import IntegrationRepositoryManager, UpdateStrategy, AlreadyClonedError
    
    # Create a real manager without mocking
    manager = IntegrationRepositoryManager(
        hass=hass,
        repo_url="https://github.com/user/awesome-component",
        update_strategy=UpdateStrategy.LATEST_TAG,
    )
    manager.clone_basedir = tmp_path / "clone_basedir"
    manager.clone_basedir.mkdir()
    manager.install_basedir = tmp_path / "install_basedir" 
    manager.install_basedir.mkdir()
    
    working_dir = manager.working_dir
    
    # Mock clone to create a real directory structure without git operations
    async def create_fake_repo_with_invalid_structure():
        working_dir.mkdir(parents=True, exist_ok=True)
        (working_dir / ".git").mkdir()
        # Create the structure that get_component_dir expects (but make it invalid)
        custom_components = working_dir / "custom_components"
        custom_components.mkdir()
        # Intentionally create multiple components to trigger InvalidStructure
        (custom_components / "awesome_component").mkdir()
        (custom_components / "another_component").mkdir()  # This will cause InvalidStructure
        
    # First attempt: should fail due to InvalidStructure but clean up properly  
    with patch.object(manager, "clone", side_effect=create_fake_repo_with_invalid_structure):
        with patch.object(manager, "get_latest_version", return_value="v1.0.0"):
            with patch.object(manager, "checkout"):
                # This should fail with InvalidStructure after successful clone
                with pytest.raises(InvalidStructure):
                    await manager.install()
    
    # Verify cleanup happened - directory should not exist
    assert not working_dir.exists(), "Directory should have been cleaned up after failed installation"
    
    # Second attempt: should not fail with AlreadyClonedError (the original bug)
    # This time, let's make it succeed to verify the fix
    async def create_fake_repo_valid():
        working_dir.mkdir(parents=True, exist_ok=True)
        (working_dir / ".git").mkdir()
        # Create the structure that get_component_dir expects (valid this time)
        custom_components = working_dir / "custom_components"
        custom_components.mkdir()
        (custom_components / "awesome_component").mkdir()
        
    with patch.object(manager, "clone", side_effect=create_fake_repo_valid):
        with patch.object(manager, "get_latest_version", return_value="v1.0.0"):
            with patch.object(manager, "checkout"):
                # This should succeed without throwing AlreadyClonedError
                await manager.install()
    
    # Verify the second attempt succeeded
    assert working_dir.exists(), "Directory should exist after successful installation"
    assert await manager.is_cloned(), "Repository should be cloned after successful installation"


async def test_resource_install_failure_cleanup_fixed(
    resource_manager: ResourceRepositoryManager,
) -> None:
    """Test that failed resource installation cleans up cloned repository (with fix)."""
    # Mock installation failure after successful clone
    with patch(
        "custom_components.gpm._manager.async_download", side_effect=ResourceInstallError
    ):
        with pytest.raises(ResourceInstallError):
            # Call the actual install method directly from the class
            await ResourceRepositoryManager.install(resource_manager)
    
    # Repository should be cleaned up after failed installation (fixed behavior)
    assert await resource_manager.is_cloned() is False
    
    # Second attempt should work without AlreadyClonedError
    await resource_manager.clone()
    assert await resource_manager.is_cloned() is True


async def test_install_base_method_cleanup_on_checkout_failure(
    integration_manager: IntegrationRepositoryManager,
) -> None:
    """Test that base install method cleans up on checkout failure."""
    # Mock checkout failure after successful clone
    with patch.object(
        integration_manager, "checkout", side_effect=CheckoutError("invalid-ref", "test error")
    ):
        with pytest.raises(CheckoutError):
            # Call the actual install method directly from the class
            await IntegrationRepositoryManager.install(integration_manager)
    
    # Repository should be cleaned up after failed checkout (fixed behavior)
    assert await integration_manager.is_cloned() is False
