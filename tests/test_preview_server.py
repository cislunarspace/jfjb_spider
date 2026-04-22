"""PreviewServer 单元测试。"""

from __future__ import annotations


import requests

from newspaper_pdf.gui.preview_server import PreviewServer, find_free_port


class TestPreviewServer:
    """验证本地 HTTP 预览服务器核心功能。"""

    def test_start_and_stop(self, tmp_path):
        """服务器应能正常启动和停止，并绑定到可用端口。"""
        server = PreviewServer(tmp_path)
        assert server.port == 0

        server.start()
        assert server.port > 0
        assert server.url == f"http://127.0.0.1:{server.port}"

        server.stop()
        assert server._server is None

    def test_serves_static_file(self, tmp_path):
        """服务器应能正确提供根目录下的静态文件。"""
        (tmp_path / "test.pdf").write_bytes(b"%PDF-1.4 fake content")

        server = PreviewServer(tmp_path)
        server.start()

        try:
            resp = requests.get(f"{server.url}/test.pdf", timeout=5)
            assert resp.status_code == 200
            assert resp.content == b"%PDF-1.4 fake content"
        finally:
            server.stop()

    def test_get_url_with_subpath(self, tmp_path):
        """get_url 应正确构造带子路径的 URL。"""
        sub = tmp_path / "2026-03-10"
        sub.mkdir()
        server = PreviewServer(tmp_path)
        server.start()

        try:
            url = server.get_url("2026-03-10/report.pdf")
            assert url.startswith(server.url)
            assert "2026-03-10/report.pdf" in url
        finally:
            server.stop()

    def test_get_url_encodes_unicode(self, tmp_path):
        """get_url 应对中文字符进行百分号编码。"""
        server = PreviewServer(tmp_path)
        server.start()

        try:
            url = server.get_url("解放军报/全集.pdf")
            assert "%E8%A7%A3" in url  # 解 的 UTF-8 编码
        finally:
            server.stop()

    def test_idempotent_start(self, tmp_path):
        """多次调用 start 不应抛出异常或重复绑定。"""
        server = PreviewServer(tmp_path)
        server.start()
        original_port = server.port

        try:
            server.start()
            assert server.port == original_port
        finally:
            server.stop()

    def test_idempotent_stop(self, tmp_path):
        """多次调用 stop 不应抛出异常。"""
        server = PreviewServer(tmp_path)
        server.stop()
        server.stop()
        assert server._server is None


class TestFindFreePort:
    """验证端口查找工具。"""

    def test_returns_valid_port(self):
        """应返回一个可用端口。"""
        port = find_free_port()
        assert isinstance(port, int)
        assert 1024 < port < 65535

    def test_port_is_free(self):
        """返回的端口应确实可用。"""
        port = find_free_port()
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            assert s.connect_ex(("127.0.0.1", port)) != 0
