#!/usr/bin/env python3
"""
Security Hardening Tool
批量对多个节点完成安全配置并检查
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from inventory import Inventory
from ssh_client import SSHClient
from executor import Executor, Checker


def create_ssh_client(node: Dict[str, Any], args) -> SSHClient:
    return SSHClient(
        host=node['host'],
        port=node.get('port', 22),
        user=node.get('user', 'root'),
        auth=node.get('auth', 'key'),
        key_path=node.get('key_path', os.path.expanduser('~/.ssh/id_rsa')),
        password=args.password or node.get('password'),
        passphrase=args.passphrase or node.get('passphrase'),
        timeout=args.timeout
    )


def process_node(node: Dict[str, Any], args) -> Dict[str, Any]:
    result = {
        'host': node['host'],
        'status': 'failed',
        'tasks': [],
        'error': ''
    }
    
    # Load rollback data from output file if available
    rollback_data = {}
    if args.output and os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
                for r in output_data.get('results', []):
                    if r.get('host') == node['host']:
                        for rb in r.get('rollback_data', []):
                            rollback_data[rb['backup_key']] = rb['original_value']
        except:
            pass
    
    ssh = create_ssh_client(node, args)
    
    if not ssh.connect():
        result['error'] = 'Connection failed'
        return result
    
    try:
        if args.mode == 'check':
            checker = Checker(ssh)
            result['tasks'] = checker.check_category(args.task)
            result['summary'] = {
                'compliant': sum(1 for r in result['tasks'] if r['status'] == 'compliant'),
                'non_compliant': sum(1 for r in result['tasks'] if r['status'] == 'non_compliant')
            }
            result['status'] = 'completed'
            
        elif args.mode == 'exec':
            executor = Executor(ssh)
            result['tasks'] = executor.execute_category(args.task)
            result['rollback_data'] = executor.get_rollback_summary()
            result['status'] = 'completed'
            result['rollback_data'] = executor.get_rollback_summary()
            result['status'] = 'completed'
            
        elif args.mode == 'check_only':
            checker = Checker(ssh)
            result['tasks'] = checker.check_category(args.task)
            result['summary'] = {
                'compliant': sum(1 for r in result['tasks'] if r['status'] == 'compliant'),
                'non_compliant': sum(1 for r in result['tasks'] if r['status'] == 'non_compliant')
            }
            result['status'] = 'completed'
            
        elif args.mode == 'rollback':
            executor = Executor(ssh)
            # Load rollback data from previous execution
            if rollback_data:
                executor.rollback_data = rollback_data
            # Override with command line value if provided
            if args.original_value:
                executor.rollback_data = {args.task_name: args.original_value}
            if args.task_name:
                success = executor.rollback_task(args.task_name, args.original_value or "")
                result['tasks'] = [{'task': args.task_name, 'rolled_back': success}]
            result['status'] = 'completed'
            
    except Exception as e:
        result['error'] = str(e)
    finally:
        ssh.close()
    
    return result


def print_results(results: List[Dict[str, Any]], args):
    for result in results:
        print(f"\n{'='*60}")
        print(f"Host: {result['host']}")
        print(f"Status: {result['status']}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
            continue
            
        if args.mode in ['check', 'check_only']:
            if 'summary' in result:
                print(f"Compliance: {result['summary']['compliant']}/{len(result['tasks'])} passed")
            for task in result.get('tasks', []):
                status_icon = '✓' if task['status'] == 'compliant' else '✗'
                print(f"  {status_icon} {task['task_name']}: {task['message']}")
                
        elif args.mode == 'exec':
            success = sum(1 for t in result.get('tasks', []) if t['status'] == 'success')
            print(f"Success: {success}/{len(result.get('tasks', []))}")
            for task in result.get('tasks', []):
                status_icon = '✓' if task['status'] == 'success' else '✗'
                print(f"  {status_icon} {task['task_name']}")
            
            if result.get('rollback_data'):
                print("\nRollback available for:")
                for rb in result['rollback_data']:
                    print(f"  - {rb['task_name']}: {rb['original_value']}")
                    
        elif args.mode == 'rollback':
            for task in result.get('tasks', []):
                print(f"  Rollback: {task.get('task')}: {'Success' if task.get('rolled_back') else 'Failed'}")


def main():
    parser = argparse.ArgumentParser(
        description='Security Hardening Tool - 批量服务器安全加固',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 检查节点配置
  python main.py -n nodes.yaml --check
  
  # 执行所有安全加固
  python main.py -n nodes.yaml --exec
  
  # 仅执行密码策略
  python main.py -n nodes.yaml -t password --exec
  
  # 回滚特定任务
  python main.py -n nodes.yaml --rollback --task-name "检查密码最长使用天数"
  
  # 使用密码认证
  python main.py -n nodes.yaml -u admin -p 'password' --exec
        """
    )
    
    parser.add_argument('-n', '--nodes', required=True, help='节点配置文件路径 (YAML)')
    parser.add_argument('-t', '--task', default='all', 
                       choices=['all', 'password', 'system', 'ssh', 'permission'],
                       help='任务类别 (default: all)')
    
    # Mode
    parser.add_argument('--check', action='store_true', help='检查当前配置状态')
    parser.add_argument('--check-only', action='store_true', help='仅检查不执行')
    parser.add_argument('--exec', action='store_true', help='执行安全加固')
    parser.add_argument('--rollback', action='store_true', help='回滚任务')
    
    # SSH Auth
    parser.add_argument('-u', '--user', default='root', help='SSH用户名')
    parser.add_argument('-p', '--password', help='SSH密码')
    parser.add_argument('-k', '--key', dest='key_path', help='SSH私钥路径')
    parser.add_argument('--passphrase', help='SSH私钥 passphrase')
    
    # Options
    parser.add_argument('--task-name', help='回滚时指定任务名称')
    parser.add_argument('--original-value', help='回滚时指定原始值')
    parser.add_argument('--timeout', type=int, default=30, help='SSH连接超时时间')
    parser.add_argument('-j', '--jobs', type=int, default=5, help='并发数')
    parser.add_argument('-o', '--output', help='输出报告文件路径 (JSON)')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.check:
        args.mode = 'check'
    elif args.check_only:
        args.mode = 'check_only'
    elif args.rollback:
        args.mode = 'rollback'
    else:
        args.mode = 'exec'
    
    # Load inventory
    try:
        inventory = Inventory(args.nodes)
        nodes = inventory.load()
    except Exception as e:
        print(f"Error loading inventory: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(nodes)} nodes")
    print(f"Mode: {args.mode}, Task: {args.task}")
    
    # Process nodes
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(process_node, node, args): node for node in nodes}
        
        for future in as_completed(futures):
            node = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    'host': node['host'],
                    'status': 'failed',
                    'error': str(e)
                })
    
    # Print results
    print_results(results, args)
    
    # Save output
    if args.output:
        output_data = {
            'mode': args.mode,
            'task': args.task,
            'results': results
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")
    
    # Summary
    failed = sum(1 for r in results if r['status'] == 'failed')
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
