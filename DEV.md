# 服务器安全加固工具 - 开发文档

## 一、项目背景

### 1.1 背景

随着信息安全等级保护要求的不断提高，企业需要定期对服务器进行安全基线检查和加固。传统的人工逐台检查和配置效率低下，容易出错且难以统一管理。

本工具旨在实现服务器安全基线配置的自动化，支持批量对多个Linux节点进行安全加固配置，同时提供配置检查和回滚功能，确保配置变更的安全性和可追溯性。

### 1.2 目标

- 实现服务器安全基线配置的标准化、自动化
- 支持批量节点并行处理，提高效率
- 提供配置检查功能，实时掌握安全状态
- 支持配置回滚，确保变更可逆
- 生成详细的执行报告，便于审计追踪

---

## 二、核心功能

### 2.1 功能列表

| 功能 | 说明 |
|------|------|
| 批量执行 | 支持多节点并行安全加固配置 |
| 配置检查 | 检查当前节点的安全配置状态 |
| 任务回滚 | 支持单个或批量回滚配置变更 |
| 报告生成 | 输出JSON格式执行报告 |
| 多种认证 | 支持SSH密钥和密码认证 |
| 分类执行 | 支持按类别（密码/系统/SSH/权限）选择性执行 |

### 2.2 任务类别

#### 密码策略 (password)
- 密码最长使用天数
- 密码最短使用天数
- 密码最小长度
- 密码到期警告天数
- 密码复杂度要求

#### 系统安全 (system)
- 空口令账号检查
- UID为0的非root用户检查
- wheel组限制
- 日志服务配置
- 审计服务配置

#### SSH加固 (ssh)
- SSH协议版本
- 认证方式配置
- 日志级别
- 最大认证重试次数
- DNS反向解析

#### 文件权限 (permission)
- 系统文件权限设置
- 敏感文件访问控制

---

## 三、系统架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (CLI入口)                      │
│              参数解析、任务调度、结果输出                   │
└─────────────────────┬───────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │Inventory │ │SSHClient │ │Executor  │
   │ 节点管理  │ │SSH连接   │ │任务执行   │
   └──────────┘ └──────────┘ └──────────┘
         │            │            │
         │            │            ▼
         │            │     ┌──────────────┐
         │            │     │   Checker    │
         │            │     │   配置检查    │
         │            │     └──────────────┘
         │            │
         │            ▼
         │     ┌──────────────┐
         │     │   Tasks      │
         │     │  任务定义    │
         │     └──────────────┘
         │
         ▼
   ┌──────────────────────────────────────────┐
   │           Target Servers                 │
   │  192.168.1.10 | 192.168.1.11 | ...      │
   └──────────────────────────────────────────┘
```

### 3.2 模块说明

| 模块 | 文件 | 职责 |
|------|------|------|
| CLI入口 | main.py | 参数解析、任务调度、结果展示 |
| 节点管理 | inventory.py | 加载和验证节点配置 |
| SSH连接 | ssh_client.py | SSH连接、执行命令、回滚 |
| 执行器 | executor.py | 任务执行、结果记录、回滚逻辑 |
| 任务定义 | tasks/__init__.py | 定义所有安全加固任务 |
| 配置检查 | executor.py | 检查当前配置状态 |

### 3.3 数据流

```
1. 加载配置
   nodes.yaml → Inventory → Node List

2. 连接节点
   Node Info → SSHClient → SSH Connection

3. 执行任务
   Task List → Executor → SSH Command → Result

4. 保存结果
   Result → JSON Report → rollback_data

5. 回滚
   Report/Input → Executor.rollback → SSH.rollback
```

---

## 四、安装与运行

### 4.1 环境要求

- Python 3.8+
- Linux/Unix 服务器
- SSH访问权限

### 4.2 安装步骤

```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd security-harden-tool

# 2. 安装依赖
pip install paramiko pyyaml

# 3. 配置节点
vim nodes.yaml
```

### 4.3 目录结构

```
security-harden-tool/
├── main.py                 # CLI入口程序
├── inventory.py            # 节点配置管理
├── ssh_client.py           # SSH连接与命令执行
├── executor.py             # 任务执行与回滚
├── tasks/
│   └── __init__.py        # 任务定义
├── nodes.yaml             # 节点配置示例
├── requirements.txt        # Python依赖
├── README.md              # 使用文档
└── DEV.md                 # 开发文档
```

---

## 五、使用指南

### 5.1 快速开始

```bash
# 1. 配置节点
vim nodes.yaml

