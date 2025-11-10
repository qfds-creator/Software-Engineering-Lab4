```markdown
# FinanceApp — Python 实现（实验3）

简介
- 命令行的记账管理系统（Transaction/Account/Category/Reminder 核心模块），支持：
  - 交易增删改查（CRUD）
  - 账户与分类管理
  - 本地加密存储（PBKDF2 + AES-GCM）
  - 导出/导入 CSV
  - 备份数据（加密文件副本）
  - 简单统计（按分类汇总与排行）
  - 应用锁（密码、错误计数、自动锁定）

依赖
- Python 3.9+
- cryptography 库

快速安装（Ubuntu / Windows）
1. 克隆或复制本项目到本地目录，例如 ~/finance_app
2. 创建并激活虚拟环境（推荐）
   python3 -m venv .venv
   source .venv/bin/activate      # Linux/macOS
   .venv\Scripts\activate         # Windows (PowerShell)
3. 安装依赖
   pip install -r requirements.txt

运行
- 进入项目目录，运行：
  python -m src.main
- 首次运行会提示输入应用密码（可留空），并会创建加密数据文件 `data.enc`。

文件结构（建议）
finance_app/
├── README.md
├── requirements.txt
└── src
    ├── main.py
    ├── models.py
    ├── utils.py
    ├── encryption.py
    ├── storage.py
    └── services.py

安全说明
- 本实现使用 PBKDF2（SHA256）进行 key 派生，并使用 AES-GCM 进行加密与完整性校验。存储结构保存 salt 与 nonce 以支持解密。
- 课堂实验实现已考虑基本安全实践，但生产环境应使用更严格的密钥管理策略（如 Argon2、密钥轮换、硬件密钥库等）。
```