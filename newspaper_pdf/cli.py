"""共享命令行参数解析工具。

提供两个爬虫共用的 argparse 参数工厂函数和日志配置，
确保 CLI 接口风格统一。
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path


def setup_logging() -> None:
    """配置统一的日志输出格式。

    在 main() 入口处调用一次，所有模块的 logger 输出将使用相同格式。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """为解析器添加两个爬虫共用的命令行参数。

    包括：日期、输出目录、导出模式、字体配置等。

    Args:
        parser: argparse.ArgumentParser 实例
    """
    parser.add_argument(
        "--date",
        help="指定报纸日期，格式为 YYYY-MM-DD；不传时自动抓取当天最新版。",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="输出目录，默认 output",
    )
    parser.add_argument(
        "--combined-only",
        action="store_true",
        help="仅输出汇总 PDF。",
    )
    parser.add_argument(
        "--individual-only",
        action="store_true",
        help="仅输出单篇 PDF。",
    )
    parser.add_argument(
        "--font-simhei",
        type=Path,
        default=None,
        help="SimHei（黑体）字体文件路径，默认自动发现。",
    )
    parser.add_argument(
        "--font-simsun",
        type=Path,
        default=None,
        help="SimSun（宋体）字体文件路径，默认自动发现。",
    )
    parser.add_argument(
        "--font-times",
        type=Path,
        default=None,
        help="Times New Roman 字体文件路径，默认自动发现。",
    )
    parser.add_argument(
        "--font-dir",
        type=Path,
        default=None,
        help="字体文件所在目录，优先从中查找字体。",
    )
    parser.add_argument(
        "--json-progress",
        action="store_true",
        help="以 JSON 行格式输出进度（供 Web 服务调用）。",
    )


def build_font_paths(args: argparse.Namespace) -> dict[str, Path]:
    """从命令行参数中提取用户指定的字体路径。

    Args:
        args: 解析后的命令行参数

    Returns:
        字体注册名到路径的映射（仅包含用户指定的字体）
    """
    paths: dict[str, Path] = {}
    if args.font_simhei:
        paths["SimHei"] = args.font_simhei
    if args.font_simsun:
        paths["SimSun"] = args.font_simsun
    if args.font_times:
        paths["TimesNewRoman"] = args.font_times
    return paths


def _json_emit(obj: dict) -> None:
    """输出 JSON 行到 stdout 并立即刷新。"""
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def emit_progress(*, current: int, total: int, message: str) -> None:
    """输出进度事件。"""
    _json_emit({"type": "progress", "current": current, "total": total, "message": message})


def emit_log(*, level: str, message: str) -> None:
    """输出日志事件。"""
    _json_emit({"type": "log", "level": level, "message": message})


def emit_finished(*, success: int, fail: int, skip: int, total: int) -> None:
    """输出完成事件。"""
    _json_emit({"type": "finished", "success": success, "fail": fail, "skip": skip, "total": total})


def emit_error(*, message: str) -> None:
    """输出错误事件。"""
    _json_emit({"type": "error", "message": message})


def log_message(
    logger: logging.Logger,
    message: str,
    *,
    level: str = "INFO",
    json_mode: bool = False,
) -> None:
    """统一输出日志：json_mode 时输出 JSON 行，否则写入 logging。"""
    if json_mode:
        emit_log(level=level, message=message)
    else:
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn("%s", message)