# 2. 检查配置状态
python main.py -n nodes.yaml --check

# 3. 执行安全加固
python main.py -n nodes.yaml --exec -o report.json

# 4. 查看报告
cat report.json
```

### 5.2 任务回滚

```bash
# 使用报告文件回滚
python main.py -n nodes.yaml -o report.json --rollback --task-name "检查密码最长使用天数"

# 手动指定原始值回滚
python main.py -n nodes.yaml --rollback --task-name "检查密码最长使用天数" --original-value "99999"
```

### 5.3 任务列表

所有可用任务名称：

**密码策略类**
- 检查密码最长使用天数
- 检查密码最短使用天数
- 检查密码需要满足的最短长度
- 检查用户密码到期前警告天数
- 密码复杂度设置

**系统安全类**
- 检查系统是否有空口令账号
- 配置只有wheel组中的用户才能su到root权限
- 避免记录不存在用户的登录信息
- 配置用户密码尝试次数
- 记录用户上次登录时间
- rsyslog服务是否开启
- audit服务是否开启

**SSH加固类**
- 检查ssh协议
- 记录所有信息，包括info信息
- 最大重试次数
- 允许密码验证
- 修改ChallengeResponseAuthentication
- 禁止设置空密码
- 禁止对远程主机名进行反向解析

**文件权限类**
- 配置/etc/passwd文件权限
- 配置/etc/shadow文件权限
- 配置/etc/crontab文件权限
- 配置/etc/init.d/*权限

---

## 六、API接口

### 6.1 Inventory 类

```python
from inventory import Inventory

# 加载节点配置
inventory = Inventory('nodes.yaml')
nodes = inventory.load()

# 获取单个节点
node = inventory.get_node('192.168.1.10')
```

### 6.2 SSHClient 类

```python
from ssh_client import SSHClient

# 创建连接
ssh = SSHClient(
    host='192.168.1.10',
    port=22,
    user='root',
    auth='key',
    key_path='~/.ssh/id_rsa'
)

# 执行命令
ssh.connect()
exit_code, stdout, stderr = ssh.execute('ls -la')
ssh.close()
```

### 6.3 Executor 类

```python
from executor import Executor, Checker
from ssh_client import SSHClient

ssh = SSHClient(...)
ssh.connect()

# 执行任务
executor = Executor(ssh)
results = executor.execute_category('password')

# 回滚任务
executor.rollback_task('检查密码最长使用天数', '99999')

ssh.close()
```

### 6.4 Checker 类

```python
from executor import Checker

checker = Checker(ssh)
check_results = checker.check_category('all')
```

---

## 七、配置说明

### 7.1 节点配置 (nodes.yaml)

```yaml
nodes:
  - host: 192.168.1.10
    port: 22
    user: root
    auth: key
    key_path: ~/.ssh/id_rsa
    
  - host: 192.168.1.20
    user: admin
    auth: password
    password: secret
```

### 7.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| host | string | 是 | 目标服务器IP或主机名 |
| port | int | 否 | SSH端口，默认22 |
| user | string | 是 | SSH用户名 |
| auth | string | 否 | 认证方式：key/password，默认key |
| key_path | string | 否 | SSH私钥路径 |
| password | string | 否 | SSH密码 |
| passphrase | string | 否 | 私钥密码 |

---

## 八、扩展开发

### 8.1 添加新任务

在 `tasks/__init__.py` 中添加任务定义：

```python
NEW_TASK = [
    {
        'name': '新任务名称',
        'command': '执行的命令',
        'check': '检查命令',
        'expected': '期望结果',
        'backup_key': '回滚标识'
    },
]

ALL_TASKS['category'].extend(NEW_TASK)
```

### 8.2 添加新回滚命令

在 `ssh_client.py` 的 `rollback` 方法中添加：

```python
rollback_cmds = {
    'NEW_KEY': f"回滚命令模板",
}
```

---

## 九、常见问题

### Q1: 连接失败
- 检查SSH服务是否运行
- 检查网络连通性
- 确认用户名和认证信息正确

### Q2: 权限不足
- 确保SSH用户有root权限
- 检查sudo配置

### Q3: 回滚失败
- 确认原始值正确
- 检查配置文件是否被其他程序修改
- 手动检查服务器状态
