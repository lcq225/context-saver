"""
操作跟踪器 - 跟踪关键操作并记录到日志

集成到文件操作、命令执行等技能中
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# ==================== 配置 ====================

WORKSPACE_DIR = Path(r"D:\CoPaw\.copaw\workspaces\default")
OPERATION_LOG_PATH = WORKSPACE_DIR / "operation_log.jsonl"

# 操作类型
OP_CONFIG_CHANGE = "config_change"
OP_TASK_UPDATE = "task_update"
OP_DECISION = "decision"
OP_ERROR = "error"
OP_FILE_WRITE = "file_write"
OP_EXTERNAL = "external"

# ==================== 核心功能 ====================

def track_operation(op_type, summary, details=None, extra=None):
    """
    跟踪关键操作
    
    Args:
        op_type: 操作类型
                 - config_change: 配置修改
                 - task_update: 任务状态更新
                 - decision: 重要决策
                 - error: 错误/教训
                 - file_write: 文件创建/修改
                 - external: 外部交互
        summary: 操作摘要（简短描述，一行）
        details: 详细信息（可选）
        extra: 额外数据（字典，可选）
    
    Returns:
        操作 ID（时间戳）
    """
    # 确保目录存在
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    
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
    
    # 如果是关键操作，触发立即保存
    if op_type in [OP_CONFIG_CHANGE, OP_DECISION]:
        from auto_context_flush import flush_context
        flush_context(reason="critical_change", custom_data=summary)
    
    return operation["timestamp"]

# ==================== 便捷函数 ====================

def on_config_change(config_path, change_summary):
    """配置修改后调用"""
    return track_operation(
        OP_CONFIG_CHANGE,
        summary=f"配置修改：{config_path}",
        details=change_summary,
        extra={"path": str(config_path)}
    )

def on_task_update(task_summary, status="in_progress"):
    """任务状态更新时调用"""
    return track_operation(
        OP_TASK_UPDATE,
        summary=f"任务更新：{task_summary}",
        details=f"状态：{status}",
        extra={"status": status}
    )

def on_decision(decision_summary, rationale=None):
    """重要决策后调用"""
    return track_operation(
        OP_DECISION,
        summary=decision_summary,
        details=rationale or "",
        extra={"type": "decision"}
    )

def on_error(error_summary, root_cause=None, solution=None):
    """错误解决后调用"""
    details = []
    if root_cause:
        details.append(f"根因：{root_cause}")
    if solution:
        details.append(f"解决方案：{solution}")
    
    return track_operation(
        OP_ERROR,
        summary=error_summary,
        details="\n".join(details),
        extra={"type": "error"}
    )

def on_file_write(file_path, file_type=None):
    """文件写入后调用"""
    extra = {"path": str(file_path)}
    if file_type:
        extra["file_type"] = file_type
    
    return track_operation(
        OP_FILE_WRITE,
        summary=f"文件保存：{Path(file_path).name}",
        details=f"路径：{file_path}",
        extra=extra
    )

def on_external_interaction(service, action, result=None):
    """外部交互后调用"""
    return track_operation(
        OP_EXTERNAL,
        summary=f"外部交互：{service} - {action}",
        details=result or "",
        extra={"service": service, "action": action}
    )

# ==================== 包装器（用于技能集成） ====================

class TrackedFileWriter:
    """
    带跟踪的文件写入器
    
    使用示例：
    writer = TrackedFileWriter()
    writer.write("test.md", "content")  # 自动记录操作
    """
    
    def __init__(self, auto_track=True):
        self.auto_track = auto_track
    
    def write(self, file_path, content, file_type=None):
        """写入文件并跟踪"""
        from write_file_tool import write_file  # 假设这是实际的写入工具
        
        # 执行写入
        result = write_file(file_path, content)
        
        # 跟踪操作
        if self.auto_track:
            on_file_write(file_path, file_type)
        
        return result

# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="操作跟踪工具")
    parser.add_argument("--type", required=True, help="操作类型")
    parser.add_argument("--summary", required=True, help="操作摘要")
    parser.add_argument("--details", default="", help="详细信息")
    parser.add_argument("--list", action="store_true", help="列出最近操作")
    parser.add_argument("--clear", action="store_true", help="清空日志")
    
    args = parser.parse_args()
    
    if args.list:
        if not OPERATION_LOG_PATH.exists():
            print("操作日志为空")
            return
        
        print("📋 最近操作:\n")
        with open(OPERATION_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-10:]  # 最近 10 条
        
        for line in reversed(lines):
            try:
                op = json.loads(line)
                print(f"[{op['timestamp'][:19]}] {op['type']}: {op['summary']}")
            except:
                pass
        return
    
    if args.clear:
        if OPERATION_LOG_PATH.exists():
            OPERATION_LOG_PATH.unlink()
            print("✅ 操作日志已清空")
        return
    
    # 记录操作
    op_id = track_operation(args.type, args.summary, args.details)
    print(f"✅ 操作已记录：{op_id}")

if __name__ == "__main__":
    main()
