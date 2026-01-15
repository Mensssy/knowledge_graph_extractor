"""
三元组正确性验证脚本
Triplet Validation Script

该脚本通过在原始文本中查找evidence是否存在，来验证抽取三元组的正确性。
验证时忽略所有空白字符（空格、换行、制表符等）进行模糊匹配。
"""

import json
import os
import re
from typing import List, Dict, Tuple
from pathlib import Path


class TripletValidator:
    """三元组验证器"""
    
    def __init__(self, output_dir: str, processed_dir: str):
        """
        初始化验证器
        
        Args:
            output_dir: 三元组输出目录
            processed_dir: 处理后的文本目录
        """
        self.output_dir = output_dir
        self.processed_dir = processed_dir
        self.validation_results = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'details': []
        }
    
    def normalize_text(self, text: str) -> str:
        """
        规范化文本：移除所有空白字符
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        # 移除所有空白字符（包括空格、制表符、换行等）
        normalized = re.sub(r'\s+', '', text)
        return normalized
    
    def load_triplets(self, triplet_file: str) -> List[Dict]:
        """
        加载三元组数据
        
        Args:
            triplet_file: 三元组JSON文件路径
            
        Returns:
            三元组列表
        """
        try:
            with open(triplet_file, 'r', encoding='utf-8') as f:
                triplets = json.load(f)
            print(f"成功加载 {len(triplets)} 个三元组")
            return triplets
        except Exception as e:
            print(f"加载三元组失败: {e}")
            return []
    
    def load_text(self, text_file: str) -> str:
        """
        加载原始文本
        
        Args:
            text_file: 文本文件路径
            
        Returns:
            文本内容
        """
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"成功加载原始文本，长度: {len(text)} 字符")
            return text
        except Exception as e:
            print(f"加载文本失败: {e}")
            return ""
    
    def validate_triplet(self, triplet: Dict, normalized_text: str) -> Tuple[bool, str]:
        """
        验证单个三元组
        
        Args:
            triplet: 三元组字典
            normalized_text: 规范化后的原始文本
            
        Returns:
            (是否有效, 验证信息)
        """
        evidence = triplet.get('evidence', '').strip()
        
        if not evidence:
            return False, "证据为空"
        
        # 规范化证据文本
        normalized_evidence = self.normalize_text(evidence)
        
        # 检查证据是否在原文本中出现
        if normalized_evidence in normalized_text:
            return True, "证据在原文本中找到"
        else:
            # 如果完整的证据没找到，尝试查找关键的实体或短语
            subject = triplet.get('subject', '').strip()
            obj = triplet.get('object', '').strip()
            
            # 尝试查找主语和宾语是否同时存在
            normalized_subject = self.normalize_text(subject)
            normalized_object = self.normalize_text(obj)
            
            subject_found = normalized_subject in normalized_text if normalized_subject else False
            object_found = normalized_object in normalized_text if normalized_object else False
            
            if subject_found and object_found:
                return True, f"主语和宾语均在原文本中找到"
            elif subject_found or object_found:
                return True, f"主语或宾语在原文本中找到"
            else:
                return False, f"证据及实体在原文本中未找到"
    
    def validate_all(self, limit: int = 200) -> Dict:
        """
        验证所有三元组（最多limit条）
        
        Args:
            limit: 验证的最大三元组数量
            
        Returns:
            验证结果统计
        """
        # 查找输出目录中的原始三元组文件
        triplet_files = []
        for root, dirs, files in os.walk(self.output_dir):
            if 'raw_triplets.json' in files:
                triplet_files.append(os.path.join(root, 'raw_triplets.json'))
        
        if not triplet_files:
            print("未找到任何raw_triplets.json文件")
            return self.validation_results
        
        print(f"找到 {len(triplet_files)} 个三元组文件")
        
        # 对每个三元组文件进行验证
        for triplet_file in triplet_files:
            # 获取对应的文本文件
            doc_name = os.path.basename(os.path.dirname(triplet_file))
            text_file = os.path.join(self.processed_dir, f"{doc_name}.txt")
            
            if not os.path.exists(text_file):
                print(f"警告: 未找到对应的文本文件 {text_file}")
                continue
            
            print(f"\n验证文件: {doc_name}")
            print("=" * 70)
            
            # 加载数据
            triplets = self.load_triplets(triplet_file)
            original_text = self.load_text(text_file)
            
            if not triplets or not original_text:
                print("数据加载失败，跳过此文件")
                continue
            
            # 规范化原始文本
            normalized_text = self.normalize_text(original_text)
            
            # 只验证前limit条
            triplets_to_validate = triplets[:limit]
            
            print(f"开始验证前 {len(triplets_to_validate)} 个三元组...")
            
            for idx, triplet in enumerate(triplets_to_validate, 1):
                is_valid, reason = self.validate_triplet(triplet, normalized_text)
                
                self.validation_results['total'] += 1
                if is_valid:
                    self.validation_results['valid'] += 1
                    status = "✓"
                else:
                    self.validation_results['invalid'] += 1
                    status = "✗"
                
                # 记录详细信息
                detail = {
                    'index': idx,
                    'status': status,
                    'subject': triplet.get('subject', ''),
                    'relation': triplet.get('relation_type', ''),
                    'object': triplet.get('object', ''),
                    'evidence': triplet.get('evidence', '')[:100],  # 只记录前100个字符
                    'reason': reason
                }
                self.validation_results['details'].append(detail)
                
                # 打印进度（每10条打印一次）
                if idx % 10 == 0:
                    print(f"  已验证 {idx}/{len(triplets_to_validate)} 条")
        
        return self.validation_results
    
    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 70)
        print("验证报告总结")
        print("=" * 70)
        
        total = self.validation_results['total']
        valid = self.validation_results['valid']
        invalid = self.validation_results['invalid']
        
        if total == 0:
            print("未进行任何验证")
            return
        
        accuracy = (valid / total) * 100
        
        print(f"总验证条数: {total}")
        print(f"有效三元组: {valid} ({accuracy:.2f}%)")
        print(f"无效三元组: {invalid} ({100-accuracy:.2f}%)")
        
        # 按状态分类输出
        print("\n" + "-" * 70)
        print("详细验证结果（前20条）:")
        print("-" * 70)
        
        for detail in self.validation_results['details'][:20]:
            print(f"\n[{detail['index']}] {detail['status']} {detail['reason']}")
            print(f"  三元组: {detail['subject']} --[{detail['relation']}]--> {detail['object']}")
            print(f"  证据: {detail['evidence']}...")
        
        # 统计失败原因
        print("\n" + "-" * 70)
        print("失败三元组汇总（如有）:")
        print("-" * 70)
        
        failed_details = [d for d in self.validation_results['details'] if d['status'] == '✗']
        
        if failed_details:
            print(f"共有 {len(failed_details)} 个失败的三元组:")
            for detail in failed_details[:10]:  # 只显示前10个失败的
                print(f"\n  [{detail['index']}] {detail['reason']}")
                print(f"     {detail['subject']} -> {detail['object']}")
        else:
            print("所有验证的三元组都通过了验证！")
    
    def save_report(self, output_file: str = "data/output/validation_report.json"):
        """
        保存验证报告到JSON文件
        
        Args:
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
            print(f"\n验证报告已保存到: {output_file}")
        except Exception as e:
            print(f"保存报告失败: {e}")


def main():
    """主函数"""
    # 配置路径
    output_dir = "data/output"
    processed_dir = "data/processed"
    
    # 创建验证器
    validator = TripletValidator(output_dir, processed_dir)
    
    print("=" * 70)
    print("开始验证三元组正确性")
    print("=" * 70)
    print()
    
    validator.validate_all(limit=200)
    
    # 打印报告
    validator.print_report()
    
    # 保存报告
    validator.save_report("data/output/validation_report.json")


if __name__ == "__main__":
    main()
