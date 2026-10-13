# -*- coding: utf-8 -*-
"""ntfy notification sender."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse, urlunparse

import requests

from src.config import Config
from src.formatters import chunk_content_by_max_bytes, strip_hidden_markdown_metadata


logger = logging.getLogger(__name__)

# ntfy JSON publish API 对请求体有大小上限（免费版约 4KB），超过会返回 413。
# 预留 JSON 包装与分页标记的余量，超出部分自动分批发送。
_NTFY_MAX_BYTES_DEFAULT = 3500


def resolve_ntfy_endpoint(ntfy_url: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split NTFY_URL into server root and topic from the final path segment."""
    raw_url = (ntfy_url or "").strip().rstrip("/")
    if not raw_url:
        return None, None

    parsed = urlparse(raw_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None, None

    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if not path_segments:
        return None, None

    topic = unquote(path_segments[-1]).strip()
    if not topic:
        return None, None

    root_path = "/".join(path_segments[:-1])
    server_url = urlunparse(
        parsed._replace(
            path=f"/{root_path}" if root_path else "",
            params="",
            query="",
            fragment="",
        )
    ).rstrip("/")

    return server_url, topic


class NtfySender:
    """Send Markdown text notifications through the ntfy JSON publish API."""

    def __init__(self, config: Config):
        self._ntfy_url = getattr(config, "ntfy_url", None)
        self._ntfy_token = getattr(config, "ntfy_token", None)
        self._webhook_verify_ssl = getattr(config, "webhook_verify_ssl", True)

    def _is_ntfy_configured(self) -> bool:
        return bool(self._ntfy_url)

    def _resolve_ntfy_endpoint(self) -> Tuple[Optional[str], Optional[str]]:
        return resolve_ntfy_endpoint(self._ntfy_url)

    def send_to_ntfy(
        self,
        content: str,
        title: Optional[str] = None,
        *,
        timeout_seconds: Optional[float] = None,
    ) -> bool:
        """Publish a notification to ntfy using a JSON body with UTF-8 text."""
        if not self._is_ntfy_configured():
            logger.warning("ntfy URL 未配置，跳过推送")
            return False

        server_url, topic = self._resolve_ntfy_endpoint()
        if not server_url or not topic:
            logger.error("NTFY_URL 必须是包含 topic path 的完整 endpoint，例如 https://ntfy.sh/my-topic")
            return False

        if title is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"📈 股票分析报告 - {date_str}"
        sanitized_content = strip_hidden_markdown_metadata(content).strip()
        if not sanitized_content:
            logger.warning("ntfy 消息内容为空，跳过推送")
            return False

        content_bytes = len(sanitized_content.encode("utf-8"))
        if content_bytes > _NTFY_MAX_BYTES_DEFAULT:
            logger.info("ntfy 消息内容超长(%d字节)，将分批发送", content_bytes)
            return self._send_ntfy_chunked(
                sanitized_content, title, server_url, topic, timeout_seconds
            )

        return self._publish_ntfy(server_url, topic, title, sanitized_content, timeout_seconds)

    def _publish_ntfy(
        self,
        server_url: str,
        topic: str,
        title: str,
        message: str,
        timeout_seconds: Optional[float] = None,
    ) -> bool:
        """Publish a single ntfy JSON message."""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "daily_stock_analysis",
        }
        token = (self._ntfy_token or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "topic": topic,
            "title": title,
            "message": message,
            "markdown": True,
        }

        try:
            response = requests.post(
                server_url,
                json=payload,
                headers=headers,
                timeout=timeout_seconds or 10,
                verify=self._webhook_verify_ssl,
            )
            if 200 <= response.status_code < 300:
                logger.info("ntfy 消息发送成功")
                return True

            logger.error("ntfy 请求失败: HTTP %s", response.status_code)
            logger.debug("ntfy 响应内容: %s", response.text)
            return False
        except requests.exceptions.Timeout:
            logger.error("发送 ntfy 消息失败: 请求超时")
            return False
        except requests.exceptions.RequestException as exc:
            logger.error("发送 ntfy 消息失败: 网络请求异常")
            logger.debug("ntfy 请求异常类型: %s", type(exc).__name__)
            return False
        except Exception as exc:
            logger.error("发送 ntfy 消息失败: 未知异常")
            logger.debug("ntfy 未知异常类型: %s", type(exc).__name__)
            return False

    def _send_ntfy_chunked(
        self,
        content: str,
        title: str,
        server_url: str,
        topic: str,
        timeout_seconds: Optional[float] = None,
    ) -> bool:
        """Split an oversized report and publish each part as its own ntfy message."""
        chunks = chunk_content_by_max_bytes(content, _NTFY_MAX_BYTES_DEFAULT, add_page_marker=True)
        total_chunks = len(chunks)
        success_count = 0
        for i, chunk in enumerate(chunks):
            part_title = title if total_chunks == 1 else f"{title} ({i + 1}/{total_chunks})"
            if self._publish_ntfy(server_url, topic, part_title, chunk, timeout_seconds):
                success_count += 1
            else:
                logger.error("ntfy 第 %d/%d 批发送失败", i + 1, total_chunks)
            if i < total_chunks - 1:
                time.sleep(1)
        return success_count == total_chunks
