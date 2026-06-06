from __future__ import annotations

import time
from typing import Any

from hermes_max_adapter.client import build_answer_callback_request, build_send_request, classify_send_response
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import DedupeDecision, InMemoryDedupeStore
from hermes_max_adapter.models.max_messages import OutboundMessage, OutboundTextPart
from hermes_max_adapter.observability import InMemoryMetrics
from hermes_max_adapter.renderer import render_canonical_outbound_message
from hermes_max_adapter.transport import HttpMaxSender
from hermes_max_adapter.updates import normalize_update


class MaxAdapter:
    def __init__(self, config: MaxAdapterConfig, sender: object | None = None) -> None:
        self.config = config
        self.connected = False
        self.dedupe_store = InMemoryDedupeStore()
        self.metrics = InMemoryMetrics()
        self.sender = sender or HttpMaxSender(config=config)
        self.base_url = "https://platform-api.max.ru"
        self.max_retries = config.max_retries
        self.retry_backoff_seconds = config.retry_backoff_seconds
        self.user_dialog_index: dict[str, str] = {}

    def connect_sync(self) -> bool:
        self.connected = True
        return True

    async def connect(self) -> bool:
        return self.connect_sync()

    def disconnect_sync(self) -> None:
        self.connected = False

    async def disconnect(self) -> None:
        self.disconnect_sync()

    def build_dedupe_key(self, payload: dict) -> str:
        live_message = payload.get("messageCreated", {}).get("message", {})
        message = payload.get("message", {})
        message_body = message.get("body", {})
        live_body = live_message.get("body", {})
        marker = (
            payload.get("mid")
            or message.get("mid")
            or message_body.get("mid")
            or live_message.get("mid")
            or live_body.get("mid")
            or payload.get("callback_id")
            or "unknown"
        )
        update_type = payload.get("update_type")
        if not update_type and payload.get("eventType") == "messageCreated":
            update_type = "message_created"
        return f"{update_type or 'unknown'}:{marker}"

    def process_update(self, payload: dict) -> dict:
        self.metrics.increment("inbound_updates_total")
        dedupe_key = self.build_dedupe_key(payload)
        decision = self.dedupe_store.check_and_mark(dedupe_key)
        if decision == DedupeDecision.DUPLICATE:
            self.metrics.increment("duplicate_updates_total")
            return {"dedupe": decision, "event": None}

        event = normalize_update(payload)
        if event.user_id and event.chat_id:
            self.user_dialog_index[str(event.user_id)] = str(event.chat_id)
        return {"dedupe": decision, "event": event}

    def _send_payload_once(self, payload: dict, *, chat_id: str | None = None, user_id: str | None = None) -> dict:
        request = build_send_request(
            base_url=self.base_url,
            token=self.config.bot_token,
            chat_id=chat_id,
            user_id=user_id,
            payload=payload,
        )
        raw_response = self.sender.send(request)
        return classify_send_response(raw_response) | {"request": request}

    def _send_payload_with_retry(self, payload: dict, *, chat_id: str | None = None, user_id: str | None = None) -> dict:
        attempts = 0
        last_outcome: dict | None = None
        while attempts <= self.max_retries:
            attempts += 1
            outcome = self._send_payload_once(chat_id=chat_id, user_id=user_id, payload=payload)
            last_outcome = outcome
            if outcome["success"] or not outcome["retryable"]:
                return outcome | {"attempts": attempts}
            if self.retry_backoff_seconds > 0:
                time.sleep(self.retry_backoff_seconds)
        return (last_outcome or {"success": False, "retryable": False, "status_code": 500, "error": "unknown"}) | {"attempts": attempts}

    def _resolve_delivery_target(self, message: OutboundMessage) -> tuple[str | None, str | None]:
        target_user_id = str(message.target_user_id).strip() if message.target_user_id is not None else None
        target_chat_id = str(message.target_chat_id).strip() if message.target_chat_id is not None else None
        if target_user_id:
            resolved_chat_id = self.user_dialog_index.get(target_user_id)
            return resolved_chat_id, target_user_id
        return target_chat_id, None

    def send_message_sync(self, message: OutboundMessage) -> dict:
        target_chat_id, target_user_id = self._resolve_delivery_target(message)
        payloads = render_canonical_outbound_message(message)
        message_ids: list[str] = []
        failures: list[dict] = []

        for payload in payloads:
            outcome = self._send_payload_with_retry(chat_id=target_chat_id, user_id=target_user_id, payload=payload)
            if outcome["success"]:
                self.metrics.increment("outbound_messages_total")
                if outcome["message_id"] is not None:
                    message_ids.append(str(outcome["message_id"]))
                continue

            self.metrics.increment("outbound_failures_total")
            failures.append(outcome)

        return {
            "success": len(failures) == 0,
            "message_ids": message_ids,
            "failures": failures,
        }

    def send_text_sync(self, chat_id: str, text: str) -> dict:
        return self.send_message_sync(
            OutboundMessage(target_chat_id=chat_id, parts=[OutboundTextPart(text=text)])
        )

    def send_text_to_user_sync(self, user_id: str, text: str) -> dict:
        return self.send_message_sync(
            OutboundMessage(target_user_id=user_id, parts=[OutboundTextPart(text=text)])
        )

    def answer_callback_sync(
        self,
        callback_id: str,
        text: str | None = None,
        notification: str | None = None,
        show_alert: bool | None = None,
    ) -> dict:
        request = build_answer_callback_request(
            base_url=self.base_url,
            token=self.config.bot_token,
            callback_id=callback_id,
            text=text,
            notification=notification,
            show_alert=show_alert,
        )
        raw_response = self.sender.send(request)
        return classify_send_response(raw_response) | {"request": request}

    async def send(self, chat_id: str, content: str, reply_to: str | None = None, metadata: dict | None = None) -> dict:
        _ = reply_to, metadata
        return self.send_text_sync(chat_id=chat_id, text=content)

    async def get_chat_info(self, chat_id: str) -> dict[str, str]:
        return {"name": chat_id, "type": "dm"}

    def health_status(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "config": {
                "webhook_enabled": bool(self.config.webhook_url),
                "long_polling_enabled": self.config.enable_long_polling,
                "max_retries": self.config.max_retries,
                "request_timeout_seconds": self.config.request_timeout_seconds,
            },
            "metrics": dict(self.metrics.counters),
        }

    def status(self) -> dict[str, Any]:
        return self.health_status()

    async def get_status(self) -> dict[str, Any]:
        return self.status()

