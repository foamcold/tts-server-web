"""
文本处理器
处理替换规则、分割等
"""
import re
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.replace_rule import ReplaceRule
from ..models.speech_rule import SpeechRule
from ..plugins.js_engine import PluginEngine


class TextProcessor:
    """文本处理器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._replace_rules: List[ReplaceRule] = []
        self._speech_rules: List[SpeechRule] = []
        self._loaded = False

    async def load_rules(self):
        """加载规则"""
        if self._loaded:
            return
        
        # 加载替换规则 (只加载TTS前执行的规则, execution=0)
        stmt = select(ReplaceRule).where(
            ReplaceRule.is_enabled == True,
            ReplaceRule.execution == 0  # TTS 前执行
        ).order_by(ReplaceRule.order)
        result = await self.db.execute(stmt)
        self._replace_rules = list(result.scalars().all())
        # 加载朗读规则
        stmt = select(SpeechRule).where(
            SpeechRule.is_enabled == True
        ).order_by(SpeechRule.order)
        result = await self.db.execute(stmt)
        self._speech_rules = list(result.scalars().all())
        
        self._loaded = True

    def apply_replace_rules(self, text: str) -> str:
        """应用替换规则"""
        for rule in self._replace_rules:
            try:
                # pattern_type: 0=普通文本, 1=正则表达式
                if rule.pattern_type == 1:
                    text = re.sub(rule.pattern, rule.replacement, text)
                else:
                    text = text.replace(rule.pattern, rule.replacement)
            except re.error:
                # 正则表达式错误，跳过此规则
                continue
        return text

    async def split_by_speech_rules(self, text: str) -> List[Tuple[str, Optional[int], Optional[str]]]:
        """
        根据朗读规则分割文本
        使用 JavaScript 引擎执行朗读规则代码
        返回: [(文本片段, 配置ID, 标签), ...]
        配置ID 为 None 表示使用默认配置
        """
        if not self._speech_rules:
            return [(text, None, None)]
        
        segments: List[Tuple[str, Optional[int], Optional[str]]] = []
        
        for rule in self._speech_rules:
            if not rule.code:
                continue
            
            try:
                # 通过 JS 引擎执行朗读规则的 split 方法
                #朗读规则应该返回分割后的文本段落和对应的标签
                result = await PluginEngine.execute_async(
                    rule.rule_id, 
                    rule.code, 
                    {},  # 朗读规则不需要用户变量
                    'handleText',
                    text
                )
                
                if result and isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            segment_text = item.get('text', '')
                            tag = item.get('tag')
                            # 根据标签获取配置 ID（如果有映射）
                            config_id = self._get_config_id_for_tag(rule, tag)
                            if segment_text:
                                segments.append((segment_text, config_id, tag))
                        elif isinstance(item, str):
                            segments.append((item, None, None))    # 如果成功处理，返回结果
                    if segments:
                        return segments
                        
            except Exception as e:
                # 规则执行失败，跳过
                print(f"朗读规则 {rule.name} 执行失败: {e}")
                continue
        
        # 没有规则匹配，返回原文
        return [(text, None, None)]

    def _get_config_id_for_tag(self, rule: SpeechRule, tag: Optional[str]) -> Optional[int]:
        """根据标签获取配置 ID"""
        if not tag or not rule.tags:
            return None
        # tags 格式: {tag: config_id} 或 {tag: name}
        # 这里假设 tags 中存储的是配置 ID
        tag_value = rule.tags.get(tag)
        if isinstance(tag_value, int):
            return tag_value
        return None

    def split_sentences(self, text: str, max_length: int = 500) -> List[str]:
        """
        分割长文本为句子
        """
        # 按标点分割
        delimiters = r'[。！？.!?；;\n]'
        sentences = re.split(f'({delimiters})', text)
        
        result = []
        current = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            delimiter = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            if len(current) + len(sentence) + len(delimiter) <= max_length:
                current += sentence + delimiter
            else:
                if current:
                    result.append(current)
                if len(sentence) > max_length:
                    # 超长句子按字数切分
                    for j in range(0, len(sentence), max_length):
                        result.append(sentence[j:j + max_length])
                    current = ""
                else:
                    current = sentence + delimiter
        
        if current:
            result.append(current)
        
        return result

    async def process_text(self, text: str, apply_replace: bool = True) -> str:
        """处理文本 (应用替换规则)"""
        await self.load_rules()
        
        if apply_replace:
            text = self.apply_replace_rules(text)
        
        return text