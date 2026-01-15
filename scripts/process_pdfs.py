"""
批量处理PDF文件脚本
Batch Process PDF Files Script
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.modules.data_loader import DataLoader

def main():
    print("=" * 70)
    print("批量处理PDF文件")
    print("=" * 70)
    
    # 初始化数据加载器
    loader = DataLoader(input_dir="./data/input")
    
    # 列出所有PDF文件
    print("\n查找PDF文件...")
    pdf_files = loader.list_pdf_files()
    
    if not pdf_files:
        print("未找到PDF文件！")
        print("请将PDF文件放入 data/input/ 目录")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {Path(pdf).name}")
    
    # 批量处理所有PDF文件
    print("\n开始批量处理...")
    success_count = 0
    fail_count = 0
    
    for pdf_file in pdf_files:
        try:
            print(f"\n正在处理: {Path(pdf_file).name}")
            
            # 读取PDF文件
            text = loader.load_pdf(pdf_file)
            print(f"  ✓ 成功提取 {len(text)} 个字符")
            
            # 保存到processed目录
            output_path = f"./data/processed/{Path(pdf_file).stem}.txt"
            loader.save_text(text, output_path)
            print(f"  ✓ 已保存到: {output_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            fail_count += 1
    
    # 输出统计信息
    print("\n" + "=" * 70)
    print("处理完成！")
    print("=" * 70)
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"总计: {success_count + fail_count} 个")
    print("\n处理后的文本文件已保存在 data/processed/ 目录")
    print("=" * 70)


if __name__ == "__main__":
    main()
