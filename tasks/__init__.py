# Security Hardening Tasks

PASSWORD_POLICY_TASKS = [
    {
        'name': '检查密码最长使用天数',
        'command': "sed -ri '/PASS_MAX_DAYS/s/99999/90/g' /etc/login.defs",
        'check': "grep PASS_MAX_DAYS /etc/login.defs | grep -v '^#'",
        'expected': '90',
        'backup_key': 'PASS_MAX_DAYS'
    },
    {
        'name': '检查密码最短使用天数',
        'command': "sed -ri '/PASS_MIN_DAYS/s/0/1/g' /etc/login.defs",
        'check': "grep PASS_MIN_DAYS /etc/login.defs | grep -v '^#'",
        'expected': '1',
        'backup_key': 'PASS_MIN_DAYS'
    },
    {
        'name': '检查密码需要满足的最短长度',
        'command': "sed -ri '/PASS_MIN_LEN/s/5/8/g' /etc/login.defs",
        'check': "grep PASS_MIN_LEN /etc/login.defs | grep -v '^#'",
        'expected': '8',
        'backup_key': 'PASS_MIN_LEN'
    },
    {
        'name': '检查用户密码到期前警告天数',
        'command': "sed -ri '/PASS_WARN_AGE/s/7/14/g' /etc/login.defs",
        'check': "grep PASS_WARN_AGE /etc/login.defs | grep -v '^#'",
        'expected': '14',
        'backup_key': 'PASS_WARN_AGE'
    },
    {
        'name': '密码复杂度设置',
        'command': "sed -i 's/retry=3 authtok_type=/retry=3 authtok_type= minlen=8 difok=3 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1 enforce_for_root/' /etc/pam.d/system-auth",
        'check': "grep 'minlen=8' /etc/pam.d/system-auth",
        'expected': 'minlen=8',
        'backup_key': 'PAM_PASSWORD'
    },
]

SYSTEM_SECURITY_TASKS = [
    {
        'name': '检查系统是否有空口令账号',
        'command': "echo 'skip empty password check'",
        'check': "cat /etc/shadow |awk -F ':' 'length($2)==0 {print $1}'",
        'expected': '',
        'allow_empty': True
    },
    {
        'name': '检查用户密码到期前警告天数',
        'command': "echo 'skip uid check'",
        'check': "awk -F ':' '$3==0||$4==0 {print}' /etc/passwd",
        'expected': 'root',
        'allow_empty': True
    },
    {
        'name': '配置只有wheel组中的用户才能su到root权限',
        'command': "sed '/#*pam_wheel.so*/s/^#//' /etc/pam.d/su;echo -e '\\n\\nSU_WHEEL_ONLY yes' >> /etc/login.defs",
        'check': "grep 'SU_WHEEL_ONLY' /etc/login.defs",
        'expected': 'SU_WHEEL_ONLY',
        'backup_key': 'SU_WHEEL'
    },
    {
        'name': '避免记录不存在用户的登录信息',
        'command': "echo -e '\\n\\nLOG_UNKFAIL_ENAB yes'>> /etc/login.defs",
        'check': "grep 'LOG_UNKFAIL_ENAB' /etc/login.defs",
        'expected': 'yes',
        'backup_key': 'LOG_UNKFAIL'
    },
    {
        'name': '配置用户密码尝试次数',
        'command': "echo -e '\\n\\nLOGIN_RETRIES 6'>> /etc/login.defs",
        'check': "grep 'LOGIN_RETRIES' /etc/login.defs",
        'expected': '6',
        'backup_key': 'LOGIN_RETRIES'
    },
    {
        'name': '记录用户上次登录时间',
        'command': "echo -e '\\n\\nLASTLOG_ENAB yes'>> /etc/login.defs",
        'check': "grep 'LASTLOG_ENAB' /etc/login.defs",
        'expected': 'yes',
        'backup_key': 'LASTLOG'
    },
    {
        'name': '检查是否禁止普通用户重起服务器权限',
        'command': "rm -rf /etc/security/console.apps/poweroff /etc/security/console.apps/reboot /etc/security/console.apps/halt 2>/dev/null || true",
        'check': "ls /etc/security/console.apps | grep -E 'poweroff|reboot|halt'",
        'expected': '',
        'allow_empty': True
    },
    {
        'name': 'rsyslog服务是否开启',
        'command': "systemctl start rsyslog.service && systemctl enable rsyslog.service",
        'check': "systemctl is-active rsyslog.service",
        'expected': 'active',
        'backup_key': 'RSYSLOG'
    },
    {
        'name': 'audit服务是否开启',
        'command': "systemctl start audit.service && systemctl enable audit.service",
        'check': "systemctl is-active audit.service",
        'expected': 'active',
        'backup_key': 'AUDIT'
    },
]

