"""字体发现与注册模块测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from newspaper_pdf.fonts import (
    FONT_CANDIDATES,
    _find_font_in_dirs,
    _get_system_font_dirs,
    resolve_fonts,
)


@pytest.mark.unit
class TestGetSystemFontDirs:
    def test_returns_list(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "platform", "linux")
        result = _get_system_font_dirs()
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_linux_dirs(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "platform", "linux")
        result = _get_system_font_dirs()
        assert Path("/usr/share/fonts") in result

    def test_darwin_dirs(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "platform", "darwin")
        result = _get_system_font_dirs()
        assert Path("/Library/Fonts") in result

    def test_win32_dirs(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("SystemRoot", "C:\\Windows")
        # 需要重新导入以触发模块级逻辑，或者直接验证函数返回类型
        result = _get_system_font_dirs()
        assert isinstance(result, list)


@pytest.mark.unit
class TestFindFontInDirs:
    def test_direct_match(self, tmp_path: Path) -> None:
        font_file = tmp_path / "simhei.ttf"
        font_file.write_text("fake font")
        result = _find_font_in_dirs("simhei.ttf", [tmp_path])
        assert result == font_file

    def test_recursive_match(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        font_file = sub / "simhei.ttf"
        font_file.write_text("fake font")
        result = _find_font_in_dirs("simhei.ttf", [tmp_path])
        assert result == font_file

    def test_not_found(self, tmp_path: Path) -> None:
        result = _find_font_in_dirs("nonexistent.ttf", [tmp_path])
        assert result is None

    def test_skips_nonexistent_dirs(self, tmp_path: Path) -> None:
        font_file = tmp_path / "simhei.ttf"
        font_file.write_text("fake font")
        bad_path = Path("/nonexistent/path")
        result = _find_font_in_dirs("simhei.ttf", [bad_path, tmp_path])
        assert result == font_file

    def test_empty_search_dirs(self) -> None:
        result = _find_font_in_dirs("simhei.ttf", [])
        assert result is None


@pytest.mark.unit
class TestResolveFonts:
    def test_custom_paths(self, tmp_path: Path) -> None:
        font_file = tmp_path / "simhei.ttf"
        font_file.write_text("fake font")
        result = resolve_fonts(custom_paths={"SimHei": font_file})
        assert "SimHei" in result
        assert result["SimHei"] == font_file

    def test_custom_path_not_exist(self, tmp_path: Path, monkeypatch) -> None:
        fake_path = tmp_path / "nonexistent.ttf"
        monkeypatch.delenv("NEWSPAPER_FONT_SIMHEI", raising=False)
        monkeypatch.delenv("NEWSPAPER_FONT_SIMSUN", raising=False)
        monkeypatch.delenv("NEWSPAPER_FONT_TIMES", raising=False)
        monkeypatch.setattr(
            "newspaper_pdf.fonts._get_system_font_dirs", lambda: [tmp_path]
        )
        with pytest.raises(RuntimeError, match="未找到任何中文字体"):
            resolve_fonts(custom_paths={"SimHei": fake_path}, font_dir=tmp_path)

    def test_font_dir(self, tmp_path: Path) -> None:
        font_file = tmp_path / "simsun.ttc"
        font_file.write_text("fake font")
        result = resolve_fonts(font_dir=tmp_path)
        assert "SimSun" in result

    def test_raises_without_cjk(self, tmp_path: Path, monkeypatch) -> None:
        # 清除环境变量，使用空目录，并替换系统字体目录
        monkeypatch.delenv("NEWSPAPER_FONT_SIMHEI", raising=False)
        monkeypatch.delenv("NEWSPAPER_FONT_SIMSUN", raising=False)
        monkeypatch.delenv("NEWSPAPER_FONT_TIMES", raising=False)
        monkeypatch.setattr(
            "newspaper_pdf.fonts._get_system_font_dirs", lambda: [tmp_path]
        )
        with pytest.raises(RuntimeError, match="未找到任何中文字体"):
            resolve_fonts(custom_paths={}, font_dir=tmp_path)

    def test_env_var(self, tmp_path: Path, monkeypatch) -> None:
        font_file = tmp_path / "simhei.ttf"
        font_file.write_text("fake font")
        monkeypatch.setenv("NEWSPAPER_FONT_SIMHEI", str(font_file))
        result = resolve_fonts()
        assert "SimHei" in result
        assert result["SimHei"] == font_file

    def test_font_candidates_has_three_fonts(self) -> None:
        assert set(FONT_CANDIDATES.keys()) == {"SimHei", "SimSun", "TimesNewRoman"}
