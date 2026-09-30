from __future__ import annotations

import importlib.util
import sys

import pytest

from konftes import AKAR

pytest.importorskip("uvicorn")


def _jalan():
    spesifikasi = importlib.util.spec_from_file_location("jalan_uji", AKAR / "backend" / "jalan.py")
    modul = importlib.util.module_from_spec(spesifikasi)
    spesifikasi.loader.exec_module(modul)
    return modul


def test_ctrl_c_mematikan_dashboard_tanpa_traceback(monkeypatch, capsys):
    jalan = _jalan()

    def dihentikan(coro):
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(sys, "argv", ["jalan.py", "--port", "8765"])
    monkeypatch.setattr(jalan, "_soket_loopback", lambda _inang, _porta: None)
    monkeypatch.setattr(jalan.asyncio, "run", dihentikan)

    assert jalan.main() == 0
    assert "dashboard dimatikan" in capsys.readouterr().out
