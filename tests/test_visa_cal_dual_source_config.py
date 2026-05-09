from __future__ import annotations

import json
import pathlib

import pytest

from etl_pipeline import config_loader


def _write_config(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_source_paths_supports_dual_visa_cal_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    config_path = tmp_path / "private_data" / "sources_config.json"
    payload = {
        "ynab_folder": "private_data/incoming/ynab",
        "sources": {
            "Mizrachi": "private_data/incoming/mizrachi_joint",
            "Bank Leumi": "private_data/incoming/bank_leumi_private_shai",
            "Bank Hapoalim": "private_data/incoming/bank_hapoalim_private_shai",
            "Max Uniq": "private_data/incoming/max_uniq_joint",
            "Visa Cal 4779": "private_data/incoming/mastercard_4779_private",
            "Visa Cal 7353": "private_data/incoming/mastercard_7353_private",
            "Isracard": "private_data/incoming/isracard_4054_joint",
        },
    }
    _write_config(config_path, payload)

    monkeypatch.setattr(config_loader, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config_loader, "_CONFIG_PATH", config_path)

    paths = config_loader.load_source_paths()

    assert "Visa Cal 4779" in paths.sources
    assert "Visa Cal 7353" in paths.sources
    assert paths.sources["Visa Cal 4779"].endswith("private_data/incoming/mastercard_4779_private")
    assert paths.sources["Visa Cal 7353"].endswith("private_data/incoming/mastercard_7353_private")


def test_get_source_folder_fails_when_second_visa_cal_key_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    config_path = tmp_path / "private_data" / "sources_config.json"
    payload = {
        "ynab_folder": "private_data/incoming/ynab",
        "sources": {
            "Mizrachi": "private_data/incoming/mizrachi_joint",
            "Bank Leumi": "private_data/incoming/bank_leumi_private_shai",
            "Bank Hapoalim": "private_data/incoming/bank_hapoalim_private_shai",
            "Max Uniq": "private_data/incoming/max_uniq_joint",
            "Visa Cal 4779": "private_data/incoming/mastercard_4779_private",
            "Isracard": "private_data/incoming/isracard_4054_joint",
        },
    }
    _write_config(config_path, payload)

    monkeypatch.setattr(config_loader, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config_loader, "_CONFIG_PATH", config_path)

    with pytest.raises(KeyError):
        config_loader.get_source_folder("Visa Cal 7353")


def test_source_registry_declares_both_visa_cal_entries() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    consolidate_py = repo_root / "etl_pipeline" / "consolidate.py"
    text = consolidate_py.read_text(encoding="utf-8")

    assert 'name="Visa Cal 4779"' in text
    assert 'name="Visa Cal 7353"' in text
    assert '_paths.sources["Visa Cal 4779"]' in text
    assert '_paths.sources["Visa Cal 7353"]' in text
