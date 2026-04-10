"""网络请求工具模块。

提供 HTTP 会话创建和带重试机制的 GET 请求，供两个爬虫共用。
"""

from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)

# 默认请求超时时间（秒）
REQUEST_TIMEOUT = 30

# 模拟 Chrome 浏览器的 User-Agent，用于绕过网站的基本反爬检测
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


def create_session(user_agent: str | None = None) -> requests.Session:
    """创建带默认请求头的 HTTP 会话。

    Args:
        user_agent: 自定义 User-Agent，不传则使用默认值

    Returns:
        配置好的 requests.Session 对象
    """
    session = requests.Session()
    session.headers.update(
        {"User-Agent": user_agent or DEFAULT_USER_AGENT}
    )
    return session


def retry_get(
    session: requests.Session,
    url: str,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs,
) -> requests.Response:
    """带指数退避的重试 GET 请求。

    当遇到网络连接错误或请求超时时，自动重试。
    每次重试的等待时间按指数增长：backoff_factor * 2^attempt 秒。

    Args:
        session: HTTP 会话对象
        url: 请求 URL
        max_retries: 最大重试次数，默认 3 次
        backoff_factor: 退避因子（秒），默认 1.0
        **kwargs: 传递给 session.get() 的额外参数（如 timeout）

    Returns:
        成功的响应对象

    Raises:
        requests.exceptions.RequestException: 所有重试均失败后抛出最后一次的异常
    """
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)

    last_exception: requests.exceptions.RequestException | None = None
    for attempt in range(max_retries):
        try:
            response = session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as exc:
            # 仅对服务器错误（5xx）重试，客户端错误（4xx）直接抛出
            if exc.response.status_code < 500:
                raise
            last_exception = exc
            if attempt < max_retries - 1:
                wait = backoff_factor * (2 ** attempt)
                logger.warning(
                    "HTTP %d 错误（第 %d/%d 次），%.1f 秒后重试: %s",
                    exc.response.status_code, attempt + 1, max_retries, wait, url,
                )
                time.sleep(wait)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_exception = exc
            if attempt < max_retries - 1:
                wait = backoff_factor * (2 ** attempt)
                logger.warning(
                    "请求失败（第 %d/%d 次），%.1f 秒后重试: %s",
                    attempt + 1, max_retries, wait, url,
                )
                time.sleep(wait)

    raise last_exception  # type: ignore[misc]
