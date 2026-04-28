from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

from app.utils.clocks import utc_now_iso


class ProvenanceStoreService:
    """SQLite-backed provenance record store for process/verify workflows."""

    def __init__(self, db_path: str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provenance_records (
                    asset_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    signature_b64 TEXT NOT NULL,
                    pdq_hash_hex TEXT NOT NULL,
                    semantic_hash_hex TEXT NOT NULL,
                    commitment TEXT,
                    mini_mac TEXT,
                    clip_embedding_json TEXT,
                    protected_image_png BLOB,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            # Lightweight migration in case the DB was created before the image column existed.
            columns = {
                row["name"]
                for row in self._conn.execute("PRAGMA table_info(provenance_records)").fetchall()
            }
            if "protected_image_png" not in columns:
                self._conn.execute("ALTER TABLE provenance_records ADD COLUMN protected_image_png BLOB")
            if "commitment" not in columns:
                self._conn.execute("ALTER TABLE provenance_records ADD COLUMN commitment TEXT")
            if "mini_mac" not in columns:
                self._conn.execute("ALTER TABLE provenance_records ADD COLUMN mini_mac TEXT")
            self._conn.commit()

    def upsert_record(
        self,
        *,
        asset_id: str,
        payload: dict[str, Any],
        signature_b64: str,
        pdq_hash_hex: str,
        semantic_hash_hex: str,
        commitment: str,
        mini_mac: str,
        clip_embedding: list[float] | None,
        protected_image_png: bytes | None,
    ) -> None:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO provenance_records (
                    asset_id, payload_json, signature_b64, pdq_hash_hex,
                    semantic_hash_hex, commitment, mini_mac, clip_embedding_json,
                    protected_image_png, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    signature_b64=excluded.signature_b64,
                    pdq_hash_hex=excluded.pdq_hash_hex,
                    semantic_hash_hex=excluded.semantic_hash_hex,
                    commitment=excluded.commitment,
                    mini_mac=excluded.mini_mac,
                    clip_embedding_json=excluded.clip_embedding_json,
                    protected_image_png=excluded.protected_image_png,
                    updated_at=excluded.updated_at
                """,
                (
                    asset_id,
                    json.dumps(payload, separators=(",", ":")),
                    signature_b64,
                    pdq_hash_hex,
                    semantic_hash_hex,
                    commitment,
                    mini_mac,
                    json.dumps(clip_embedding) if clip_embedding is not None else None,
                    protected_image_png,
                    now,
                    now,
                ),
            )
            self._conn.commit()

    def get_record(self, asset_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT asset_id, payload_json, signature_b64, pdq_hash_hex,
                       semantic_hash_hex, commitment, mini_mac, clip_embedding_json,
                       created_at, updated_at
                FROM provenance_records
                WHERE asset_id = ?
                """,
                (asset_id,),
            ).fetchone()

        if row is None:
            return None

        clip_embedding_json = row["clip_embedding_json"]
        return {
            "asset_id": row["asset_id"],
            "payload": json.loads(row["payload_json"]),
            "signature_b64": row["signature_b64"],
            "pdq_hash_hex": row["pdq_hash_hex"],
            "semantic_hash_hex": row["semantic_hash_hex"],
            "commitment": row["commitment"],
            "mini_mac": row["mini_mac"],
            "clip_embedding": json.loads(clip_embedding_json) if clip_embedding_json else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_protected_image(self, asset_id: str) -> bytes | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT protected_image_png FROM provenance_records WHERE asset_id = ?",
                (asset_id,),
            ).fetchone()
        if row is None:
            return None
        return row["protected_image_png"]

    def ping(self) -> bool:
        try:
            with self._lock:
                self._conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False
