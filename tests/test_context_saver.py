"""
Unit Tests for Context Saver
Context Saver 单元测试
"""

import unittest
import os
import tempfile
import shutil
from context_saver import AutoContextFlush, OperationTracker, CompressionGuard


class TestAutoContextFlush(unittest.TestCase):
    """Tests for AutoContextFlush | AutoContextFlush 测试"""
    
    def setUp(self):
        """Set up test fixtures | 设置测试夹具"""
        self.test_dir = tempfile.mkdtemp()
        self.flusher = AutoContextFlush(
            save_dir=self.test_dir,
            max_snapshots=5
        )
    
    def tearDown(self):
        """Clean up test fixtures | 清理测试夹具"""
        shutil.rmtree(self.test_dir)
    
    def test_save_session(self):
        """Test session saving | 测试会话保存"""
        session_id = "test_001"
        result = self.flusher.save_session(
            session_id=session_id,
            todos=["Task 1", "Task 2"],
            decisions=["Decision 1"],
            recent_requests=["Request 1"]
        )
        
        self.assertTrue(result)
        
        # Check if file exists | 检查文件是否存在
        history_dir = os.path.join(self.test_dir, "context_flush_history")
        self.assertTrue(os.path.exists(history_dir))
    
    def test_max_snapshots(self):
        """Test max snapshots limit | 测试最大快照限制"""
        # Save 10 sessions | 保存 10 个会话
        for i in range(10):
            self.flusher.save_session(
                session_id=f"test_{i}",
                todos=[],
                decisions=[],
                recent_requests=[]
            )
        
        # Check if only 5 snapshots remain | 检查是否只保留 5 个快照
        history_dir = os.path.join(self.test_dir, "context_flush_history")
        files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
        self.assertLessEqual(len(files), 5)


class TestOperationTracker(unittest.TestCase):
    """Tests for OperationTracker | OperationTracker 测试"""
    
    def setUp(self):
        """Set up test fixtures | 设置测试夹具"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.jsonl',
            delete=False
        )
        self.test_file.close()
        self.tracker = OperationTracker(log_file=self.test_file.name)
    
    def tearDown(self):
        """Clean up test fixtures | 清理测试夹具"""
        os.unlink(self.test_file.name)
    
    def test_track_operation(self):
        """Test operation tracking | 测试操作跟踪"""
        result = self.tracker.track(
            op_type="config_change",
            description="Test config change",
            details={"key": "value"}
        )
        
        self.assertTrue(result)
        
        # Check if log file has content | 检查日志文件是否有内容
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            self.assertIn("config_change", content)
    
    def test_track_multiple_operations(self):
        """Test tracking multiple operations | 测试跟踪多个操作"""
        operations = [
            ("config_change", "Config 1"),
            ("file_write", "File 1"),
            ("decision", "Decision 1"),
        ]
        
        for op_type, desc in operations:
            self.tracker.track(
                op_type=op_type,
                description=desc,
                details={}
            )
        
        # Check log file | 检查日志文件
        with open(self.test_file.name, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 3)


class TestCompressionGuard(unittest.TestCase):
    """Tests for CompressionGuard | CompressionGuard 测试"""
    
    def setUp(self):
        """Set up test fixtures | 设置测试夹具"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False
        )
        self.test_file.write("# Test Context")
        self.test_file.close()
        
        self.flusher_dir = tempfile.mkdtemp()
        self.flusher = AutoContextFlush(save_dir=self.flusher_dir)
        self.guard = CompressionGuard(
            context_file=self.test_file.name,
            threshold_minutes=30
        )
    
    def tearDown(self):
        """Clean up test fixtures | 清理测试夹具"""
        os.unlink(self.test_file.name)
        shutil.rmtree(self.flusher_dir)
    
    def test_should_save_fresh(self):
        """Test should_save with fresh file | 测试新鲜文件的 should_save"""
        # File is fresh (just created) | 文件是新鲜的（刚创建）
        should_save = self.guard.should_save()
        self.assertFalse(should_save)
    
    def test_force_save(self):
        """Test force save | 测试强制保存"""
        result = self.guard.force_save(self.flusher)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
