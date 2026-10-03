"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def isolate_global_config(tmp_path_factory, monkeypatch):
    """Keep every test away from the user's real ~/.keecas/config.toml.

    Points HOME/USERPROFILE at a throwaway directory, so any ConfigManager built
    during a test resolves its global config path there. The import-time
    singleton resolved its path before any fixture ran, so it is redirected too.
    """
    fake_home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))

    from keecas.config import get_config_manager

    monkeypatch.setattr(
        get_config_manager(),
        "_global_config_path",
        fake_home / ".keecas" / "config.toml",
    )
