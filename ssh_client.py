import paramiko
from typing import Dict, Any, Optional, Tuple
import os
import time


class SSHClient:
    def __init__(self, host: str, port: int, user: str, 
                 auth: str = 'key', 
                 key_path: Optional[str] = None,
                 password: Optional[str] = None,
                 passphrase: Optional[str] = None,
                 timeout: int = 30):
        self.host = host
        self.port = port
        self.user = user
        self.auth = auth
        self.key_path = key_path
        self.password = password
        self.passphrase = passphrase
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self._backup_commands: Dict[str, str] = {}
        
    def connect(self) -> bool:
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.auth == 'key':
                key_path = self.key_path or os.path.expanduser('~/.ssh/id_rsa')
                key = paramiko.RSAKey.from_private_key_file(
                    key_path, 
                    password=self.passphrase
                )
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    pkey=key,
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
            return True
        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False
    
    def execute(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        if not self.client:
            raise RuntimeError("Not connected")
        
        stdin, stdout, stderr = self.client.exec_command(
            command, 
            timeout=timeout
        )
        exit_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode('utf-8', errors='ignore')
        stderr_str = stderr.read().decode('utf-8', errors='ignore')
        
        return exit_code, stdout_str, stderr_str
    
    def execute_with_backup(self, command: str, backup_key: str, 
                           check_cmd: str) -> Tuple[int, str, str]:
        # 执行前先备份当前配置
        exit_code, before, _ = self.execute(check_cmd)
        if exit_code == 0 and before.strip():
            self._backup_commands[backup_key] = before.strip()
        
        return self.execute(command)
    
    def get_backup(self, key: str) -> Optional[str]:
        return self._backup_commands.get(key)
    
    def rollback(self, backup_key: str, original_value: str = "") -> bool:
        backup_value = self._backup_commands.get(backup_key) or original_value or ""
        if not backup_value:
            print(f"  [WARN] No backup found for: {backup_key}")
            return False
        
        rollback_cmds = {
            'PASS_MAX_DAYS': f"sed -i 's/PASS_MAX_DAYS.*/PASS_MAX_DAYS    {backup_value}/' /etc/login.defs",
            'PASS_MIN_DAYS': f"sed -i 's/PASS_MIN_DAYS.*/PASS_MIN_DAYS    {backup_value}/' /etc/login.defs",
            'PASS_MIN_LEN': f"sed -i 's/PASS_MIN_LEN.*/PASS_MIN_LEN     {backup_value}/' /etc/login.defs",
            'PASS_WARN_AGE': f"sed -i 's/PASS_WARN_AGE.*/PASS_WARN_AGE    {backup_value}/' /etc/login.defs",
            'PAM_PASSWORD': f"sed -i 's/minlen=8/minlen=5/; s/difok=3//; s/ucredit=-1//; s/lcredit=-1//; s/dcredit=-1//; s/ocredit=-1//; s/enforce_for_root//' /etc/pam.d/system-auth 2>/dev/null || true",
            'SU_WHEEL': "sed -i 's/^SU_WHEEL_ONLY.*//' /etc/login.defs",
            'LOG_UNKFAIL': "sed -i 's/^LOG_UNKFAIL_ENAB.*//' /etc/login.defs",
            'LOGIN_RETRIES': "sed -i 's/^LOGIN_RETRIES.*//' /etc/login.defs",
            'LASTLOG': "sed -i 's/^LASTLOG_ENAB.*//' /etc/login.defs",
            'RSYSLOG': "systemctl stop rsyslog.service",
            'AUDIT': "systemctl stop audit.service",
            'SSH_PROTOCOL': "sed -i '/^Protocol/d' /etc/ssh/sshd_config",
            'SSH_LOGLEVEL': "sed -i 's/^LogLevel.*/#LogLevel INFO/' /etc/ssh/sshd_config",
            'SSH_MAXAUTH': "sed -i 's/^MaxAuthTries.*/#MaxAuthTries 6/' /etc/ssh/sshd_config",
            'SSH_PWD_AUTH': "sed -i 's/^PasswordAuthentication.*/#PasswordAuthentication no/' /etc/ssh/sshd_config",
            'SSH_CHALLENGE': "sed -i 's/^ChallengeResponseAuthentication.*/#ChallengeResponseAuthentication no/' /etc/ssh/sshd_config",
            'SSH_EMPTY_PWD': "sed -i 's/^PermitEmptyPasswords.*/#PermitEmptyPasswords no/' /etc/ssh/sshd_config",
            'SSH_USEDNS': "sed -i 's/^UseDNS.*/#UseDNS yes/' /etc/ssh/sshd_config",
        }
        
        if backup_key in rollback_cmds:
            cmd = rollback_cmds[backup_key]
            exit_code, stdout, stderr = self.execute(cmd)
            if exit_code == 0:
                print(f"  [OK] Rolled back {backup_key} to: {backup_value}")
                return True
            else:
                print(f"  [ERROR] Rollback failed: {stderr}")
                return False
        
        print(f"  [WARN] No rollback command for: {backup_key}, trying generic restore")
        return False
    
    def close(self):
        if self.client:
            self.client.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
