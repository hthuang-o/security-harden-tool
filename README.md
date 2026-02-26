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
