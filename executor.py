from typing import Dict, Any, List, Tuple
from ssh_client import SSHClient
from tasks import ALL_TASKS
import json
from datetime import datetime


class Executor:
    def __init__(self, ssh_client: SSHClient):
        self.ssh = ssh_client
        self.results: List[Dict[str, Any]] = []
        self.rollback_data: Dict[str, Any] = {}
        
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'task_name': task['name'],
            'command': task['command'],
            'status': 'pending',
            'output': '',
            'error': '',
            'rollback_available': False
        }
        
        # 执行前检查当前状态（备份）
        if 'check' in task and 'backup_key' in task:
            exit_code, output, _ = self.ssh.execute(task['check'])
            if exit_code == 0 and output.strip():
                self.rollback_data[task['backup_key']] = output.strip()
                result['original_value'] = output.strip()
                result['backup_key'] = task['backup_key']
        
        # 执行命令
        exit_code, stdout, stderr = self.ssh.execute(task['command'])
        result['exit_code'] = exit_code
        result['output'] = stdout
        result['error'] = stderr
        
        if exit_code == 0:
            # 验证结果
            if 'check' in task and 'expected' in task:
                verify_code, verify_out, _ = self.ssh.execute(task['check'])
                
                if task.get('allow_empty'):
                    result['status'] = 'success'
                elif task['expected'] in verify_out:
                    result['status'] = 'success'
                    result['rollback_available'] = 'backup_key' in task
                else:
                    result['status'] = 'warning'
                    result['verify_output'] = verify_out
            else:
                result['status'] = 'success'
        else:
            result['status'] = 'failed'
            
        self.results.append(result)
        return result
    
    def execute_category(self, category: str) -> List[Dict[str, Any]]:
        if category == 'all':
            categories = ['password', 'system', 'ssh', 'permission']
        else:
            categories = [category]
            
        all_results = []
        for cat in categories:
            tasks = ALL_TASKS.get(cat, [])
            for task in tasks:
                print(f"  Executing: {task['name']}")
                result = self.execute_task(task)
                all_results.append(result)
                
        return all_results
    
    def rollback_task(self, task_name: str, original_value: str = "") -> bool:
        backup_key = None
        for task in sum(ALL_TASKS.values(), []):
            if task['name'] == task_name:
                backup_key = task.get('backup_key')
                break
        
        if not backup_key:
            print(f"  [ERROR] Task not found: {task_name}")
            return False
        
        # Use provided original_value or try to get from saved results
        if not original_value:
            original_value = self.rollback_data.get(backup_key, '')
        
        if not original_value:
            # Try to get current value from server
            for task in sum(ALL_TASKS.values(), []):
                if task['name'] == task_name and 'check' in task:
                    exit_code, output, _ = self.ssh.execute(task['check'])
                    if exit_code == 0:
                        original_value = output.strip()
                    break
        
        if backup_key:
            return self.ssh.rollback(backup_key, original_value)
        return False
    
    def get_rollback_summary(self) -> List[Dict[str, Any]]:
        rollback_summary = []
        for result in self.results:
            if result.get('rollback_available') and result.get('original_value'):
                rollback_summary.append({
                    'task_name': result['task_name'],
                    'original_value': result['original_value'],
                    'backup_key': result.get('backup_key', '')
                })
        return rollback_summary
    
    def save_results(self, filepath: str):
        output = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'rollback_available': self.get_rollback_summary()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)


class Checker:
    def __init__(self, ssh_client: SSHClient):
        self.ssh = ssh_client
        self.check_results: List[Dict[str, Any]] = []
        
    def check_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'task_name': task['name'],
            'status': 'unknown',
            'current_value': '',
            'expected': task.get('expected', ''),
            'message': ''
        }
        
        if 'check' not in task:
            result['message'] = 'No check command defined'
            self.check_results.append(result)
            return result
            
        exit_code, output, stderr = self.ssh.execute(task['check'])
        result['current_value'] = output.strip()
        
        if task.get('allow_empty'):
            if not output.strip():
                result['status'] = 'compliant'
                result['message'] = 'No issues found (empty as expected)'
            else:
                result['status'] = 'non_compliant'
                result['message'] = f'Found: {output.strip()}'
        elif task['expected'] in output:
            result['status'] = 'compliant'
            result['message'] = 'Configuration is correct'
        else:
            result['status'] = 'non_compliant'
            result['message'] = f'Expected: {task["expected"]}, Found: {output.strip()}'
            
        self.check_results.append(result)
        return result
    
    def check_category(self, category: str) -> List[Dict[str, Any]]:
        if category == 'all':
            categories = ['password', 'system', 'ssh', 'permission']
        else:
            categories = [category]
            
        all_results = []
        for cat in categories:
            tasks = ALL_TASKS.get(cat, [])
            for task in tasks:
                print(f"  Checking: {task['name']}")
                result = self.check_task(task)
                all_results.append(result)
                
        return all_results
    
    def save_check_results(self, filepath: str):
        compliant = sum(1 for r in self.check_results if r['status'] == 'compliant')
        non_compliant = sum(1 for r in self.check_results if r['status'] == 'non_compliant')
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(self.check_results),
                'compliant': compliant,
                'non_compliant': non_compliant,
                'compliance_rate': f"{compliant / len(self.check_results) * 100:.1f}%" if self.check_results else "N/A"
            },
            'results': self.check_results
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
