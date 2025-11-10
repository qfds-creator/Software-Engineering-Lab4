"""
services.py - 事务、统计、导入导出等业务逻辑
"""
from typing import List, Optional, Dict, Tuple
from .models import Transaction, Account, Category, TxType
from . import utils
import copy
import datetime


class TransactionService:
    def __init__(self, txs: List[Transaction], accounts: List[Account], categories: List[Category]):
        self.txs = txs
        self.accounts = accounts
        self.categories = categories

    def add_transaction(self, tx: Transaction) -> Transaction:
        if not tx.id:
            tx.id = utils.generate_uuid()
        self.txs.append(tx)
        self.recalculate_balances()
        return tx

    def edit_transaction(self, tx_id: str, new_tx: Transaction) -> bool:
        for i, t in enumerate(self.txs):
            if t.id == tx_id:
                self.txs[i] = new_tx
                if not self.txs[i].id:
                    self.txs[i].id = tx_id
                self.recalculate_balances()
                return True
        return False

    def delete_transaction(self, tx_id: str) -> bool:
        orig_len = len(self.txs)
        self.txs = [t for t in self.txs if t.id != tx_id]
        if len(self.txs) != orig_len:
            self.recalculate_balances()
            return True
        return False

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        for t in self.txs:
            if t.id == tx_id:
                return t
        return None

    def list_transactions(self) -> List[Transaction]:
        return list(self.txs)

    def search_by_category(self, category_id: str) -> List[Transaction]:
        return [t for t in self.txs if t.category_id == category_id]

    def filter_by_date_range(self, start_iso: str, end_iso: str) -> List[Transaction]:
        def between(dt):
            if start_iso and dt < start_iso:
                return False
            if end_iso and dt > end_iso:
                return False
            return True
        return [t for t in self.txs if between(t.datetime)]

    def recalculate_balances(self):
        # reset
        for a in self.accounts:
            a.current_balance = float(a.initial_balance)
        # apply sorted by datetime
        sorted_tx = sorted(self.txs, key=lambda x: x.datetime)
        for t in sorted_tx:
            for a in self.accounts:
                if a.id == t.account_id:
                    if t.type == TxType.Income:
                        a.current_balance += t.amount
                    else:
                        a.current_balance -= t.amount


class StatisticsService:
    def __init__(self, txs: List[Transaction], categories: List[Category]):
        self.txs = txs
        self.categories = categories

    def calculate_totals(self, start_iso: str = "", end_iso: str = "") -> Tuple[float, float]:
        inc = 0.0
        exp = 0.0
        for t in self.txs:
            if start_iso and t.datetime < start_iso:
                continue
            if end_iso and t.datetime > end_iso:
                continue
            if t.type == TxType.Income:
                inc += t.amount
            else:
                exp += t.amount
        return inc, exp

    def top_categories(self, tx_type: TxType, top_n: int = 10, start_iso: str = "", end_iso: str = "") -> List[Dict]:
        sums = {}
        for t in self.txs:
            if t.type != tx_type:
                continue
            if start_iso and t.datetime < start_iso:
                continue
            if end_iso and t.datetime > end_iso:
                continue
            sums[t.category_id] = sums.get(t.category_id, 0.0) + t.amount
        items = sorted(sums.items(), key=lambda x: x[1], reverse=True)
        out = []
        for cid, total in items[:top_n]:
            name = cid
            for c in self.categories:
                if c.id == cid:
                    name = c.name
                    break
            out.append({"category_id": cid, "category_name": name, "total": total})
        return out


class ExportService:
    @staticmethod
    def export_transactions_to_csv(txs: List[Transaction], cats: List[Category], accts: List[Account], path: str) -> bool:
        rows = []
        for t in txs:
            catname = t.category_id
            for c in cats:
                if c.id == t.category_id:
                    catname = c.name
                    break
            acctname = t.account_id
            for a in accts:
                if a.id == t.account_id:
                    acctname = a.name
                    break
            rows.append({
                "id": t.id,
                "type": t.type.value,
                "amount": t.amount,
                "category": catname,
                "account": acctname,
                "datetime": t.datetime,
                "remark": t.remark,
                "receipt": t.receipt_path
            })
        try:
            utils.write_transactions_csv(path, rows)
            return True
        except Exception:
            return False

    @staticmethod
    def import_transactions_from_csv(path: str) -> List[Transaction]:
        data = utils.read_transactions_csv(path)
        out = []
        for row in data:
            t = Transaction(
                id=row.get("id") or utils.generate_uuid(),
                type=TxType(row.get("type") or TxType.Expense.value),
                amount=float(row.get("amount") or 0.0),
                category_id=row.get("category") or "",
                account_id=row.get("account") or "",
                datetime=row.get("datetime") or utils.current_datetime_iso(),
                remark=row.get("remark") or "",
                receipt_path=row.get("receipt") or ""
            )
            out.append(t)
        return out