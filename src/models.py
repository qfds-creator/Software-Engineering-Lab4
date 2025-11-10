"""
models.py - 数据模型（交易、账户、分类、应用锁）
"""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List
import time
import json


class TxType(str, Enum):
    Income = "income"
    Expense = "expense"


@dataclass
class Transaction:
    id: str
    type: TxType
    amount: float
    category_id: str
    account_id: str
    datetime: str  # ISO8601 string
    remark: str = ""
    receipt_path: str = ""

    def to_dict(self):
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @staticmethod
    def from_dict(d):
        return Transaction(
            id=d.get("id", ""),
            type=TxType(d.get("type", TxType.Expense.value)),
            amount=float(d.get("amount", 0.0)),
            category_id=d.get("category_id", ""),
            account_id=d.get("account_id", ""),
            datetime=d.get("datetime", ""),
            remark=d.get("remark", ""),
            receipt_path=d.get("receipt_path", ""),
        )


@dataclass
class Account:
    id: str
    name: str
    icon: str = ""
    initial_balance: float = 0.0
    current_balance: float = 0.0

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Account(
            id=d.get("id", ""),
            name=d.get("name", ""),
            icon=d.get("icon", ""),
            initial_balance=float(d.get("initial_balance", 0.0)),
            current_balance=float(d.get("current_balance", 0.0)),
        )


@dataclass
class Category:
    id: str
    name: str
    icon: str = ""
    color: str = "#000000"
    type: TxType = TxType.Expense

    def to_dict(self):
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @staticmethod
    def from_dict(d):
        return Category(
            id=d.get("id", ""),
            name=d.get("name", ""),
            icon=d.get("icon", ""),
            color=d.get("color", "#000000"),
            type=TxType(d.get("type", TxType.Expense.value)),
        )


@dataclass
class AppLock:
    enabled: bool = False
    password_hash: str = ""  # hex sha256
    wrong_attempts: int = 0
    lock_until: int = 0  # epoch seconds

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return AppLock(
            enabled=bool(d.get("enabled", False)),
            password_hash=d.get("password_hash", ""),
            wrong_attempts=int(d.get("wrong_attempts", 0)),
            lock_until=int(d.get("lock_until", 0)),
        )


@dataclass
class DataBundle:
    transactions: List[dict]
    accounts: List[dict]
    categories: List[dict]
    applock: dict

    def to_json(self):
        return json.dumps({
            "transactions": self.transactions,
            "accounts": self.accounts,
            "categories": self.categories,
            "applock": self.applock
        }, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(s: str):
        data = json.loads(s)
        return DataBundle(
            transactions=data.get("transactions", []),
            accounts=data.get("accounts", []),
            categories=data.get("categories", []),
            applock=data.get("applock", {})
        )