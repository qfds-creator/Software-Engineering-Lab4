"""
storage.py - 本地加密存储：序列化 JSON -> encrypt -> write file
Load: read file -> decrypt -> parse JSON
"""
from typing import List, Tuple
import json
import os
from .models import Transaction, Account, Category, AppLock, DataBundle
from . import encryption, utils


DEFAULT_DATA_FILE = "data.enc"


class LocalStorage:
    def __init__(self, path: str = DEFAULT_DATA_FILE, password: str = ""):
        self.path = path
        self.password = password or ""
        # when file exists, the salt is embedded in file; password must match to decrypt.

    def load(self) -> Tuple[List[Transaction], List[Account], List[Category], AppLock]:
        if not utils.file_exists(self.path):
            # return empty
            return [], [], [], AppLock()
        raw = utils.read_bytes(self.path)
        try:
            plaintext = encryption.decrypt(raw, self.password)
        except Exception as e:
            raise RuntimeError(f"Decrypt failed: {e}")
        s = plaintext.decode("utf-8")
        bundle = DataBundle.from_json(s)
        txs = [Transaction.from_dict(t) for t in bundle.transactions]
        accts = [Account.from_dict(a) for a in bundle.accounts]
        cats = [Category.from_dict(c) for c in bundle.categories]
        applock = AppLock.from_dict(bundle.applock) if bundle.applock else AppLock()
        return txs, accts, cats, applock

    def save(self, txs: List[Transaction], accts: List[Account], cats: List[Category], applock: AppLock) -> bool:
        bundle = DataBundle(
            transactions=[t.to_dict() for t in txs],
            accounts=[a.to_dict() for a in accts],
            categories=[c.to_dict() for c in cats],
            applock=applock.to_dict()
        )
        txt = bundle.to_json().encode("utf-8")
        blob = encryption.encrypt(txt, self.password)
        utils.write_bytes(self.path, blob)
        return True

    def backup(self, backup_path: str) -> bool:
        try:
            utils.ensure_dir(os.path.dirname(os.path.abspath(backup_path)) or ".")
            data = utils.read_bytes(self.path)
            utils.write_bytes(backup_path, data)
            return True
        except Exception:
            return False