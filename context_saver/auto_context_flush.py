"""
会话上下文自动保存 - 支持增量保存和版本管理

触发时机：
1. 会话结束前
2. 压缩触发前（安全网）
3. 手动调用（copaw flush）
4. 关键操作后（配置修改、重要决策）
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import sqlite3

# ==================== 配置 ====================

WORKSPACE_DIR = Path(r"D:\CoPaw\.copaw\workspaces\default")
CONTEXT_FLUSH_DIR = WORKSPACE_DIR / "context_flush_history"
CONTEXT_FLUSH_LATEST = WORKSPACE_DIR / "context_flush.md"
CURRENT_TASK_PATH = WORKSPACE_DIR / "CURRENT_TASK.md"
OPERATION_LOG_PATH = WORKSPACE_DIR / "operation_log.jsonl"
MEMORY_DB_PATH = Path(r"D:\CoPaw\.copaw\.agent-memory\memory.db")
DIALOG_DIR = WORKSPACE_DIR / "dialog"
ARCHIVE_DIR = WORKSPACE_DIR / "archive"

# 保留最近 N 次会话快照
MAX_SESSION_SNAPSHOTS = 30

# ==================== 工具函数 ====================

def ensure_dirs():
    """确保目录存在"""
    CONTEXT_FLUSH_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def get_session_id():
    """生成会话 ID（时间戳 + 随机数）"""
    import random
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    random_id = random.randint(1000, 9999)
    return f"{timestamp}_{random_id}"

def get_recent_dialogs(limit=3):
    """获取最近的对话文件"""
    if not DIALOG_DIR.exists():
        return []
    
    files = sorted(DIALOG_DIR.glob("*.jsonl"), reverse=True)[:limit]
    return files

def get_memory_stats():
    """获取记忆系统统计"""
    if not MEMORY_DB_PATH.exists():
        return "数据库不存在"
    
    try:
        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        for table_name in ["memory_entries", "memories", "entries"]:
            if table_name in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                conn.close()
                return f"共 {count} 条记忆"
        
        conn.close()
        return f"表结构未知（{len(tables)} 个表）"
    except Exception as e:
        return f"查询失败：{e}"

def read_operation_log(limit=50):
    """读取操作日志"""
    if not OPERATION_LOG_PATH.exists():
        return []
    
    operations = []
    with open(OPERATION_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                operations.append(json.loads(line))
            except:
                pass
    
    return operations[-limit:]

def cleanup_old_snapshots():
    """清理旧的会话快照（保留最近 N 次）"""
    if not CONTEXT_FLUSH_DIR.exists():
        return
    
    files = sorted(CONTEXT_FLUSH_DIR.glob("*_session.md"), reverse=True)
    
    for old_file in files[MAX_SESSION_SNAPSHOTS:]:
        try:
            old_file.unlink()
            print(f"🗑️  清理旧快照：{old_file.name}")
        except Exception as e:
            print(f"⚠️  清理失败：{old_file.name} - {e}")

# ==================== 核心功能 ====================

def flush_context(reason="session_end", session_id=None, custom_data=None):
    """
    保存会话上下文
    
    Args:
        reason: 触发原因 (session_end|before_compress|manual|critical_change)
        session_id: 会话 ID（自动生成或使用传入的）
        custom_data: 自定义数据（用于补充关键信息）
    
    Returns:
        保存的文件路径
    """
    ensure_dirs()
    
    if not session_id:
        session_id = get_session_id()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"🔄 保存会话上下文...")
    print(f"   会话 ID: {session_id}")
    print(f"   触发原因：{reason}")
    
    # 1. 读取 CURRENT_TASK.md（任务状态）
    current_task_content = ""
    if CURRENT_TASK_PATH.exists():
        with open(CURRENT_TASK_PATH, "r", encoding="utf-8") as f:
            current_task_content = f.read()
    
    # 2. 读取操作日志
    operations = read_operation_log()
    
    # 3. 提取关键信息
    decisions = [op for op in operations if op.get("type") == "decision"]
    errors = [op for op in operations if op.get("type") == "error"]
    file_changes = [op for op in operations if op.get("type") == "file_write"]
    
    # 4. 生成会话快照内容
    content = f"""# 📋 会话上下文快照

> 会话 ID: {session_id}
> 保存时间：{timestamp}
> 触发原因：{reason}

---

## ⏳ 进行中的任务

{current_task_content if current_task_content else "无进行中任务"}

