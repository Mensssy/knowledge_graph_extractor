"""
程序入口
Program Entry Point
"""

import sys
import os
import json
import yaml

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.text_splitter import TextSplitter
from src.modules.llm_extractor import LLMExtractor
from src.modules.kg_saver import KGSaver

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    # 1. 加载配置
    config_path = "config/config.yaml"
    config = load_config(config_path)
    
    processed_dir = config['paths'].get('processed_dir', 'data/processed')
    output_dir = config['paths']['output_dir']
    project_name = config['project']['name']
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting extraction for project: {project_name}")
    
    # 初始化模块
    splitter = TextSplitter(config)
    extractor = LLMExtractor(config)
    saver = KGSaver(output_dir, project_name)

    # 2. 处理所有文本文件
    for filename in os.listdir(processed_dir):
        if filename.endswith(".txt"):
            txt_path = os.path.join(processed_dir, filename)
            print(f"\nProcessing: {filename}")

            # 分割文本
            chunks = splitter.split_text_file(txt_path)
            print(f"Split into {len(chunks)} chunks.")

            # 提取三元组
            all_triplets = []
            for i, chunk in enumerate(chunks):
                print(f"\nExtracting triplets from chunk {i+1}/{len(chunks)}...")
                # 这里 extract_triplets 返回的是三元组字典列表
                # [{'subject': ..., 'subject_type': ..., 'relation_type': ..., 'object': ..., 'object_type': ..., 'evidence': ...}, ...]
                triplets = extractor.extract_triplets(chunk.text)
                
                # 过滤掉无效的三元组
                valid_triplets = [t for t in triplets if t.get('subject') and t.get('relation_type') and t.get('object')]
                
                # 输出本次请求找到的三元组数量和预览
                print(f"  Found {len(valid_triplets)} valid triplets in this chunk")
                if valid_triplets:
                    print("  Preview (first 2 triplets):")
                    for j, triplet in enumerate(valid_triplets[:2]):
                        print(f"    {j+1}. {triplet.get('subject')} -> {triplet.get('relation_type')} -> {triplet.get('object')}")
                        print(f"       Subject Type: {triplet.get('subject_type')}")
                        print(f"       Object Type: {triplet.get('object_type')}")
                        print(f"       Evidence: {triplet.get('evidence', 'N/A')}")
                
                all_triplets.extend(valid_triplets)

            # 3. 保存结果
            if all_triplets:
                # 创建子文件夹存放该文档的结果
                doc_output_dir = os.path.join(output_dir, filename.replace('.txt', ''))
                if not os.path.exists(doc_output_dir):
                    os.makedirs(doc_output_dir)
                
                # 先保存原始三元组到JSON文件
                json_file_path = os.path.join(doc_output_dir, "raw_triplets.json")
                try:
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(all_triplets, f, ensure_ascii=False, indent=2)
                    print(f"\n  Saved {len(all_triplets)} triplets to JSON: {json_file_path}")
                except Exception as e:
                    print(f"  Error saving JSON: {e}")
                
                # 使用 kg_saver 从JSON文件读取并生成CSV文件
                saver = KGSaver(doc_output_dir, project_name)
                saver.save_triplets(json_file_path=json_file_path)
                
                print(f"\nExtraction completed for {filename}. Total triplets: {len(all_triplets)}")
            else:
                print(f"No valid triplets extracted for {filename}.")

    print("\nAll tasks finished.")

if __name__ == "__main__":
    main()
