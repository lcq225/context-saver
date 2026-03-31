"""
Integration Example | 集成示例

This example shows how to integrate Context Saver into your AI agent project.
此示例展示如何将 Context Saver 集成到你的 AI Agent 项目中。
"""

from context_saver import AutoContextFlush, OperationTracker, CompressionGuard
import json
from datetime import datetime

class MyAIAgent:
    """
    Example AI Agent with Context Saver integration
    集成 Context Saver 的 AI Agent 示例
    """
    
    def __init__(self):
        # Initialize context saver components
        # 初始化上下文保存组件
        self.context_flusher = AutoContextFlush(
            save_dir="./agent_context_history",
            max_snapshots=30
        )
        
        self.operation_tracker = OperationTracker(
            log_file="./agent_operations.jsonl"
        )
        
        self.compression_guard = CompressionGuard(
            context_file="./agent_context.md",
            threshold_minutes=30
        )
        
        self.current_task = None
        self.todos = []
        
    def start_task(self, task_name):
        """Start a new task | 开始新任务"""
        self.current_task = task_name
        self.todos.append(task_name)
        
        # Track operation | 跟踪操作
        self.operation_tracker.track(
            op_type="task_start",
            description=f"Started task: {task_name}",
            details={"task": task_name, "time": datetime.now().isoformat()}
        )
        
        # Auto-save context | 自动保存上下文
        self._save_context()
        
        print(f"✓ Task started: {task_name}")
        print(f"✓ 任务已启动：{task_name}")
        
    def complete_task(self, task_name):
        """Complete a task | 完成任务"""
        if task_name in self.todos:
            self.todos.remove(task_name)
            
            # Track operation | 跟踪操作
            self.operation_tracker.track(
                op_type="task_complete",
                description=f"Completed task: {task_name}",
                details={"task": task_name, "time": datetime.now().isoformat()}
            )
            
            # Auto-save context | 自动保存上下文
            self._save_context()
            
            print(f"✓ Task completed: {task_name}")
            print(f"✓ 任务已完成：{task_name}")
    
    def make_decision(self, decision, alternatives=None):
        """Make a decision | 做出决策"""
        # Track decision | 跟踪决策
        self.operation_tracker.track(
            op_type="decision",
            description=f"Decision: {decision}",
            details={
                "decision": decision,
                "alternatives": alternatives,
                "time": datetime.now().isoformat()
            }
        )
        
        # Auto-save context | 自动保存上下文
        self._save_context()
        
        print(f"✓ Decision recorded: {decision}")
        print(f"✓ 决策已记录：{decision}")
    
    def handle_error(self, error_message, error_type="unknown"):
        """Handle an error | 处理错误"""
        # Track error | 跟踪错误
        self.operation_tracker.track(
            op_type="error",
            description=f"Error: {error_message}",
            details={
                "error_type": error_type,
                "message": error_message,
                "time": datetime.now().isoformat()
            }
        )
        
        # Auto-save context | 自动保存上下文
        self._save_context()
        
        print(f"✓ Error logged: {error_message}")
        print(f"✓ 错误已记录：{error_message}")
    
    def compress_context(self):
        """
        Compress context (with protection)
        压缩上下文（带保护）
        """
        # Check if save is needed before compression
        # 压缩前检查是否需要保存
        if self.compression_guard.should_save():
            print("⚠ Context stale, saving before compression...")
            print("⚠ 上下文过期，压缩前保存中...")
            self.compression_guard.force_save(self.context_flusher)
            print("✓ Save complete")
            print("✓ 保存完成")
        
        # Now safe to compress
        # 现在可以安全压缩
        print("✓ Compression safe to proceed")
        print("✓ 可以安全执行压缩")
    
    def _save_context(self):
        """Internal method to save context | 内部保存上下文方法"""
        self.context_flusher.save_session(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            todos=self.todos,
            decisions=[],
            recent_requests=[self.current_task] if self.current_task else []
        )

# Example usage | 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("AI Agent Integration Example")
    print("AI Agent 集成示例")
    print("=" * 60)
    
    # Create agent instance | 创建 Agent 实例
    agent = MyAIAgent()
    
    # Start a task | 启动任务
    agent.start_task("Implement feature X")
    
    # Make a decision | 做出决策
    agent.make_decision(
        "Use three-tier architecture",
        alternatives=["two-tier", "four-tier"]
    )
    
    # Handle an error | 处理错误
    agent.handle_error("Connection timeout", "network")
    
    # Complete the task | 完成任务
    agent.complete_task("Implement feature X")
    
    # Compress context | 压缩上下文
    agent.compress_context()
    
    print("\n" + "=" * 60)
    print("Integration example completed successfully!")
    print("集成示例执行成功！")
    print("=" * 60)
