"""
数据读入模块
Data Loading Module for PDF Files
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
from PyPDF2 import PdfReader


class DataLoader:
    """PDF文件数据加载器"""
    
    def __init__(self, input_dir: str = "./data/input"):
        """
        初始化数据加载器
        
        Args:
            input_dir: 输入PDF文件目录
        """
        self.input_dir = Path(input_dir)
        self.logger = self._setup_logger()
        
        # 确保输入目录存在
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def load_pdf(self, file_path: str) -> str:
        """
        加载单个PDF文件并提取文本内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的文本内容
            
        Raises:
            FileNotFoundError: 文件不存在
            Exception: PDF读取错误
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"文件格式错误，需要PDF文件: {file_path}")
        
        self.logger.info(f"开始读取PDF文件: {file_path}")
        
        try:
            # 创建PDF读取器
            reader = PdfReader(file_path)
            
            # 获取总页数
            num_pages = len(reader.pages)
            self.logger.info(f"PDF总页数: {num_pages}")
            
            # 提取所有页面的文本
            full_text = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        full_text.append(text)
                        self.logger.debug(f"成功提取第 {page_num}/{num_pages} 页")
                except Exception as e:
                    self.logger.warning(f"第 {page_num} 页提取失败: {e}")
                    continue
            
            # 合并所有文本
            text_content = '\n\n'.join(full_text)
            
            self.logger.info(f"成功提取文本，总长度: {len(text_content)} 字符")
            
            return text_content
            
        except PyPDF2.PdfReadError as e:
            self.logger.error(f"PDF读取错误: {e}")
            raise Exception(f"PDF文件可能已损坏或加密: {e}")
        except Exception as e:
            self.logger.error(f"未知错误: {e}")
            raise Exception(f"读取PDF文件时出错: {e}")
    
    def load_pdf_by_page(self, file_path: str) -> List[str]:
        """
        按页加载PDF文件内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            每页文本内容的列表
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        self.logger.info(f"按页读取PDF文件: {file_path}")
        
        try:
            reader = PdfReader(file_path)
            pages_text = []
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    pages_text.append(text or "")
                except Exception as e:
                    self.logger.warning(f"第 {page_num} 页提取失败: {e}")
                    pages_text.append("")
            
            self.logger.info(f"成功提取 {len(pages_text)} 页内容")
            return pages_text
            
        except Exception as e:
            self.logger.error(f"按页读取PDF失败: {e}")
            raise Exception(f"读取PDF文件时出错: {e}")
    
    def get_pdf_info(self, file_path: str) -> Dict:
        """
        获取PDF文件信息
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            PDF文件信息字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            reader = PdfReader(file_path)
            info = {
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'num_pages': len(reader.pages),
                'metadata': reader.metadata
            }
            
            self.logger.info(f"获取PDF信息: {info}")
            return info
            
        except Exception as e:
            self.logger.error(f"获取PDF信息失败: {e}")
            raise Exception(f"获取PDF信息时出错: {e}")
    
    def list_pdf_files(self, directory: Optional[str] = None) -> List[str]:
        """
        列出目录中的所有PDF文件
        
        Args:
            directory: 目录路径，默认为初始化时的input_dir
            
        Returns:
            PDF文件路径列表
        """
        target_dir = Path(directory) if directory else self.input_dir
        
        if not target_dir.exists():
            self.logger.warning(f"目录不存在: {target_dir}")
            return []
        
        pdf_files = list(target_dir.glob('*.pdf'))
        pdf_files.extend(target_dir.glob('*.PDF'))
        
        # 去重并排序
        pdf_files = sorted(set(pdf_files))
        
        self.logger.info(f"在目录 {target_dir} 中找到 {len(pdf_files)} 个PDF文件")
        
        return [str(f) for f in pdf_files]
    
    def load_all_pdfs(self, directory: Optional[str] = None) -> Dict[str, str]:
        """
        加载目录中的所有PDF文件
        
        Args:
            directory: 目录路径，默认为初始化时的input_dir
            
        Returns:
            字典: {文件路径: 文本内容}
        """
        pdf_files = self.list_pdf_files(directory)
        
        if not pdf_files:
            self.logger.warning("未找到PDF文件")
            return {}
        
        results = {}
        
        for pdf_file in pdf_files:
            try:
                text = self.load_pdf(pdf_file)
                results[pdf_file] = text
            except Exception as e:
                self.logger.error(f"加载文件 {pdf_file} 失败: {e}")
                continue
        
        self.logger.info(f"成功加载 {len(results)}/{len(pdf_files)} 个PDF文件")
        
        return results
    
    def save_text(self, text: str, output_path: str) -> None:
        """
        保存提取的文本到文件
        
        Args:
            text: 文本内容
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        self.logger.info(f"文本已保存到: {output_path}")
    
    def load_from_txt(self, pdf_path: str, processed_dir: str = "./data/processed") -> Optional[str]:
        """
        从processed目录加载已提取的txt文件
        
        Args:
            pdf_path: 原始PDF文件路径
            processed_dir: 处理后的文本目录
            
        Returns:
            文本内容，如果文件不存在则返回None
        """
        pdf_path = Path(pdf_path)
        processed_path = Path(processed_dir)
        
        # 构建对应的txt文件路径
        txt_path = processed_path / f"{pdf_path.stem}.txt"
        
        if not txt_path.exists():
            self.logger.info(f"未找到已处理的文本文件: {txt_path}")
            return None
        
        self.logger.info(f"从已处理的文本文件读取: {txt_path}")
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        self.logger.info(f"成功加载文本，总长度: {len(text_content)} 字符")
        
        return text_content
    
    def load_text(self, file_path: str, processed_dir: str = "./data/processed") -> str:
        """
        加载文本内容，优先从processed目录读取txt文件，如果不存在则从PDF提取
        
        Args:
            file_path: PDF文件路径
            processed_dir: 处理后的文本目录
            
        Returns:
            文本内容
        """
        # 先尝试从processed目录读取
        text = self.load_from_txt(file_path, processed_dir)
        
        if text is not None:
            return text
        
        # 如果txt文件不存在，则从PDF提取
        return self.load_pdf(file_path)