FILE_PERMISSION_TASKS = [
    {'name': '配置/boot/grub/grub.conf文件权限', 'command': 'chmod 600 /boot/grub/grub.conf', 'check': 'stat -c %a /boot/grub/grub.conf', 'expected': '600'},
    {'name': '配置/etc/crontab文件权限', 'command': 'chmod 400 /etc/crontab', 'check': 'stat -c %a /etc/crontab', 'expected': '400'},
    {'name': '配置/etc/securetty文件权限', 'command': 'chmod 400 /etc/securetty', 'check': 'stat -c %a /etc/securetty', 'expected': '400'},
    {'name': '配置/etc/hosts.allow文件权限', 'command': 'chmod 644 /etc/hosts.allow', 'check': 'stat -c %a /etc/hosts.allow', 'expected': '644'},
    {'name': '配置/etc/hosts.deny文件权限', 'command': 'chmod 644 /etc/hosts.deny', 'check': 'stat -c %a /etc/hosts.deny', 'expected': '644'},
    {'name': '配置/etc/inittab文件权限', 'command': 'chmod 600 /etc/inittab', 'check': 'stat -c %a /etc/inittab', 'expected': '600'},
    {'name': '配置/etc/login.defs文件权限', 'command': 'chmod 644 /etc/login.defs', 'check': 'stat -c %a /etc/login.defs', 'expected': '644'},
    {'name': '配置/etc/profile文件权限', 'command': 'chmod 644 /etc/profile', 'check': 'stat -c %a /etc/profile', 'expected': '644'},
    {'name': '配置/etc/bashrc文件权限', 'command': 'chmod 644 /etc/bashrc', 'check': 'stat -c %a /etc/bashrc', 'expected': '644'},
    {'name': '配置/etc/passwd文件权限', 'command': 'chmod 644 /etc/passwd', 'check': 'stat -c %a /etc/passwd', 'expected': '644'},
    {'name': '配置/etc/group文件权限', 'command': 'chmod 644 /etc/group', 'check': 'stat -c %a /etc/group', 'expected': '644'},
    {'name': '配置/etc/shadow文件权限', 'command': 'chmod 600 /etc/shadow', 'check': 'stat -c %a /etc/shadow', 'expected': '600'},
    {'name': '配置/etc/init.d/*权限', 'command': 'chmod 700 /etc/init.d/*', 'check': 'stat -c %a /etc/init.d/lsb-core 2>/dev/null || stat -c %a /etc/init.d/README 2>/dev/null || echo "skip"', 'expected': '700'},
]

SSH_HARDENING_TASKS = [
    {
        'name': '检查ssh协议',
        'command': "echo -e '\\n\\nProtocol 2' >> /etc/ssh/sshd_config",
        'check': "grep '^Protocol' /etc/ssh/sshd_config",
        'expected': '2',
        'backup_key': 'SSH_PROTOCOL'
    },
    {
        'name': '记录所有信息，包括info信息',
        'command': "sed -i 's/#LogLevel INFO/LogLevel INFO/g' /etc/ssh/sshd_config",
        'check': "grep '^LogLevel' /etc/ssh/sshd_config",
        'expected': 'INFO',
        'backup_key': 'SSH_LOGLEVEL'
    },
    {
        'name': '最大重试次数',
        'command': "sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/g' /etc/ssh/sshd_config; sed -i 's/^MaxAuthTries [0-9]*/MaxAuthTries 3/g' /etc/ssh/sshd_config",
        'check': "grep '^MaxAuthTries' /etc/ssh/sshd_config",
        'expected': '3',
        'backup_key': 'SSH_MAXAUTH'
    },
    {
        'name': '允许密码验证',
        'command': "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config; sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' /etc/ssh/sshd_config",
        'check': "grep '^PasswordAuthentication' /etc/ssh/sshd_config",
        'expected': 'yes',
        'backup_key': 'SSH_PWD_AUTH'
    },
    {
        'name': '修改ChallengeResponseAuthentication',
        'command': "sed -i 's/ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/g' /etc/ssh/sshd_config",
        'check': "grep '^ChallengeResponseAuthentication' /etc/ssh/sshd_config",
        'expected': 'no',
        'backup_key': 'SSH_CHALLENGE'
    },
    {
        'name': '禁止设置空密码',
        'command': "sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords no/g' /etc/ssh/sshd_config",
        'check': "grep '^PermitEmptyPasswords' /etc/ssh/sshd_config",
        'expected': 'no',
        'backup_key': 'SSH_EMPTY_PWD'
    },
    {
        'name': '禁止对远程主机名进行反向解析',
        'command': "sed -i 's/#UseDNS yes/UseDNS no/g' /etc/ssh/sshd_config; systemctl restart sshd",
        'check': "grep '^UseDNS' /etc/ssh/sshd_config",
        'expected': 'no',
        'backup_key': 'SSH_USEDNS'
    },
    {
        'name': '/etc/passwd注释掉相应的用户',
        'command': "for i in $(egrep 'games|uucp|lp|ftp|news|rpcuser|mail' /etc/passwd | awk -F ':' '{print $1}'); do sed -i \"s/^$i/#&/g\" /etc/passwd; done",
        'check': "egrep 'games|uucp|lp|ftp|news|rpcuser|mail' /etc/passwd | grep -v '^#'",
        'expected': '',
        'allow_empty': True
    },
    {
        'name': '/etc/group文件权限',
        'command': "for i in $(egrep 'lp|mail|news|uucp|games|ftp|floppy|mailnull' /etc/group | awk -F ':' '{print $1}'); do sed -i \"s/^$i/#&/g\" /etc/group; done",
        'check': "egrep 'lp|mail|news|uucp|games|ftp|floppy|mailnull' /etc/group | grep -v '^#'",
        'expected': '',
        'allow_empty': True
    },
    {
        'name': '清空所有ACL规则',
        'command': "setfacl -b /etc/passwd; setfacl -b /etc/group; setfacl -b /etc/shadow",
        'check': "getfacl /etc/passwd | head -1",
        'expected': 'getfacl',
        'allow_empty': True
    },
]

ALL_TASKS = {
    'password': PASSWORD_POLICY_TASKS,
    'system': SYSTEM_SECURITY_TASKS,
    'ssh': SSH_HARDENING_TASKS,
    'permission': FILE_PERMISSION_TASKS,
}
