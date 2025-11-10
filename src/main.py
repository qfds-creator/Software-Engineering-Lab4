"""
main.py - CLI 入口，提供菜单用于交互（添加/编辑/删除交易、导入/导出、统计、备份、账户/分类管理、应用锁）
运行： python -m src.main
"""
import sys
import os
from .models import Transaction, Account, Category, AppLock, TxType
from .storage import LocalStorage
from .services import TransactionService, StatisticsService, ExportService
from . import utils, encryption
import traceback

DATA_FILE = "data.enc"


def input_nonempty(prompt: str) -> str:
    val = input(prompt).strip()
    return val


def print_main_menu():
    print("\n=== FinanceApp 主菜单 ===")
    print("1) 添加交易")
    print("2) 编辑交易")
    print("3) 删除交易")
    print("4) 列出交易")
    print("5) 搜索/筛选交易")
    print("6) 导出交易(CSV)")
    print("7) 导入交易(CSV)")
    print("8) 备份数据")
    print("9) 查看统计（区间）")
    print("10) 管理账户")
    print("11) 管理分类")
    print("12) 应用锁设置")
    print("0) 退出并保存")
    print("请选择: ", end="", flush=True)


def main():
    print("FinanceApp (Python 实现)")

    pwd = input("请输入应用密码（若空则使用空密码）：").strip()
    storage = LocalStorage(DATA_FILE, pwd)
    try:
        txs, accounts, categories, applock = storage.load()
    except Exception as e:
        print("加载数据失败:", e)
        # If decrypt failed, ask user whether to continue with empty dataset or exit
        ans = input("是否以空数据继续？(y/N): ").strip().lower()
        if ans != "y":
            return
        txs, accounts, categories, applock = [], [], [], AppLock()

    # Check applock
    if applock.enabled:
        import time
        now = int(time.time())
        if applock.lock_until > now:
            import time as _t
            print("应用暂时被锁定，直到：", _t.ctime(applock.lock_until))
            return
        ok = False
        for i in range(5):
            p = input("请输入应用密码：")
            if encryption.hash_password_hex(p) == applock.password_hash:
                ok = True
                applock.wrong_attempts = 0
                break
            else:
                applock.wrong_attempts += 1
                print("密码错误")
                if applock.wrong_attempts >= 5:
                    applock.lock_until = int(time.time()) + 600
                    print("连续失败，应用锁定 10 分钟")
                    break
        if not ok and applock.lock_until > int(time.time()):
            # save lock state and exit
            storage.save(txs, accounts, categories, applock)
            return

    # ensure default account / category if empty
    if not accounts:
        a = Account(id=utils.generate_uuid(), name="现金", initial_balance=0.0, current_balance=0.0)
        accounts.append(a)
    if not categories:
        c1 = Category(id=utils.generate_uuid(), name="餐饮", type=TxType.Expense, color="#FF0000")
        c2 = Category(id=utils.generate_uuid(), name="工资", type=TxType.Income, color="#00AA00")
        categories.extend([c1, c2])

    tx_service = TransactionService(txs, accounts, categories)
    stat_service = StatisticsService(txs, categories)

    running = True
    while running:
        try:
            print_main_menu()
            choice = input().strip()
            if choice == "1":
                # add transaction
                typ = input("类型 (0:收入 1:支出): ").strip()
                ttype = TxType.Income if typ == "0" else TxType.Expense
                amt = float(input("金额: ").strip())
                print("可用分类:")
                for c in categories:
                    print(f"{c.id} : {c.name} ({c.type.value})")
                cid = input("输入分类ID: ").strip()
                print("可用账户:")
                for a in accounts:
                    print(f"{a.id} : {a.name} (余额 {a.current_balance})")
                aid = input("输入账户ID: ").strip()
                dt = input("时间 (空用当前 YYYY-MM-DDTHH:MM:SS): ").strip()
                if not dt:
                    dt = utils.current_datetime_iso()
                remark = input("备注(可选): ").strip()
                tx = Transaction(
                    id=utils.generate_uuid(),
                    type=ttype,
                    amount=amt,
                    category_id=cid,
                    account_id=aid,
                    datetime=dt,
                    remark=remark
                )
                tx_service.add_transaction(tx)
                print("已添加交易:", tx.id)
            elif choice == "2":
                tid = input("输入要编辑的交易ID: ").strip()
                t = tx_service.get_transaction(tid)
                if not t:
                    print("未找到交易")
                    continue
                print("当前金额:", t.amount)
                s = input("新金额(回车保留): ").strip()
                if s:
                    t.amount = float(s)
                s = input(f"当前备注: {t.remark} 新备注回车保留: ").strip()
                if s:
                    t.remark = s
                tx_service.edit_transaction(tid, t)
                print("已更新")
            elif choice == "3":
                tid = input("输入要删除的交易ID: ").strip()
                if tx_service.delete_transaction(tid):
                    print("删除成功")
                else:
                    print("未找到")
            elif choice == "4":
                alltx = tx_service.list_transactions()
                print(f"共 {len(alltx)} 条交易：")
                for t in alltx:
                    print(f"{t.id} | {t.type.value} | {t.amount} | {t.datetime} | {t.remark}")
            elif choice == "5":
                st = input("开始时间 (空不限制): ").strip()
                ed = input("结束时间 (空不限制): ").strip()
                res = tx_service.filter_by_date_range(st, ed)
                print(f"筛选结果 {len(res)} 条：")
                for t in res:
                    print(f"{t.id} | {t.type.value} | {t.amount} | {t.datetime} | {t.remark}")
            elif choice == "6":
                path = input("导出 CSV 路径 (例如 export.csv): ").strip()
                ok = ExportService.export_transactions_to_csv(txs, categories, accounts, path)
                print("导出成功" if ok else "导出失败")
            elif choice == "7":
                path = input("导入 CSV 路径: ").strip()
                imported = ExportService.import_transactions_from_csv(path)
                for t in imported:
                    tx_service.add_transaction(t)
                print(f"已导入 {len(imported)} 条")
            elif choice == "8":
                import time
                t = int(time.time())
                bpath = f"data_backup_{t}.enc"
                if storage.backup(bpath):
                    print("备份成功:", bpath)
                else:
                    print("备份失败")
            elif choice == "9":
                st = input("开始时间 (空不限制): ").strip()
                ed = input("结束时间 (空不限制): ").strip()
                inc, ex = stat_service.calculate_totals(st, ed)
                print(f"收入合计: {inc} 支出合计: {ex}")
                top = stat_service.top_categories(TxType.Expense, 10, st, ed)
                print("支出排行：")
                for s in top:
                    print(f"{s['category_name']} : {s['total']}")
            elif choice == "10":
                op = input("账户: 1) 新增 2) 列表 请选择: ").strip()
                if op == "1":
                    name = input("名称: ").strip()
                    bal = float(input("初始余额: ").strip() or "0")
                    a = Account(id=utils.generate_uuid(), name=name, initial_balance=bal, current_balance=bal)
                    accounts.append(a)
                    print("已添加账户", a.id)
                else:
                    for a in accounts:
                        print(f"{a.id} | {a.name} | 初始 {a.initial_balance} | 当前 {a.current_balance}")
            elif choice == "11":
                op = input("分类: 1) 新增 2) 列表 请选择: ").strip()
                if op == "1":
                    name = input("名称: ").strip()
                    tp = input("类型 (0:收入 1:支出): ").strip()
                    ctype = TxType.Income if tp == "0" else TxType.Expense
                    color = input("颜色(例如 #FF0000): ").strip() or "#000000"
                    c = Category(id=utils.generate_uuid(), name=name, type=ctype, color=color)
                    categories.append(c)
                    print("已添加分类", c.id)
                else:
                    for c in categories:
                        print(f"{c.id} | {c.name} | {c.type.value}")
            elif choice == "12":
                op = input("应用锁: 1) 启用/修改密码 2) 关闭 请选择: ").strip()
                if op == "1":
                    p = input("请输入新密码: ")
                    applock.enabled = True
                    applock.password_hash = encryption.hash_password_hex(p)
                    applock.wrong_attempts = 0
                    applock.lock_until = 0
                    print("已设置应用锁")
                else:
                    applock.enabled = False
                    applock.password_hash = ""
                    applock.wrong_attempts = 0
                    applock.lock_until = 0
                    print("已关闭应用锁")
            elif choice == "0":
                try:
                    storage.save(txs, accounts, categories, applock)
                    print("已保存，退出")
                except Exception as e:
                    print("保存失败:", e)
                    traceback.print_exc()
                running = False
            else:
                print("未知选项")
        except KeyboardInterrupt:
            print("\n捕获中断，保存后退出...")
            storage.save(txs, accounts, categories, applock)
            break
        except Exception as e:
            print("运行时异常：", e)
            traceback.print_exc()

    print("Bye")


if __name__ == "__main__":
    main()