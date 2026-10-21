# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import json
import logging
import datetime
import threading
import time
from typing import Optional, Tuple, Dict, Any
import httpx
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MonitorClient:
    """
    Background Telemetry Client to report status and incidents to the external Monitor
    via MQTT Broker or HTTP/HTTPS REST Endpoints (e.g. ngrok, Webhooks, APIs).
    Supports strict JSON payload structures with ISO8601 formatting.
    """
    def __init__(self, host: str = "localhost", port: int = 1883, enabled: bool = False, topic: str = "noxfort/telemetry/"):
        self.host = host.strip() if host else "localhost"
        self.port = port
        self.enabled = enabled
        self.topic = topic
        self.is_http: bool = self._check_is_http(self.host)
        self.http_url: str = self._normalize_http_url(self.host) if self.is_http else ""
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._client: Optional[mqtt.Client] = None
        
        if self.enabled:
            self.start()

    @staticmethod
    def _check_is_http(target: str) -> bool:
        if not target:
            return False
        clean = target.strip().lower()
        if clean.startswith("http://") or clean.startswith("https://"):
            return True
        if "/" in clean:
            return True
        if ".ngrok" in clean or ".dev" in clean or "api." in clean or "/api" in clean:
            return True
        return False

    @staticmethod
    def _normalize_http_url(target: str) -> str:
        clean = target.strip()
        if not (clean.startswith("http://") or clean.startswith("https://")):
            clean = f"https://{clean}"
        return clean

    def _create_payload_dict(self, origin: str, category: str, level: str, message: str) -> Dict[str, Any]:
        """Creates dictionary representation of strict telemetry payload."""
        now_local = datetime.datetime.now().astimezone()
        return {
            "category": category,
            "origin": origin,
            "level": level,
            "message": message,
            "occurred_at": now_local.isoformat(),
        }

    def _create_payload(self, origin: str, category: str, level: str, message: str) -> str:
        """Formats the strict JSON payload string required by the monitoring server."""
        return json.dumps(self._create_payload_dict(origin, category, level, message))

    def _send_http(self, payload: Dict[str, Any]) -> bool:
        """Dispatches telemetry JSON payload via HTTP POST."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Synapse-Telemetry-Client/2.0",
            "ngrok-skip-browser-warning": "true",
        }
        try:
            with httpx.Client(timeout=6.0) as client:
                res = client.post(self.http_url, json=payload, headers=headers)
                if res.is_success:
                    logger.debug(f"[Monitor] HTTP Telemetry dispatched successfully ({res.status_code}) to {self.http_url}")
                    return True
                else:
                    logger.warning(f"[Monitor] HTTP Telemetry server returned status {res.status_code} for {self.http_url}")
                    return False
        except Exception as e:
            logger.warning(f"[Monitor] Failed dispatching HTTP telemetry to {self.http_url}: {e}")
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"[Monitor] Successfully connected to Broker!")
        else:
            logger.error(f"[Monitor] Failed to connect. Code: {reason_code}")

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        pass

    def _connect_mqtt(self):
        if self._client:
            return
            
        try:
            import uuid
            main_client_id = f"synapse_{uuid.uuid4().hex[:8]}"
            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=main_client_id)
            self._client.on_connect = self._on_connect
            self._client.on_publish = self._on_publish
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            logger.info(f"[Monitor] Connected to MQTT broker at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"[Monitor] Failed to connect to MQTT broker: {e}")
            self._client = None

    def start(self):
        if not self.enabled or self._running:
            return
            
        self._running = True
        if self.is_http:
            logger.info(f"🌐 [Monitor] Telemetry client started in HTTP REST mode: {self.http_url}")
        else:
            logger.info(f"📡 [Monitor] Telemetry client started in MQTT mode: {self.host}:{self.port}")
            self._connect_mqtt()

        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            
        if self._thread is not None and self._thread.is_alive(): # type: ignore
            self._thread.join(timeout=2.0)
        logger.info("[Monitor] Telemetry client stopped.")

    def _heartbeat_loop(self):
        """Sends a Carina Heartbeat every 30 seconds using the 5-field schema."""
        while self._running:
            payload_dict = self._create_payload_dict("synapse", "SOFTWARE", "INFO", "heartbeat")
            if self.is_http:
                self._send_http(payload_dict)
            elif self._client:
                try:
                    payload_str = json.dumps(payload_dict)
                    self._client.publish(self.topic, payload_str, qos=0)
                except Exception as e:
                    logger.warning(f"[Monitor] Failed to publish MQTT heartbeat: {e}")
                    
            # Sleep in chunks to allow responsive shutdown
            for _ in range(30):
                if not self._running:
                    break
                time.sleep(1)

    def report_incident(self, category: str, level: str, message: str):
        """
        Immediately dispatches an incident report.
        level must be 'INFO', 'WARNING', or 'CRITICAL'.
        category must be 'SOFTWARE' or 'HARDWARE'.
        """
        if not self.enabled:
            return
            
        payload_dict = self._create_payload_dict("synapse", category, level.upper(), message)
        if self.is_http:
            self._send_http(payload_dict)
        else:
            if not self._client:
                self._connect_mqtt()
                
            if self._client:
                try:
                    payload_str = json.dumps(payload_dict)
                    self._client.publish(self.topic, payload_str, qos=1)
                    logger.debug(f"[Monitor] Incident reported via MQTT: {level} - {message}")
                except Exception as e:
                    logger.error(f"[Monitor] Failed to publish incident via MQTT: {e}")

    @classmethod
    def test_connection_detailed(cls, host: str, port: int = 1883, topic: str = "noxfort/telemetry/") -> Tuple[bool, str]:
        """
        Tests connection and dispatches an instant test heartbeat.
        Returns a tuple of (success, human_readable_message).
        """
        clean_target = host.strip() if host else "localhost"
        if cls._check_is_http(clean_target):
            url = cls._normalize_http_url(clean_target)
            now_local = datetime.datetime.now().astimezone()
            payload = {
                "category": "SOFTWARE",
                "origin": "synapse",
                "level": "INFO",
                "message": "heartbeat_test",
                "occurred_at": now_local.isoformat(),
            }
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Synapse-Telemetry-Client/2.0",
                "ngrok-skip-browser-warning": "true",
            }
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.is_success:
                        return True, f"Conexão HTTP OK! Servidor respondeu status {resp.status_code}."
                    else:
                        return False, f"Servidor HTTP respondeu com erro {resp.status_code}: {resp.text[:120]}"
            except httpx.ConnectError:
                return False, f"Não foi possível conectar ao endpoint HTTP: {url}. Verifique se o servidor está ativo."
            except httpx.TimeoutException:
                return False, f"Tempo limite esgotado ao tentar conectar a {url}."
            except Exception as e:
                return False, f"Falha na conexão HTTP: {str(e)}"
        else:
            try:
                import uuid
                test_client_id = f"synapse_test_{uuid.uuid4().hex[:8]}"
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=test_client_id)
                client.connect(clean_target, port, keepalive=5)
                client.loop_start()
                
                temp = cls(enabled=False)
                payload_str = temp._create_payload("synapse", "SOFTWARE", "INFO", "heartbeat_test")
                msg_info = client.publish(topic, payload_str, qos=1)
                msg_info.wait_for_publish(timeout=2.0)
                
                client.loop_stop()
                client.disconnect()
                return True, f"Conexão MQTT OK! Broker alcançado em {clean_target}:{port}."
            except Exception as e:
                logger.error(f"[Monitor] Instant MQTT heartbeat failed: {e}")
                return False, f"Falha ao conectar ao Broker MQTT em {clean_target}:{port} - {str(e)}"

    @classmethod
    def test_connection_and_send_heartbeat(cls, host: str, port: int = 1883, topic: str = "noxfort/telemetry/") -> bool:
        """
        Static/Class method to instantly test a connection and dispatch the Carina Heartbeat.
        Used by callers expecting boolean response.
        """
        ok, _ = cls.test_connection_detailed(host, port, topic)
        return ok
