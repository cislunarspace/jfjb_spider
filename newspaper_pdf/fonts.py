"""跨平台字体发现与注册模块。

支持在 Windows、Linux 和 macOS 上自动查找 CJK（中日韩）字体，
并注册到 ReportLab 的字体系统中，供 PDF 导出使用。

字体查找优先级：
1. 用户通过 CLI 参数或环境变量指定的路径
2. 操作系统标准字体目录
3. 开源 CJK 回退字体（如 Noto CJK、文泉驿等）

如果所有字体都未找到，会给出清晰的中文错误提示。
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# 操作系统标准字体目录
_WINDOWS_FONT_DIRS: list[Path] = []
_system_root = os.environ.get("SystemRoot", "")
if _system_root:
    _WINDOWS_FONT_DIRS.append(Path(_system_root) / "Fonts")
_local_appdata = os.environ.get("LOCALAPPDATA", "")
if _local_appdata:
    _WINDOWS_FONT_DIRS.append(Path(_local_appdata) / "Microsoft" / "Windows" / "Fonts")

_LINUX_FONT_DIRS = [
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".fonts",
    Path.home() / ".local" / "share" / "fonts",
]

_MACOS_FONT_DIRS = [
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path.home() / "Library" / "Fonts",
]

# 字体注册名 → 文件名候选列表（按优先级排列）
# SimHei（黑体）用于标题
_SIMHEI_CANDIDATES = [
    "simhei.ttf",
    "SIMHEI.TTF",
    "NotoSansCJKsc-Bold.otf",
    "NotoSansCJK-Bold.ttc",
    "WenQuanYiZenHei.ttf",
    "WenQuanYiZenHeiSharp.ttf",
    "SourceHanSansSC-Bold.otf",
]

# SimSun（宋体）用于正文
_SIMSUN_CANDIDATES = [
    "simsun.ttc",
    "SIMSUN.TTC",
    "simsun.ttf",
    "SIMSUN.TTF",
    "NotoSerifCJKsc-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "NotoSansCJK-Regular.ttc",
    "WenQuanYiMicroHei.ttf",
    "WenQuanYiMicroHeiLite.ttf",
    "SourceHanSerifSC-Regular.otf",
    "SourceHanSansSC-Regular.otf",
]

# Times New Roman 用于英文字符
_TIMES_CANDIDATES = [
    "times.ttf",
    "TIMES.TTF",
    "TimesNewRoman.ttf",
    "LiberationSerif-Regular.ttf",
    "DejaVuSerif.ttf",
    "FreeSerif.ttf",
]

# 字体注册映射：注册名 → 候选文件名列表
FONT_CANDIDATES: dict[str, list[str]] = {
    "SimHei": _SIMHEI_CANDIDATES,
    "SimSun": _SIMSUN_CANDIDATES,
    "TimesNewRoman": _TIMES_CANDIDATES,
}

# 环境变量名映射
_FONT_ENV_VARS: dict[str, str] = {
    "SimHei": "NEWSPAPER_FONT_SIMHEI",
    "SimSun": "NEWSPAPER_FONT_SIMSUN",
    "TimesNewRoman": "NEWSPAPER_FONT_TIMES",
}


def _get_system_font_dirs() -> list[Path]:
    """获取当前操作系统的标准字体目录列表。"""
    platform = sys.platform
    if platform == "win32":
        return _WINDOWS_FONT_DIRS
    elif platform == "darwin":
        return _MACOS_FONT_DIRS
    else:
        return _LINUX_FONT_DIRS


def _find_font_in_dirs(filename: str, search_dirs: list[Path]) -> Path | None:
    """在指定目录列表中递归查找字体文件。

    Args:
        filename: 目标字体文件名
        search_dirs: 要搜索的目录列表

    Returns:
        找到的字体文件路径，未找到返回 None
    """
    for directory in search_dirs:
        if not directory.is_dir():
            continue
        # 直接匹配
        direct_path = directory / filename
        if direct_path.is_file():
            return direct_path
        # 递归搜索子目录
        for path in directory.rglob(filename):
            if path.is_file():
                return path
    return None


def resolve_fonts(
    custom_paths: dict[str, Path] | None = None,
    font_dir: Path | None = None,
) -> dict[str, Path]:
    """解析并返回可用的字体文件路径。

    按优先级查找每个字体的文件路径：
    1. custom_paths 参数中的显式路径
    2. 环境变量指定的路径（如 NEWSPAPER_FONT_SIMHEI）
    3. font_dir 参数指定的字体目录
    4. 操作系统标准字体目录中的自动搜索
    5. 同目录下所有字体的回退扫描

    Args:
        custom_paths: 用户通过 CLI 指定的字体路径映射，如 {"SimHei": Path("/path/to/simhei.ttf")}
        font_dir: 用户指定的字体目录，包含字体文件

    Returns:
        字体注册名到文件路径的映射，如 {"SimHei": Path("/usr/share/fonts/...")}

    Raises:
        RuntimeError: 找不到任何 CJK 字体时抛出
    """
    custom_paths = custom_paths or {}
    search_dirs = _get_system_font_dirs()
    if font_dir and font_dir.is_dir():
        search_dirs = [font_dir] + search_dirs

    resolved: dict[str, Path] = {}

    for font_name, candidates in FONT_CANDIDATES.items():
        # 优先级 1：CLI 参数指定的路径
        if font_name in custom_paths:
            custom_path = custom_paths[font_name]
            if custom_path.is_file():
                resolved[font_name] = custom_path
                logger.info("字体 %s: 使用自定义路径 %s", font_name, custom_path)
                continue
            else:
                logger.warning("字体 %s: 自定义路径不存在 %s", font_name, custom_path)

        # 优先级 2：环境变量
        env_path = os.environ.get(_FONT_ENV_VARS[font_name], "")
        if env_path:
            env_font = Path(env_path)
            if env_font.is_file():
                resolved[font_name] = env_font
                logger.info("字体 %s: 使用环境变量路径 %s", font_name, env_font)
                continue
            else:
                logger.warning("字体 %s: 环境变量路径不存在 %s", font_name, env_font)

        # 优先级 3-4：在字体目录中搜索
        found = None
        for candidate in candidates:
            found = _find_font_in_dirs(candidate, search_dirs)
            if found:
                break

        if found:
            resolved[font_name] = found
            logger.info("字体 %s: 自动发现 %s", font_name, found)
        else:
            logger.warning("字体 %s: 未找到可用字体文件", font_name)

    # 检查是否至少有一个 CJK 字体（SimHei 或 SimSun）
    has_cjk = "SimHei" in resolved or "SimSun" in resolved
    if not has_cjk:
        raise RuntimeError(
            "未找到任何中文字体。请执行以下任一操作：\n"
            "  1. 安装中文字体（如 Noto CJK、文泉驿等）\n"
            "  2. 通过命令行参数指定字体路径：--font-simhei /path/to/font.ttf\n"
            "  3. 设置环境变量：export NEWSPAPER_FONT_SIMHEI=/path/to/font.ttf\n"
            "  4. 将字体文件放入指定目录：--font-dir /path/to/fonts/"
        )

    return resolved


def register_fonts(
    custom_paths: dict[str, Path] | None = None,
    font_dir: Path | None = None,
) -> set[str]:
    """解析字体文件并注册到 ReportLab 字体系统。

    Args:
        custom_paths: 用户指定的字体路径映射
        font_dir: 用户指定的字体目录

    Returns:
        成功注册的字体名称集合
    """
    resolved = resolve_fonts(custom_paths, font_dir)

    registered: set[str] = set()
    for font_name, font_path in resolved.items():
        try:
            font = TTFont(font_name, str(font_path))
            # TTC（TrueType Collection）文件加载后，ReportLab 可能给嵌入名添加 "-0" 后缀。
            # 清除 subfontNameX 可以确保字体注册名与引用名一致。
            if font_path.suffix.lower() == ".ttc":
                font.face.subfontNameX = b""
            pdfmetrics.registerFont(font)
            registered.add(font_name)
            logger.debug("已注册字体 %s <- %s", font_name, font_path)
        except Exception as exc:
            logger.error("注册字体失败 %s (%s): %s", font_name, font_path, exc)

    if "TimesNewRoman" not in registered:
        logger.warning(
            "Times New Roman 字体未找到，英文文本将使用中文字体渲染。"
            "可通过 --font-times 参数指定字体路径。"
        )

    return registered
