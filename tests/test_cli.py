"""命令行参数解析测试。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from newspaper_pdf.cli import add_common_arguments, build_font_paths


@pytest.mark.unit
class TestBuildFontPaths:
    def test_all_specified(self) -> None:
        args = argparse.Namespace(
            font_simhei=Path("/fonts/simhei.ttf"),
            font_simsun=Path("/fonts/simsun.ttf"),
            font_times=Path("/fonts/times.ttf"),
        )
        result = build_font_paths(args)
        assert result == {
            "SimHei": Path("/fonts/simhei.ttf"),
            "SimSun": Path("/fonts/simsun.ttf"),
            "TimesNewRoman": Path("/fonts/times.ttf"),
        }

    def test_none_specified(self) -> None:
        args = argparse.Namespace(
            font_simhei=None,
            font_simsun=None,
            font_times=None,
        )
        result = build_font_paths(args)
        assert result == {}

    def test_partial(self) -> None:
        args = argparse.Namespace(
            font_simhei=Path("/fonts/simhei.ttf"),
            font_simsun=None,
            font_times=None,
        )
        result = build_font_paths(args)
        assert result == {"SimHei": Path("/fonts/simhei.ttf")}

    def test_returns_correct_keys(self) -> None:
        args = argparse.Namespace(
            font_simhei=Path("a"),
            font_simsun=Path("b"),
            font_times=Path("c"),
        )
        result = build_font_paths(args)
        assert set(result.keys()) == {"SimHei", "SimSun", "TimesNewRoman"}


@pytest.mark.unit
class TestAddCommonArguments:
    def _parse(self, argv: list[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        add_common_arguments(parser)
        return parser.parse_args(argv)

    def test_default_out_dir(self) -> None:
        args = self._parse([])
        assert args.out_dir == "output"

    def test_date_parsing(self) -> None:
        args = self._parse(["--date", "2026-03-10"])
        assert args.date == "2026-03-10"

    def test_combined_only(self) -> None:
        args = self._parse(["--combined-only"])
        assert args.combined_only is True

    def test_individual_only(self) -> None:
        args = self._parse(["--individual-only"])
        assert args.individual_only is True

    def test_font_dir(self) -> None:
        args = self._parse(["--font-dir", "/custom/fonts"])
        assert args.font_dir == Path("/custom/fonts")

    def test_font_simhei(self) -> None:
        args = self._parse(["--font-simhei", "/fonts/simhei.ttf"])
        assert args.font_simhei == Path("/fonts/simhei.ttf")

    def test_out_dir_custom(self) -> None:
        args = self._parse(["--out-dir", "custom_output"])
        assert args.out_dir == "custom_output"
