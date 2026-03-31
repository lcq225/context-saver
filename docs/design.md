# Context Saver Design Document | 设计文档

## 1. Overview | 概述

Context Saver is a three-tier context preservation system designed for AI agents to prevent data loss and maintain session continuity.

Context Saver 是一个三层上下文保存系统，专为 AI Agent 设计，用于防止数据丢失并保持会话连续性。

### 1.1 Problem Statement | 问题陈述

**Problems | 问题：**
1. Session context lost during compression | 压缩时会话上下文丢失
2. No automatic save mechanism | 无自动保存机制
3. Key operations not tracked | 关键操作未跟踪
4. No historical traceability | 无历史追溯能力
5. Manual save容易忘记 | Manual save easy to forget

**Impact | 影响：**
- Task interruption cannot be recovered | 任务中断无法恢复
- Decision process cannot be reviewed | 决策过程无法回顾
- Error lessons not recorded | 错误教训未记录
- Work efficiency reduced | 工作效率降低

### 1.2 Solution | 解决方案

**Three-tier Architecture | 三层架构：**

```
┌─────────────────────────────────────────────────────────┐
│              Three-tier Context Preservation            │
│                  三层上下文保存体系                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   L1: Real-time State (CURRENT_TASK.md)                 │
│       实时状态 - 秒级更新                                │
│       - Current task status                             │
│       - Pending todos                                   │
│       - Recent decisions                                │
│                                                         │
│   L2: Session Snapshot (context_flush_history/)         │
│       会话快照 - 会话级保存                              │
│       - Full session context                            │
│       - Operation logs                                  │
│       - Key decisions & lessons                         │
│                                                         │
│   L3: Archive Version (archive/)                        │
│       归档版本 - 日/周级归档                             │
│       - Daily summaries                                 │
│       - Weekly reports                                  │
│       - Long-term storage                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture | 架构

### 2.1 Core Components | 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                   Context Saver Core                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────────────┐  ┌─────────────────┐             │
│   │ AutoContextFlush│  │OperationTracker │             │
│   │ 自动上下文刷新   │  │  操作跟踪器      │             │
│   ├─────────────────┤  ├─────────────────┤             │
│   │ - save_session()│  │ - track()       │             │
│   │ - load_session()│  │ - get_logs()    │             │
│   │ - cleanup()     │  │ - export()      │             │
│   └─────────────────┘  └─────────────────┘             │
│                                                         │
│   ┌─────────────────┐                                  │
│   │CompressionGuard │                                  │
│   │  压缩保护器      │                                  │
│   ├─────────────────┤                                  │
│   │ - should_save() │                                  │
│   │ - force_save()  │                                  │
│   │ - verify()      │                                  │
│   └─────────────────┘                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow | 数据流

```
User Action | 用户操作
    ↓
Operation Tracker (记录操作)
    ↓
Context Update (更新上下文)
    ↓
AutoContextFlush (自动保存)
    ↓
L2 Session Snapshot (会话快照)
    ↓
Compression Guard (压缩前检查)
    ↓
Safe to Compress (安全压缩)
```

---

## 3. Component Design | 组件设计

### 3.1 AutoContextFlush | 自动上下文刷新

**Responsibilities | 职责：**
- Save session context automatically | 自动保存会话上下文
- Manage session snapshots | 管理会话快照
- Cleanup old snapshots | 清理旧快照

**API | 接口：**
```python
class AutoContextFlush:
    def __init__(self, save_dir: str, max_snapshots: int = 30)
    def save_session(self, session_id: str, todos: list, 
                     decisions: list, recent_requests: list) -> bool
    def load_session(self, session_id: str) -> dict
    def cleanup(self) -> int
```

**Implementation Details | 实现细节：**
- Save format: JSON | 保存格式：JSON
- Naming: `context_flush_YYYYMMDD_HHMMSS.json` | 命名：时间戳格式
- Cleanup strategy: FIFO (keep last N) | 清理策略：先进先出

### 3.2 OperationTracker | 操作跟踪器

**Responsibilities | 职责：**
- Track key operations | 跟踪关键操作
- Log operation details | 记录操作详情
- Export operation logs | 导出操作日志

**Operation Types | 操作类型：**
| Type | 类型 | Description | 说明 |
|------|------|-------------|------|
| `config_change` | 配置变更 | Configuration modified | 配置修改 |
| `file_write` | 文件写入 | File created/modified | 文件创建/修改 |
| `decision` | 决策 | Important decision made | 重要决策 |
| `error` | 错误 | Error occurred | 发生错误 |
| `task_update` | 任务更新 | Task status changed | 任务状态变更 |
| `external` | 外部调用 | External API call | 外部 API 调用 |

**API | 接口：**
```python
class OperationTracker:
    def __init__(self, log_file: str)
    def track(self, op_type: str, description: str, 
              details: dict) -> bool
    def get_logs(self, start_time: str = None, 
                 end_time: str = None) -> list
    def export(self, format: str = "json") -> str
```

### 3.3 CompressionGuard | 压缩保护器

**Responsibilities | 职责：**
- Check context freshness | 检查上下文新鲜度
- Force save before compression | 压缩前强制保存
- Verify save success | 验证保存成功

**Protection Flow | 保护流程：**
```
1. Check context file age | 检查上下文文件年龄
   ↓
