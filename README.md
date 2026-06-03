# 课时兑换学分系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 `Flask + MySQL` 的课时申请与学分兑换系统，支持学生在线提交课时申请、教师审核、管理员分配审核教师、学分兑换等完整业务流程。

## ✨ 功能特性

### 核心功能
- 🎓 **课时申请流程**：学生提交 → 管理员分配 → 教师审核 → 课时入账
- 💱 **学分兑换流程**：学生申请 → 管理员审核 → 课时扣减 → 学分发放
- 👥 **多角色支持**：学生、教师、管理员三种角色，权限隔离
- 📎 **文件上传**：支持课时申请证明材料上传
- 📊 **课时账户**：自动统计课时收支，实时显示可用余额

### 特色功能
- ⚡ **智能联动**：专业-课程-教师三级联动选择
- 🎯 **前端验证**：必填字段智能提示，自动定位错误字段
- 🛡️ **异常处理**：网络/数据库错误友好提示，表单数据保留
- 🔄 **快速审核**：教师端支持"下一个"按钮快速跳转
- 📝 **统一规范**：所有空值统一显示为"空"

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MySQL 5.7+ / 8.0+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/你的用户名/课时兑换学分系统.git
cd 课时兑换学分系统
```

2. **创建虚拟环境**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制环境变量示例文件
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 编辑 .env 文件，修改数据库连接信息
# DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/数据库名?charset=utf8mb4
```

5. **创建数据库**
```sql
CREATE DATABASE credit_exchange_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **初始化数据库**
```bash
# 应用数据库迁移
flask db upgrade

# 导入基础数据（任务类型、系统配置、测试账号）
flask seed-basic-data
```

7. **启动服务**
```bash
python run.py
```

8. **访问系统**
```
打开浏览器访问：http://127.0.0.1:5000
```

## 👤 默认测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher1 | teacher123 |
| 学生 | student1 | student123 |

> ⚠️ **安全提示**：生产环境请务必修改默认密码！

## 📁 项目结构

```
课时兑换学分系统/
├── app/                          # 应用主目录
│   ├── __init__.py              # Flask 应用工厂
│   ├── config.py                # 配置文件
│   ├── extensions.py            # Flask 扩展初始化
│   ├── models/                  # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── student.py          # 学生模型
│   │   ├── teacher.py          # 教师模型
│   │   ├── hour_application.py # 课时申请模型
│   │   └── ...
│   ├── modules/                 # 业务模块（按角色划分）
│   │   ├── auth/               # 认证模块
│   │   ├── student/            # 学生端模块
│   │   ├── teacher/            # 教师端模块
│   │   ├── admin/              # 管理员端模块
│   │   └── credit_exchange/    # 学分兑换模块
│   ├── services/                # 业务逻辑层
│   │   ├── hour_application_service.py
│   │   ├── credit_exchange_service.py
│   │   └── ...
│   ├── templates/               # HTML 模板
│   │   ├── base.html           # 基础模板
│   │   ├── student/            # 学生端页面
│   │   ├── teacher/            # 教师端页面
│   │   └── admin/              # 管理员端页面
│   ├── static/                  # 静态文件
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/            # 用户上传文件（不纳入版本控制）
│   ├── utils/                   # 工具函数
│   └── commands/                # Flask CLI 命令
├── migrations/                   # 数据库迁移文件
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略文件
├── requirements.txt             # Python 依赖
├── run.py                       # 启动文件
├── README.md                    # 项目说明
├── 超详细需求文档.md            # 详细需求文档
└── 第一阶段任务功能详情描述.md  # 功能说明文档
```

## 🔐 安全建议

1. **生产环境**：
   - 修改 `.env` 中的 `SECRET_KEY`
   - 修改所有默认密码
   - 使用 HTTPS
   - 配置防火墙

2. **数据库**：
   - 使用强密码
   - 限制远程访问
   - 定期备份

3. **文件上传**：
   - 限制文件类型
   - 限制文件大小（当前 10MB）
   - 病毒扫描

## 📖 详细文档

- [超详细需求文档.md](超详细需求文档.md) - 完整的业务需求和数据库设计
- [第一阶段任务功能详情描述.md](第一阶段任务功能详情描述.md) - 当前阶段功能清单

## 🛠️ 技术栈

- **后端框架**：Flask 3.0.3
- **数据库**：MySQL 5.7+ / 8.0+
- **ORM**：SQLAlchemy 3.1.1
- **认证**：Flask-Login 0.6.3
- **表单**：Flask-WTF 1.2.1
- **数据库迁移**：Flask-Migrate 4.0.7
- **前端框架**：Bootstrap 5.3.3
- **模板引擎**：Jinja2

## 📝 开发计划

### 第一阶段 ✅
- [x] 用户认证与权限管理
- [x] 课时申请流程
- [x] 教师审核功能
- [x] 学分兑换流程
- [x] 课时账户管理

### 第二阶段（规划中）
- [ ] 企业微信集成
- [ ] 消息通知功能
- [ ] 高级筛选功能
- [ ] 批量操作
- [ ] 统计报表
- [ ] 多级审核
- [ ] 驳回后重新提交

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 💬 联系方式

如有问题，请提交 [Issue](https://github.com/你的用户名/课时兑换学分系统/issues)

---

**注意**：本项目仅供学习交流使用，生产环境使用前请做好安全加固！
