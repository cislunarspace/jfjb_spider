"""PDF 预览 HTTP 服务器。

提供基于网页架构的本地静态文件服务，将 output 目录映射为 HTTP 根目录，
使系统浏览器可以直接通过 URL 预览 PDF，绕过 PyQt WebEngine 的 PDF 插件限制。
"""

from __future__ import annotations

import logging
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

logger = logging.getLogger(__name__)


class PreviewServer:
    """本地 PDF 预览 HTTP 服务器。

    基于 Python 标准库的 ThreadingHTTPServer，在随机可用端口启动，
    将指定的根目录作为静态文件服务暴露给本地浏览器。

    Attributes:
        root: 静态文件服务根目录
        port: 服务器绑定的端口号
        url: 服务根地址，如 http://127.0.0.1:8765
    """

    def __init__(self, root: Path, port: int = 0) -> None:
        """初始化预览服务器。

        Args:
            root: 静态文件服务根目录
            port: 指定端口号，0 表示自动选择可用端口
        """
        self.root = Path(root).resolve()
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        """返回实际绑定的端口号，未启动时为 0。"""
        if self._server is not None:
            return self._server.server_address[1]
        return 0

    @property
    def url(self) -> str:
        """返回服务根 URL。"""
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        """启动 HTTP 服务器（非阻塞，在后台线程运行）。"""
        if self._server is not None:
            return

        addr = ("127.0.0.1", self._port)
        handler = self._make_handler()
        self._server = ThreadingHTTPServer(addr, handler)

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("PreviewServer started at %s", self.url)

    def stop(self) -> None:
        """停止 HTTP 服务器。"""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        logger.info("PreviewServer stopped")

    def get_url(self, relative_path: str | Path) -> str:
        """根据相对路径构造完整的 HTTP URL。

        Args:
            relative_path: 相对于服务根目录的路径

        Returns:
            可在外部浏览器中直接访问的 URL
        """
        rel = str(relative_path).replace("\\", "/")
        # 对路径中的中文字符进行百分号编码
        encoded = quote(rel, safe="/")
        return f"{self.url}/{encoded}"

    def _make_handler(self) -> type[SimpleHTTPRequestHandler]:
        """构造绑定到指定根目录的请求处理器类。"""
        root = self.root

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                super().__init__(*args, directory=str(root), **kwargs)

            def log_message(self, format: str, *args) -> None:  # noqa: A002
                # 降级访问日志为 debug 级别，避免刷屏
                logger.debug(format, *args)

        return Handler


def find_free_port(start: int = 18080, end: int = 19080) -> int:
    """在指定范围内查找一个可用端口。

    Args:
        start: 起始端口
        end: 结束端口

    Returns:
        可用端口号

    Raises:
        RuntimeError: 范围内无可用端口
    """
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port available in range {start}-{end}")