2. If age > threshold (30min) | 如果年龄 > 阈值（30 分钟）
   ↓
3. Force save | 强制保存
   ↓
4. Verify save success | 验证保存成功
   ↓
5. Proceed with compression | 执行压缩
```

**API | 接口：**
```python
class CompressionGuard:
    def __init__(self, context_file: str, threshold_minutes: int = 30)
    def should_save(self) -> bool
    def force_save(self, flusher: AutoContextFlush) -> bool
    def verify(self) -> bool
```

---

## 4. Data Structures | 数据结构

### 4.1 Session Snapshot | 会话快照

```json
{
  "session_id": "session_20260401_090000",
  "timestamp": "2026-04-01T09:00:00+08:00",
  "todos": [
    {"task": "Task 1", "priority": "high", "status": "in_progress"}
  ],
  "decisions": [
    {"decision": "Adopt three-tier architecture", "reason": "..."}
  ],
  "recent_requests": [
    {"request": "Implement feature X", "timestamp": "..."}
  ],
  "operation_logs": [...],
  "context_summary": "..."
}
```

### 4.2 Operation Log | 操作日志

```json
{
  "timestamp": "2026-04-01T09:00:00+08:00",
  "op_type": "config_change",
  "description": "Updated memory threshold",
  "details": {
    "old_value": 100,
    "new_value": 200,
    "reason": "Performance optimization"
  },
  "session_id": "session_20260401_090000"
}
```

---

## 5. Error Handling | 错误处理

### 5.1 Error Types | 错误类型

| Error | 错误 | Handling | 处理方式 |
|-------|------|----------|----------|
| File write failed | 文件写入失败 | Retry 3 times, then alert | 重试 3 次，然后告警 |
| JSON parse error | JSON 解析错误 | Log error, skip record | 记录错误，跳过记录 |
| Directory not found | 目录不存在 | Create automatically | 自动创建 |
| Permission denied | 权限拒绝 | Alert user | 告警用户 |

### 5.2 Recovery Strategy | 恢复策略

```
Error detected | 检测到错误
    ↓
Log error details | 记录错误详情
    ↓
Attempt recovery | 尝试恢复
    ↓
If recovery fails | 如果恢复失败
    ↓
Alert user | 告警用户
    ↓
Continue operation | 继续操作
```

---

## 6. Performance Considerations | 性能考虑

### 6.1 Optimization Strategies | 优化策略

1. **Async Save** - Non-blocking save operations | 异步保存 - 非阻塞保存操作
2. **Batch Write** - Batch write operation logs | 批量写入 - 批量写入操作日志
3. **Compression** - Compress old snapshots | 压缩 - 压缩旧快照
4. **Cleanup** - Regular cleanup of old data | 清理 - 定期清理旧数据

### 6.2 Performance Targets | 性能目标

| Metric | 指标 | Target | 目标 |
|--------|------|--------|------|
| Save latency | 保存延迟 | < 100ms | < 100ms |
| Track latency | 跟踪延迟 | < 10ms | < 10ms |
| Storage per day | 每日存储 | < 10MB | < 10MB |
| Max snapshots | 最大快照数 | 30 | 30 |

---

## 7. Security Considerations | 安全考虑

### 7.1 Data Protection | 数据保护

- **No sensitive data** - Don't store passwords, tokens | 不存储密码、令牌
- **File permissions** - Restrict access to saved files | 限制文件访问权限
- **Encryption (optional)** - Encrypt sensitive context | 加密敏感上下文（可选）

### 7.2 Sanitization | 数据清理

- Remove sensitive information before save | 保存前移除敏感信息
- Sanitize file paths | 清理文件路径
- Validate input data | 验证输入数据

---

## 8. Testing Strategy | 测试策略

### 8.1 Test Types | 测试类型

1. **Unit Tests** - Test individual components | 单元测试 - 测试独立组件
2. **Integration Tests** - Test component interaction | 集成测试 - 测试组件交互
3. **End-to-End Tests** - Test complete workflow | 端到端测试 - 测试完整流程

### 8.2 Test Coverage | 测试覆盖率

- **Target**: > 80% code coverage | 目标：> 80% 代码覆盖率
- **Critical paths**: 100% coverage | 关键路径：100% 覆盖率

---

## 9. Future Enhancements | 未来增强

### Phase 2 (归档管理)
- [ ] Daily/weekly archive manager | 日/周归档管理器
- [ ] Scheduled cleanup tasks | 定时清理任务
- [ ] Compression strategies | 压缩策略

### Phase 3 (监控告警)
- [ ] Timestamp check script | 时间戳检查脚本
- [ ] Expiration alert | 过期告警
- [ ] Save failure notification | 保存失败通知
- [ ] Health check script | 健康检查脚本

### Phase 4 (高级功能)
- [ ] Context search | 上下文搜索
- [ ] Context comparison | 上下文对比
- [ ] Context restore | 上下文恢复
- [ ] Multi-agent sync | 多 Agent 同步

---

## 10. References | 参考

- [CoPaw Context Management](https://github.com/agentscope-ai/CoPaw)
- [Best Practices Document](https://github.com/lcq225/copaw-best-practices/blob/main/docs/context-flush-best-practices.md)

---

**Version | 版本：** 1.0.0  
**Date | 日期：** 2026-04-01  
**Author | 作者：** Mr Lee  
**License | 许可证：** MIT
