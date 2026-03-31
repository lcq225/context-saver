"""
Basic Usage Example | 基础使用示例

This example demonstrates the basic usage of Context Saver.
此示例演示 Context Saver 的基础用法。
"""

from context_saver import AutoContextFlush, OperationTracker, CompressionGuard

# Example 1: Auto Context Flush | 示例 1：自动上下文刷新
print("=" * 60)
print("Example 1: Auto Context Flush | 示例 1：自动上下文刷新")
print("=" * 60)

flusher = AutoContextFlush(
    save_dir="./context_flush_history",
    max_snapshots=30
)

# Manual save | 手动保存
flusher.save_session(
    session_id="example_001",
    todos=["Task 1", "Task 2"],
    decisions=["Decision 1"],
    recent_requests=["Request 1"]
)
print("✓ Session saved | 会话已保存")

# Example 2: Operation Tracker | 示例 2：操作跟踪
print("\n" + "=" * 60)
print("Example 2: Operation Tracker | 示例 2：操作跟踪")
print("=" * 60)

tracker = OperationTracker(log_file="./operation_log.jsonl")

# Track different operation types | 跟踪不同类型的操作
tracker.track(
    op_type="config_change",
    description="Updated memory threshold",
    details={"old": 100, "new": 200}
)
print("✓ Config change tracked | 配置变更已跟踪")

tracker.track(
    op_type="file_write",
    description="Created new document",
    details={"file": "report.md", "size": 1024}
)
print("✓ File operation tracked | 文件操作已跟踪")

tracker.track(
    op_type="decision",
    description="Adopted three-tier architecture",
    details={"alternatives": ["two-tier", "four-tier"]}
)
print("✓ Decision tracked | 决策已跟踪")

# Example 3: Compression Guard | 示例 3：压缩保护
print("\n" + "=" * 60)
print("Example 3: Compression Guard | 示例 3：压缩保护")
print("=" * 60)

guard = CompressionGuard(
    context_file="./context_flush.md",
    threshold_minutes=30
)

# Check if save is needed | 检查是否需要保存
if guard.should_save():
    print("⚠ Context file is stale, forcing save...")
    print("⚠ 上下文文件过期，强制保存中...")
    guard.force_save(flusher)
    print("✓ Save complete, safe to compress")
    print("✓ 保存完成，可以安全压缩")
else:
    print("✓ Context file is fresh, compression safe")
    print("✓ 上下文文件新鲜，压缩安全")

print("\n" + "=" * 60)
print("All examples completed successfully!")
print("所有示例执行成功！")
print("=" * 60)
