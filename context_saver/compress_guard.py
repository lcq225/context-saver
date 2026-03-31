"""
压缩保护器 - 在上下文压缩前强制保存，确保信息安全

集成到 self_evolution 的压缩流程中
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 导入自动保存模块
from auto_context_flush import flush_context, ensure_dirs, CONTEXT_FLUSH_LATEST

# ==================== 配置 ====================

WORKSPACE_DIR = Path(r"D:\CoPaw\.copaw\workspaces\default")
ARCHIVE_DIR = WORKSPACE_DIR / "archive"
COMPRESS_ARCHIVE_DIR = ARCHIVE_DIR / "compress_backups"

# 时间戳阈值（秒）- 如果 context_flush.md 超过这个时间，强制刷新
FLUSH_THRESHOLD_SECONDS = 1800  # 30 分钟

# ==================== 核心功能 ====================

def get_file_age(file_path):
    """获取文件年龄（秒）"""
    if not file_path.exists():
        return float('inf')
    
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    age = datetime.now() - mtime
    return age.total_seconds()

def before_compress():
    """
    压缩前强制保存上下文
    
    Returns:
        保存的文件路径
    """
    ensure_dirs()
    
    print("\n🛡️  压缩保护检查...")
    
    # 1. 检查 context_flush.md 时间戳
    age_seconds = get_file_age(CONTEXT_FLUSH_LATEST)
    age_minutes = age_seconds / 60
    
    print(f"   context_flush.md 年龄：{age_minutes:.1f} 分钟")
    print(f"   阈值：{FLUSH_THRESHOLD_SECONDS/60:.0f} 分钟")
    
    # 2. 如果超过阈值，强制刷新
    if age_seconds > FLUSH_THRESHOLD_SECONDS:
        print(f"   ⚠️  超过阈值，强制刷新...")
        flush_path = flush_context(reason="before_compress")
        print(f"   ✅ 已保存：{flush_path}")
    else:
        print(f"   ✅ 时间戳新鲜，无需刷新")
        flush_path = str(CONTEXT_FLUSH_LATEST)
    
    # 3. 保存压缩前快照到 archive/
    backup_path = save_compress_backup()
    print(f"   ✅ 压缩备份：{backup_path}")
    
    return flush_path

def save_compress_backup():
    """
    保存压缩前快照到归档目录
    
    Returns:
        备份文件路径
    """
    COMPRESS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = COMPRESS_ARCHIVE_DIR / f"pre_compress_{timestamp}.md"
    
    # 读取当前 context_flush.md
    if CONTEXT_FLUSH_LATEST.exists():
        with open(CONTEXT_FLUSH_LATEST, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 添加备份头
        backup_content = f"""# 🗄️ 压缩前备份

> 备份时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 原始文件：{CONTEXT_FLUSH_LATEST}

---

{content}
"""
        
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(backup_content)
    else:
        # 如果不存在，创建空备份
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(f"# 🗄️ 压缩前备份\n\n> 备份时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n> 原始文件不存在\n")
    
    # 清理旧备份（保留最近 10 次）
    cleanup_old_backups()
    
    return str(backup_path)

def cleanup_old_backups():
    """清理旧的压缩备份（保留最近 10 次）"""
    if not COMPRESS_ARCHIVE_DIR.exists():
        return
    
    files = sorted(COMPRESS_ARCHIVE_DIR.glob("pre_compress_*.md"), reverse=True)
    
    for old_file in files[10:]:
        try:
            old_file.unlink()
        except Exception as e:
            print(f"⚠️  清理备份失败：{old_file.name} - {e}")

def verify_after_compress(compressed_content, backup_path):
    """
    压缩后验证 - 确保关键信息未丢失
    
    Args:
        compressed_content: 压缩后的内容
        backup_path: 压缩前备份路径
    
    Returns:
        bool: 验证是否通过
    """
    print("\n🔍 压缩后验证...")
    
    # 读取压缩前备份
    if not Path(backup_path).exists():
        print("   ⚠️  备份文件不存在，跳过验证")
        return True
    
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_content = f.read()
    
    # 提取关键信息（任务、决策、错误）
    critical_keywords = ["进行中任务", "关键决策", "错误", "教训"]
    
    missing_keywords = []
    for keyword in critical_keywords:
        if keyword in backup_content and keyword not in compressed_content:
            missing_keywords.append(keyword)
    
    if missing_keywords:
        print(f"   ⚠️  警告：以下关键信息可能丢失：{missing_keywords}")
        print(f"   💡  建议检查备份：{backup_path}")
        return False
    else:
        print(f"   ✅ 关键信息完整")
        return True

# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="压缩保护工具")
    parser.add_argument("--check", action="store_true", help="仅检查，不保存")
    parser.add_argument("--verify", help="验证压缩后的内容（传入压缩文件路径）")
    
    args = parser.parse_args()
    
    if args.check:
        age = get_file_age(CONTEXT_FLUSH_LATEST)
        print(f"context_flush.md 年龄：{age/60:.1f} 分钟")
        print(f"阈值：{FLUSH_THRESHOLD_SECONDS/60:.0f} 分钟")
        print(f"需要刷新：{'是' if age > FLUSH_THRESHOLD_SECONDS else '否'}")
        return
    
    if args.verify:
        # 读取压缩文件
        with open(args.verify, "r", encoding="utf-8") as f:
            compressed = f.read()
        
        # 找到最近的备份
        backups = sorted(COMPRESS_ARCHIVE_DIR.glob("pre_compress_*.md"), reverse=True)
        if backups:
            verify_after_compress(compressed, str(backups[0]))
        else:
            print("⚠️  未找到备份文件")
        return
    
    # 默认执行 before_compress
    before_compress()

if __name__ == "__main__":
    main()
