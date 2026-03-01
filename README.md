# 服务器安全加固工具 - 使用文档

## 概述

本工具用于批量对多个Linux节点进行安全配置加固，支持配置检查、执行加固、任务回滚等功能。

## 环境要求

- Python 3.8+
- 依赖包: `paramiko`, `pyyaml`

安装依赖:
```bash
pip install paramiko pyyaml
```

## 节点配置

编辑 `nodes.yaml` 文件配置目标节点:

```yaml
# 方式1: SSH密钥认证
nodes:
  - host: 192.168.1.10
    port: 22
    user: root
    auth: key
    key_path: ~/.ssh/id_rsa
    
  - host: 192.168.1.11
    user: admin
    auth: key

# 方式2: 密码认证
# nodes:
#   - host: 192.168.1.20
#     user: root
#     auth: password
#     password: your_password

# 方式3: 混合使用
# nodes:
#   - host: 192.168.1.10
#     user: root
#     auth: key
#   
#   - host: 192.168.1.20
#     user: admin
#     auth: password
#     password: secret
```

## 使用方法

### 1. 检查当前配置状态

```bash
python main.py -n nodes.yaml --check
```

### 2. 执行安全加固

```bash
python main.py -n nodes.yaml --exec
```

### 3. 仅检查不执行

```bash
python main.py -n nodes.yaml --check-only
```

### 4. 执行特定类别

```bash
# 仅执行密码策略
python main.py -n nodes.yaml -t password --exec

# 仅执行系统安全配置
python main.py -n nodes.yaml -t system --exec

# 仅执行SSH加固
python main.py -n nodes.yaml -t ssh --exec

# 仅执行文件权限配置
python main.py -n nodes.yaml -t permission --exec

# 执行所有类别
python main.py -n nodes.yaml -t all --exec
```

### 5. 回滚任务

回滚支持3种方式：

**方式1: 使用之前的报告文件（推荐）**
```bash
# 先执行并保存报告
python main.py -n nodes.yaml -t password --exec -o report.json

# 回滚时指定报告文件，系统会自动读取原始值
python main.py -n nodes.yaml -o report.json --rollback --task-name "检查密码最长使用天数"
```

**方式2: 手动指定原始值**
```bash
python main.py -n nodes.yaml --rollback --task-name "检查密码最长使用天数" --original-value "99999"
```

**方式3: 自动获取当前值回滚**
```bash
# 如果没有报告文件，系统会尝试从服务器获取当前配置值进行回滚
python main.py -n nodes.yaml --rollback --task-name "检查密码最长使用天数"
```

**批量回滚所有任务**
```bash
# 先检查当前状态
python main.py -n nodes.yaml --check
```

### 6. 使用密码认证

```bash
# 命令行指定密码
python main.py -n nodes.yaml -u admin -p 'password' --exec

# 或在nodes.yaml中配置
```

### 7. 输出报告

```bash
# 保存JSON格式报告
python main.py -n nodes.yaml --exec -o report.json

# 指定并发数
python main.py -n nodes.yaml --exec -j 10
```

## 任务类别说明

| 类别 | 说明 |
|------|------|
| password | 密码策略配置（密码长度、复杂度、最长/最短使用天数等） |
| system | 系统安全配置（空口令检查、wheel组、日志服务等） |
| ssh | SSH安全加固（协议版本、认证方式、日志级别等） |
| permission | 文件权限配置（/etc/passwd、/etc/shadow等系统文件权限） |

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-n, --nodes` | 节点配置文件路径（必需） |
| `-t, --task` | 任务类别: all/password/system/ssh/permission |
| `--check` | 检查当前配置状态 |
| `--check-only` | 仅检查不执行 |
| `--exec` | 执行安全加固 |
| `--rollback` | 回滚任务 |
| `-u, --user` | SSH用户名 |
| `-p, --password` | SSH密码 |
| `-k, --key` | SSH私钥路径 |
| `--passphrase` | SSH私钥 passphrase |
| `--task-name` | 回滚时指定任务名称 |
| `--original-value` | 回滚时指定原始值（可选） |
| `--timeout` | SSH连接超时时间（默认30秒） |
| `-j, --jobs` | 并发数（默认5） |
| `-o, --output` | 输出报告文件路径 |
| `-v, --verbose` | 详细输出 |

## 输出示例

```
Loaded 2 nodes
Mode: exec, Task: all

============================================================
Host: 192.168.1.10
Status: completed
Success: 35/35

  ✓ 检查密码最长使用天数
  ✓ 检查密码最短使用天数
  ✓ 检查密码需要满足的最短长度
  ...

Rollback available for:
  - 检查密码最长使用天数: 99999
  - 检查密码最短使用天数: 0
  ...

============================================================
Host: 192.168.1.11
Status: completed
Success: 35/35
  ...
```

## 注意事项

1. 建议在生产环境执行前，先在测试环境验证
2. 部分配置修改后需要重启相应服务（如SSH）
3. 执行前请确保有系统备份
4. 建议在业务低峰期执行
5. 部分命令需要root权限

## 错误处理

- 连接失败: 检查SSH配置和网络连通性
- 权限不足: 确保SSH用户有sudo权限
- 执行失败: 查看详细错误信息，可使用回滚功能恢复

---

# Web 界面使用指南

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python app.py
```

服务启动后，访问 http://localhost:5000 即可打开 Web 界面。

## 功能介绍

### 1. 节点管理

在「节点管理」页面可以：
- 查看所有已配置的服务器节点
- 添加新节点（支持 SSH 密钥和密码认证）
- 测试节点连接是否正常
- 删除不需要的节点

### 2. 任务执行

在「任务执行」页面可以：

**选择节点**
- 勾选需要执行任务的服务器节点
- 支持全选/取消全选

**配置执行选项**
- 执行模式：
  - 检查模式：只检查配置状态，不执行修改
  - 执行模式：执行安全加固操作
- 任务类别：
  - 全部任务
  - 密码策略（5项）
  - 系统安全（9项）
  - SSH加固（10项）
  - 文件权限（13项）

**执行任务**
- 点击「开始执行」按钮
- 系统会提示输入各节点的 SSH 密码（如果使用密码认证）
- 实时显示执行进度和结果
- 执行完成后，每个任务项会显示「回滚」按钮（仅成功执行且可回滚的任务）

### 3. 报告查看

在「报告查看」页面可以：
- 查看历史执行记录列表
- 查看每条记录的统计信息（合规/成功数、失败数）
- 点击「查看详情」查看完整的执行结果
- 饼图可视化展示结果分布

## API 接口说明

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/nodes` | GET | 获取节点列表 |
| `/api/nodes` | POST | 添加新节点 |
| `/api/nodes/<host>` | PUT | 更新节点信息 |
| `/api/nodes/<host>` | DELETE | 删除节点 |
| `/api/nodes/<host>/test` | POST | 测试节点连接 |
| `/api/tasks` | GET | 获取任务列表 |
| `/api/execute` | POST | 执行任务 |
| `/api/tasks/<task_id>` | GET | 获取执行状态 |
| `/api/reports` | GET | 获取历史报告 |
| `/api/reports/<id>` | GET | 获取报告详情 |
| `/api/rollback` | POST | 回滚任务 |

## 配置文件说明

- `nodes.yaml` - 服务器节点配置
- `reports/` - 执行报告存储目录
