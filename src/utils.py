"""
utils.py - 辅助函数：UUID, 时间, 文件 I/O, CSV helpers
"""
import uuid
from datetime import datetime, timezone
import os
import csv
from typing import List


def generate_uuid() -> str:
    return str(uuid.uuid4())


def current_datetime_iso() -> str:
    # returns ISO without timezone for simplicity
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def file_exists(path: str) -> bool:
    return os.path.exists(path)


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def escape_csv_field(s: str) -> str:
    # csv module handles quoting for us normally
    return s


def write_transactions_csv(path: str, rows: List[dict]):
    # rows: list of dict contains id,type,amount,category,account,datetime,remark,receipt
    ensure_dir(os.path.dirname(os.path.abspath(path)) or ".")
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "type", "amount", "category", "account", "datetime", "remark", "receipt"])
        for r in rows:
            writer.writerow([
                r.get("id", ""),
                r.get("type", ""),
                r.get("amount", ""),
                r.get("category", ""),
                r.get("account", ""),
                r.get("datetime", ""),
                r.get("remark", ""),
                r.get("receipt", "")
            ])


def read_transactions_csv(path: str):
    out = []
    with open(path, "r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(row)
    return out