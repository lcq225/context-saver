#!/usr/bin/env python3
"""
脱敏检查脚本 - 自动扫描敏感信息
用法：python sanitize_check.py <目录路径>
"""

import os
import re
import sys
from pathlib import Path

# 敏感信息模式
SENSITIVE_PATTERNS = [
    (r'海科', '公司名'),
    (r'山东海科化工集团', '公司全名'),
    (r'@hkchem\.com', '企业邮箱'),
    (r'192\.168\.\d+\.\d+', '内网 IP'),
    (r'10\.\d+\.\d+\.\d+', '内网 IP'),
    (r'卓越与智能部', '部门名称'),
    (r'sk-[a-zA-Z0-9]{20,}', 'API Key'),
]

def scan_file(file_path):
    """扫描单个文件"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern, issue_type in SENSITIVE_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues.append({
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'type': issue_type,
                        'match': match.group()
                    })
    except Exception as e:
        print(f"⚠️ 跳过文件 {file_path}: {e}")
    return issues

def scan_directory(dir_path):
    """扫描目录"""
    all_issues = []
    skip_dirs = ['.git', '__pycache__', '.pytest_cache', 'node_modules', 'dist', 'build']
    skip_files = ['sanitize_check.py']  # 跳过自身
    
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file in skip_files:
                continue
            if file.endswith(('.py', '.md', '.txt', '.yaml', '.yml', '.json')):
                file_path = Path(root) / file
                issues = scan_file(file_path)
                all_issues.extend(issues)
    
    return all_issues

def main():
    if len(sys.argv) < 2:
        print("用法：python sanitize_check.py <目录路径>")
        sys.exit(1)
    
    dir_path = sys.argv[1]
    print(f"🔍 扫描目录：{dir_path}")
    print("=" * 60)
    
    issues = scan_directory(dir_path)
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个敏感信息:")
        for issue in issues:
            print(f"  📍 {issue['file']}:{issue['line']} [{issue['type']}] {issue['match']}")
        print("\n❌ 脱敏检查失败！")
        sys.exit(1)
    else:
        print("\n✅ 未发现敏感信息，脱敏通过！")
        sys.exit(0)

if __name__ == '__main__':
    main()
