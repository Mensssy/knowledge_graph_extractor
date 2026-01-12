"""
文本分块模块
Text Splitter Module for splitting long text into chunks
"""

import re
import logging
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class TextChunk:
    """文本块数据类"""
    chunk_id: str
    text: str
    token_count: int
    start_char: int
    end_char: int


class TextSplitter:
    """文本分块器，按token数量将长文本分割成多个块"""
    
    # 中文字符平均token数（简化计算）
    CHARS_PER_TOKEN = 1.5
    
    def __init__(self, config):
        """
        初始化文本分块器
        
        Args:
            config: 配置字典，包含 chunk_size 和 chunk_overlap
        """
        self.max_tokens = config.get('text_splitter', {}).get('chunk_size', 4096)
        self.overlap_ratio = config.get('text_splitter', {}).get('chunk_overlap', 200) / self.max_tokens
        self.min_chunk_size = 100
        self.logger = self._setup_logger()
        self.chunk_overlap = config.get('text_splitter', {}).get('chunk_overlap', 200)
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        # 简化计算：中文字符数 * 1.5 + 英文单词数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(text) - chinese_chars - english_chars
        
        # 中文字符约1.5 tokens/字符，英文约0.3 tokens/字符
        tokens = int(chinese_chars * 1.5 + english_chars * 0.3 + other_chars * 0.5)
        return max(tokens, 1)
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        按句子分割文本
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        # 中文句号、问号、感叹号、英文标点
        sentence_pattern = r'[。！？\.!?]+'
        sentences = re.split(sentence_pattern, text)
        
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def split_text(self, text: str) -> List[TextChunk]:
        """
        将长文本分割成多个块
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        self.logger.info(f"开始分割文本，总长度: {len(text)} 字符")
        
        if not text or len(text) <= self.min_chunk_size:
            # 文本太短，直接返回一个块
            token_count = self.estimate_tokens(text)
            chunk = TextChunk(
                chunk_id="chunk_001",
                text=text,
                token_count=token_count,
                start_char=0,
                end_char=len(text)
            )
            self.logger.info(f"文本较短，返回1个块，约{token_count} tokens")
            return [chunk]
        
        # 按句子分割
        sentences = self.split_by_sentences(text)
        self.logger.info(f"文本分割为 {len(sentences)} 个句子")
        
        chunks = []
        current_chunk = []
        current_chars = 0
        chunk_index = 1
        
        # 计算最大字符数
        max_chars = int(self.max_tokens / self.CHARS_PER_TOKEN)
        overlap_chars = int(max_chars * self.overlap_ratio)
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            
            # 如果加入这个句子会超过最大长度，且当前块不为空
            if current_chars + sentence_len > max_chars and current_chunk:
                # 保存当前块
                chunk_text = '。'.join(current_chunk) + '。'
                start_char = sum(len(s) + 1 for s in sentences[:i - len(current_chunk)])
                end_char = start_char + len(chunk_text)
                
                chunk = TextChunk(
                    chunk_id=f"chunk_{chunk_index:03d}",
                    text=chunk_text,
                    token_count=self.estimate_tokens(chunk_text),
                    start_char=start_char,
                    end_char=min(end_char, len(text))
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 处理重叠：保留最后几个句子
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, overlap_chars
                )
                current_chunk = overlap_sentences
                current_chars = sum(len(s) for s in overlap_sentences)
            
            # 添加当前句子
            current_chunk.append(sentence)
            current_chars += sentence_len
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '。'.join(current_chunk) + '。'
            start_pos = chunks[-1].end_char - overlap_chars if chunks else 0
            
            chunk = TextChunk(
                chunk_id=f"chunk_{chunk_index:03d}",
                text=chunk_text,
                token_count=self.estimate_tokens(chunk_text),
                start_char=max(start_pos, 0),
                end_char=len(text)
            )
            chunks.append(chunk)
        
        self.logger.info(f"文本分割完成，共 {len(chunks)} 个块")
        
        # 打印每个块的信息
        for chunk in chunks:
            self.logger.info(
                f"  {chunk.chunk_id}: {chunk.token_count} tokens, "
                f"{len(chunk.text)} chars [{chunk.start_char}:{chunk.end_char}]"
            )
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str], 
                              overlap_chars: int) -> List[str]:
        """
        获取用于重叠的句子
        
        Args:
            sentences: 当前块的句子列表
            overlap_chars: 重叠字符数
            
        Returns:
            重叠部分的句子列表
        """
        if not sentences:
            return []
        
        overlap = []
        current_chars = 0
        
        # 从后向前添加句子，直到达到重叠字符数
        for sentence in reversed(sentences):
            if current_chars + len(sentence) >= overlap_chars:
                overlap.insert(0, sentence)
                current_chars += len(sentence)
                break
            overlap.insert(0, sentence)
            current_chars += len(sentence)
        
        return overlap
    
    def split_text_by_paragraphs(self, text: str) -> List[TextChunk]:
        """
        按段落分割文本（备选方法）
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        self.logger.info("按段落分割文本")
        
        # 按段落分割
        paragraphs = re.split(r'\n\n+', text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_chars = 0
        chunk_index = 1
        
        max_chars = int(self.max_tokens / self.CHARS_PER_TOKEN)
        overlap_chars = int(max_chars * self.overlap_ratio)
        
        for i, paragraph in enumerate(paragraphs):
            para_len = len(paragraph)
            
            # 单个段落太大，按句子分割
            if para_len > max_chars:
                # 先保存当前块
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    start_char = sum(len(p) + 2 for p in paragraphs[:i - len(current_chunk)])
                    end_char = start_char + len(chunk_text)
                    
                    chunk = TextChunk(
                        chunk_id=f"chunk_{chunk_index:03d}",
                        text=chunk_text,
                        token_count=self.estimate_tokens(chunk_text),
                        start_char=start_char,
                        end_char=min(end_char, len(text))
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = []
                    current_chars = 0
                
                # 对大段落按句子分割
                sub_sentences = self.split_by_sentences(paragraph)
                for sentence in sub_sentences:
                    if current_chars + len(sentence) > max_chars and current_chunk:
                        chunk_text = '。'.join(current_chunk) + '。'
                        chunk = TextChunk(
                            chunk_id=f"chunk_{chunk_index:03d}",
                            text=chunk_text,
                            token_count=self.estimate_tokens(chunk_text),
                            start_char=len('\n\n'.join(paragraphs[:i])),
                            end_char=len('\n\n'.join(paragraphs[:i])) + len(chunk_text)
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        current_chunk = []
                        current_chars = 0
                    
                    current_chunk.append(sentence)
                    current_chars += len(sentence)
                
                # 处理当前块
                if current_chunk:
                    chunk_text = '。'.join(current_chunk) + '。'
                    chunk = TextChunk(
                        chunk_id=f"chunk_{chunk_index:03d}",
                        text=chunk_text,
                        token_count=self.estimate_tokens(chunk_text),
                        start_char=len('\n\n'.join(paragraphs[:i])),
                        end_char=len('\n\n'.join(paragraphs[:i])) + len(chunk_text)
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = []
                    current_chars = 0
                
            else:
                # 添加段落到当前块
                if current_chars + para_len > max_chars and current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    start_char = sum(len(p) + 2 for p in paragraphs[:i - len(current_chunk)])
                    end_char = start_char + len(chunk_text)
                    
                    chunk = TextChunk(
                        chunk_id=f"chunk_{chunk_index:03d}",
                        text=chunk_text,
                        token_count=self.estimate_tokens(chunk_text),
                        start_char=start_char,
                        end_char=min(end_char, len(text))
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = []
                    current_chars = 0
                
                current_chunk.append(paragraph)
                current_chars += para_len
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            start_pos = chunks[-1].end_char if chunks else 0
            
            chunk = TextChunk(
                chunk_id=f"chunk_{chunk_index:03d}",
                text=chunk_text,
                token_count=self.estimate_tokens(chunk_text),
                start_char=max(start_pos, 0),
                end_char=len(text)
            )
            chunks.append(chunk)
        
        self.logger.info(f"按段落分割完成，共 {len(chunks)} 个块")
        
        return chunks
    
    def split_text_file(self, file_path: str) -> List[TextChunk]:
        """
        读取并分割文本文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文本块列表
        """
        self.logger.info(f"读取文件: {file_path}")
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        self.logger.info(f"文件读取完成，共 {len(text)} 字符")
        
        # 分割文本
        return self.split_text(text)
