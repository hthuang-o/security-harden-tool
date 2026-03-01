#!/usr/bin/env python3
"""
Security Hardening Tool - Web API
"""

import os
import json
import yaml
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed

from inventory import Inventory
from ssh_client import SSHClient
from executor import Executor, Checker


app = Flask(__name__, static_folder='static')
CORS(app)

NODES_FILE = 'nodes.yaml'
REPORTS_DIR = 'reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

executor_pool = ThreadPoolExecutor(max_workers=10)
task_results: Dict[str, Any] = {}
task_locks = {}


def create_ssh_client(node: Dict[str, Any], password: Optional[str] = None) -> SSHClient:
    return SSHClient(
        host=node['host'],
        port=node.get('port', 22),
        user=node.get('user', 'root'),
        auth=node.get('auth', 'key'),
        key_path=node.get('key_path', os.path.expanduser('~/.ssh/id_rsa')),
        password=password or node.get('password'),
        passphrase=node.get('passphrase'),
        timeout=30
    )


def load_nodes() -> List[Dict[str, Any]]:
    try:
        inventory = Inventory(NODES_FILE)
        return inventory.load()
    except Exception as e:
        print(f"Error loading nodes: {e}")
        return []


def save_nodes(nodes: List[Dict[str, Any]]) -> bool:
    try:
        with open(NODES_FILE, 'w', encoding='utf-8') as f:
            yaml.dump({'nodes': nodes}, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving nodes: {e}")
        return False


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    nodes = load_nodes()
    for node in nodes:
        node.pop('password', None)
        node.pop('passphrase', None)
    return jsonify({'success': True, 'data': nodes})


@app.route('/api/nodes', methods=['POST'])
def add_node():
    data = request.json
    nodes = load_nodes()
    
    new_node = {
        'host': data.get('host'),
        'port': data.get('port', 22),
        'user': data.get('user', 'root'),
        'auth': data.get('auth', 'key'),
    }
    
    if data.get('auth') == 'password':
        new_node['password'] = data.get('password', '')
    else:
        new_node['key_path'] = data.get('key_path', '~/.ssh/id_rsa')
        new_node['passphrase'] = data.get('passphrase', '')
    
    nodes.append(new_node)
    
    if save_nodes(nodes):
        new_node.pop('password', None)
        new_node.pop('passphrase', None)
        return jsonify({'success': True, 'data': new_node})
    return jsonify({'success': False, 'error': 'Failed to save node'}), 500


@app.route('/api/nodes/<host>', methods=['PUT'])
def update_node(host):
    data = request.json
    nodes = load_nodes()
    
    for i, node in enumerate(nodes):
        if node['host'] == host:
            nodes[i] = {
                'host': data.get('host', host),
                'port': data.get('port', 22),
                'user': data.get('user', 'root'),
                'auth': data.get('auth', 'key'),
            }
            if data.get('auth') == 'password':
                nodes[i]['password'] = data.get('password', '')
            else:
                nodes[i]['key_path'] = data.get('key_path', '~/.ssh/id_rsa')
                nodes[i]['passphrase'] = data.get('passphrase', '')
            break
    
    if save_nodes(nodes):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to update node'}), 500


@app.route('/api/nodes/<host>', methods=['DELETE'])
def delete_node(host):
    nodes = load_nodes()
    nodes = [n for n in nodes if n['host'] != host]
    
    if save_nodes(nodes):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete node'}), 500


@app.route('/api/nodes/<host>/test', methods=['POST'])
def test_node(host):
    data = request.json
    nodes = load_nodes()
    
    node = next((n for n in nodes if n['host'] == host), None)
    if not node:
        node = data
    
    password = data.get('password', node.get('password'))
    
    try:
        ssh = create_ssh_client(node, password)
        if ssh.connect():
            ssh.close()
            return jsonify({'success': True, 'message': 'Connection successful'})
        return jsonify({'success': False, 'message': 'Connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    from tasks import ALL_TASKS
    
    tasks = []
    for category, task_list in ALL_TASKS.items():
        for task in task_list:
            tasks.append({
                'name': task['name'],
                'category': category,
                'has_check': 'check' in task,
                'has_command': 'command' in task,
                'backup_key': task.get('backup_key', '')
            })
    
    categories = [
        {'id': 'password', 'name': '密码策略', 'count': len(ALL_TASKS.get('password', []))},
        {'id': 'system', 'name': '系统安全', 'count': len(ALL_TASKS.get('system', []))},
        {'id': 'ssh', 'name': 'SSH加固', 'count': len(ALL_TASKS.get('ssh', []))},
        {'id': 'permission', 'name': '文件权限', 'count': len(ALL_TASKS.get('permission', []))},
    ]
    
    return jsonify({'success': True, 'data': tasks, 'categories': categories})


def process_node_task(node: Dict[str, Any], mode: str, task: str, password: Optional[str] = None) -> Dict[str, Any]:
    result = {
        'host': node['host'],
        'status': 'failed',
        'tasks': [],
        'error': ''
    }
    
    try:
        ssh = create_ssh_client(node, password)
        if not ssh.connect():
            result['error'] = 'Connection failed'
            return result
        
        if mode == 'check':
            checker = Checker(ssh)
            result['tasks'] = checker.check_category(task)
            result['summary'] = {
                'compliant': sum(1 for r in result['tasks'] if r['status'] == 'compliant'),
                'non_compliant': sum(1 for r in result['tasks'] if r['status'] == 'non_compliant')
            }
            result['status'] = 'completed'
        else:
            executor = Executor(ssh)
            result['tasks'] = executor.execute_category(task)
            result['rollback_data'] = executor.get_rollback_summary()
            result['status'] = 'completed'
        
        ssh.close()
    except Exception as e:
        result['error'] = str(e)
    
    return result


@app.route('/api/execute', methods=['POST'])
def execute_task():
    data = request.json
    mode = data.get('mode', 'check')
    task = data.get('task', 'all')
    hosts = data.get('hosts', [])
    passwords = data.get('passwords', {})
    
    nodes = load_nodes()
    if hosts:
        nodes = [n for n in nodes if n['host'] in hosts]
    
    if not nodes:
        return jsonify({'success': False, 'error': 'No nodes selected'}), 400
    
    task_id = f"task_{int(threading.current_thread().ident or 0)}_{len(task_results)}"
    task_results[task_id] = {
        'id': task_id,
        'mode': mode,
        'task': task,
        'status': 'running',
        'total': len(nodes),
        'completed': 0,
        'results': [],
        'start_time': str(Path(__file__).stat().st_mtime)
    }
    
    def run_tasks():
        results = []
        for node in nodes:
            password = passwords.get(node['host'])
            result = process_node_task(node, mode, task, password)
            results.append(result)
            task_results[task_id]['completed'] += 1
            task_results[task_id]['results'] = results
        
        task_results[task_id]['status'] = 'completed'
        
        output_file = os.path.join(REPORTS_DIR, f'{task_id}.json')
        output_data = {
            'mode': mode,
            'task': task,
            'results': results,
            'timestamp': str(Path(__file__).stat().st_mtime)
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    executor_pool.submit(run_tasks)
    
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id in task_results:
        return jsonify({'success': True, 'data': task_results[task_id]})
    return jsonify({'success': False, 'error': 'Task not found'}), 404


@app.route('/api/reports', methods=['GET'])
def get_reports():
    reports = []
    for f in os.listdir(REPORTS_DIR):
        if f.endswith('.json'):
            filepath = os.path.join(REPORTS_DIR, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    results = data.get('results', [])
                    compliant = 0
                    non_compliant = 0
                    success = 0
                    failed = 0
                    
                    for r in results:
                        for t in r.get('tasks', []):
                            if t.get('status') == 'compliant':
                                compliant += 1
                            elif t.get('status') == 'non_compliant':
                                non_compliant += 1
                            elif t.get('status') == 'success':
                                success += 1
                            elif t.get('status') == 'failed':
                                failed += 1
                    
                    reports.append({
                        'id': f.replace('.json', ''),
                        'mode': data.get('mode'),
                        'task': data.get('task'),
                        'timestamp': data.get('timestamp', ''),
                        'nodes_count': len(results),
                        'compliant': compliant,
                        'non_compliant': non_compliant,
                        'success': success,
                        'failed': failed
                    })
            except Exception as e:
                print(f"Error reading report {f}: {e}")
    
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify({'success': True, 'data': reports})


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    filepath = os.path.join(REPORTS_DIR, f'{report_id}.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'success': True, 'data': data})
    return jsonify({'success': False, 'error': 'Report not found'}), 404


@app.route('/api/rollback', methods=['POST'])
def rollback_task():
    data = request.json
    host = data.get('host')
    task_name = data.get('task_name')
    original_value = data.get('original_value', '')
    
    nodes = load_nodes()
    node = next((n for n in nodes if n['host'] == host), None)
    
    if not node:
        return jsonify({'success': False, 'error': 'Node not found'}), 404
    
    password = data.get('password', node.get('password'))
    
    try:
        ssh = create_ssh_client(node, password)
        if not ssh.connect():
            return jsonify({'success': False, 'message': 'Connection failed'})
        
        executor = Executor(ssh)
        success = executor.rollback_task(task_name, original_value)
        ssh.close()
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