---

## 🎯 关键决策

{chr(10).join([f"- **{d.get('timestamp', 'N/A')}**: {d.get('summary', 'N/A')}" for d in decisions[-5:]]) if decisions else "无关键决策"}

---

## ⚠️ 错误与教训

{chr(10).join([f"- **{e.get('timestamp', 'N/A')}**: {e.get('summary', 'N/A')}" for e in errors[-5:]]) if errors else "无错误记录"}

---

## 📝 文件变更

{chr(10).join([f"- `{f.get('path', 'N/A')}` ({f.get('size', 0)} bytes)" for f in file_changes[-10:]]) if file_changes else "无文件变更"}

---

## 📊 系统状态

- 记忆统计：{get_memory_stats()}
- 操作日志：{len(operations)} 条
- 会话原因：{reason}

---

## 🔐 敏感信息

无新增敏感信息

---

## 📂 重要文件位置

| 文件 | 路径 |
|------|------|
| CURRENT_TASK.md | {CURRENT_TASK_PATH} |
| context_flush.md | {CONTEXT_FLUSH_LATEST} |
| 会话快照目录 | {CONTEXT_FLUSH_DIR} |

---

## 💡 备注

{custom_data if custom_data else "无"}

---

*此文件由 auto_context_flush.py 自动生成*
*会话快照保留最近 {MAX_SESSION_SNAPSHOTS} 次*
"""
    
    # 5. 保存到历史目录（增量）
    snapshot_path = CONTEXT_FLUSH_DIR / f"{session_id}_session.md"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 会话快照：{snapshot_path.name}")
    
    # 6. 更新 context_flush.md（快捷访问 - 指向最新）
    latest_content = f"""# 📋 最近会话上下文

> 最新会话：{session_id}
> 更新时间：{timestamp}
> 完整快照：`context_flush_history/{session_id}_session.md`

---

## 📥 快速访问

- **进行中任务**：[CURRENT_TASK.md](CURRENT_TASK.md)
- **会话历史**：[context_flush_history/](context_flush_history/)
- **归档目录**：[archive/](archive/)

---

## 🕐 最近会话

"""
    
    # 列出最近 5 次会话
    recent_sessions = sorted(CONTEXT_FLUSH_DIR.glob("*_session.md"), reverse=True)[:5]
    for session_file in recent_sessions:
        latest_content += f"- [{session_file.stem}]({session_file.name})\n"
    
    latest_content += f"\n---\n*由 auto_context_flush.py 自动生成*\n"
    
    with open(CONTEXT_FLUSH_LATEST, "w", encoding="utf-8") as f:
        f.write(latest_content)
    
    print(f"✅ 快捷访问：{CONTEXT_FLUSH_LATEST.name}")
    
    # 7. 清理旧快照
    cleanup_old_snapshots()
    
    # 8. 清空操作日志（避免重复）
    if reason == "session_end":
        if OPERATION_LOG_PATH.exists():
            OPERATION_LOG_PATH.unlink()
        print(f"🗑️  已清空操作日志")
    
    return str(snapshot_path)

# ==================== 操作跟踪 ====================

def track_operation(op_type, summary, details=None, extra=None):
    """
    跟踪关键操作
    
    Args:
        op_type: 操作类型 (config_change|task_update|decision|error|file_write)
        summary: 操作摘要（简短描述）
        details: 详细信息
        extra: 额外数据（字典）
    """
    ensure_dirs()
    
    operation = {
        "timestamp": datetime.now().isoformat(),
        "type": op_type,
        "summary": summary,
        "details": details or "",
        "extra": extra or {}
    }
    
    # 追加到操作日志
    with open(OPERATION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(operation, ensure_ascii=False) + "\n")
    
    # 如果是关键操作，立即触发保存
    if op_type in ["config_change", "decision"]:
        flush_context(reason="critical_change", custom_data=summary)

# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="会话上下文保存工具")
    parser.add_argument("--reason", default="manual", help="触发原因")
    parser.add_argument("--session-id", help="会话 ID（可选）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示，不保存")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 干运行模式 - 不会实际保存")
        print(f"   触发原因：{args.reason}")
        print(f"   会话 ID: {args.session_id or '自动生成'}")
        print(f"   保存位置：{CONTEXT_FLUSH_DIR}")
        return
    
    flush_context(reason=args.reason, session_id=args.session_id)

if __name__ == "__main__":
    main()
