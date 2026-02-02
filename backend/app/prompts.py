"""Prompt Management System for Stock Analysis

This module provides prompt templates for different analysis scenarios:
- Market trend analysis
- Individual stock analysis
- Stock + sector comparison analysis
- Market sentiment analysis

Features:
- Parameterized prompts with dynamic data injection
- Version control for prompts
- Output format specification
- Token usage optimization
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class PromptVersion(str, Enum):
    """Prompt version identifiers"""
    V1_0 = "v1.0"
    V1_1 = "v1.1"
    V2_0 = "v2.0"


class AnalysisMode(str, Enum):
    """Analysis mode types"""
    SHORT_TERM = "短线T+1"  # Short-term T+1 trading
    MEDIUM_TERM = "中线"     # Medium-term trading
    LONG_TERM = "长线"       # Long-term investment
    MARKET_OVERVIEW = "大盘分析"  # Market overview
    SENTIMENT = "情绪分析"   # Sentiment analysis


@dataclass
class PromptTemplate:
    """Prompt template with versioning and metadata"""
    name: str
    version: PromptVersion
    system_prompt: str
    user_template: str
    description: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    output_format: str = "text"  # text, json, structured
    tags: List[str] = field(default_factory=list)
    
    def render(self, **kwargs) -> Tuple[str, List[Dict[str, str]]]:
        """Render the prompt template with provided parameters
        
        Args:
            **kwargs: Parameters to inject into the template
            
        Returns:
            Tuple of (rendered_system_prompt, messages_list)
        """
        # Render system prompt
        rendered_system = self._render_text(self.system_prompt, **kwargs)
        
        # Render user template
        rendered_user = self._render_text(self.user_template, **kwargs)
        
        # Return formatted messages for LLM
        messages = [
            {"role": "system", "content": rendered_system},
            {"role": "user", "content": rendered_user}
        ]
        
        return rendered_system, messages
    
    def _render_text(self, template: str, **kwargs) -> str:
        """Render a template string with parameters"""
        result = template
        for key, value in kwargs.items():
            # Handle different value types
            if isinstance(value, list):
                formatted_value = self._format_list(value)
            elif isinstance(value, dict):
                formatted_value = self._format_dict(value)
            elif isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, datetime):
                formatted_value = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_value = str(value)
            
            # Replace placeholders
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, formatted_value)
        
        return result
    
    def _format_list(self, items: List[Any]) -> str:
        """Format a list for display"""
        if not items:
            return "无数据"
        if len(items) == 1:
            return str(items[0])
        lines = []
        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                lines.append(f"{i}. {self._format_dict(item)}")
            else:
                lines.append(f"{i}. {item}")
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format a dictionary for display"""
        if not data:
            return "无数据"
        lines = []
        for key, value in data.items():
            key_display = key.replace("_", " ").title()
            if isinstance(value, list):
                value_str = self._format_list(value)
            elif isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            lines.append(f"{key_display}: {value_str}")
        return "\n".join(lines)
    
    def estimate_token_count(self, **kwargs) -> int:
        """Estimate token count for the rendered prompt"""
        _, messages = self.render(**kwargs)
        # Rough estimate: 4 characters per token
        total_chars = sum(len(m["content"]) for m in messages)
        return total_chars // 4


@dataclass
class PromptManager:
    """Manager for prompt templates with versioning and selection"""
    
    # Version tracking
    _current_version: PromptVersion = PromptVersion.V1_0
    _version_history: Dict[PromptVersion, Dict[str, PromptTemplate]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize prompt templates"""
        self._templates: Dict[str, Dict[PromptVersion, PromptTemplate]] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register all default prompt templates"""
        # Market Trend Analysis Prompt
        self.register_template(self._create_market_trend_prompt())
        
        # Individual Stock Analysis Prompt
        self.register_template(self._create_stock_analysis_prompt())
        
        # Stock + Sector Comparison Prompt
        self.register_template(self._create_sector_comparison_prompt())
        
        # Market Sentiment Analysis Prompt
        self.register_template(self._create_sentiment_analysis_prompt())
    
    def _create_market_trend_prompt(self) -> PromptTemplate:
        """Create market trend analysis prompt"""
        return PromptTemplate(
            name="market_trend_analysis",
            version=PromptVersion.V1_0,
            description="大盘走势分析提示词",
            system_prompt="""你是一位专业的股票分析师，专注于中国A股市场的大盘走势分析。

## 分析原则
1. 客观中立，基于数据说话
2. 关注技术面与基本面结合
3. 识别关键支撑位和压力位
4. 给出明确的投资建议（买入/卖出/持有）
5. 风险提示要到位

## 分析框架
- 趋势判断：上涨/下跌/震荡
- 支撑位与压力位
- 成交量分析
- 技术指标信号
- 资金流向
- 风险评估

## 输出要求
请按照以下JSON格式输出分析结果：
```json
{
    "trend": "上涨/下跌/震荡",
    "support_levels": ["支撑位1", "支撑位2"],
    "resistance_levels": ["压力位1", "压力位2"],
    "volume_analysis": "成交量分析描述",
    "technical_indicators": {
        "macd": "MACD信号描述",
        "kdj": "KDJ信号描述", 
        "rsi": "RSI值及信号"
    },
    "fund_flow": "资金流向分析",
    "risk_level": "高/中/低",
    "investment_advice": "买入/卖出/持有",
    "confidence_score": 0.0-1.0,
    "reasoning": "详细分析理由"
}
```""",
            user_template="""请分析当前大盘走势：

## 指数信息
- 指数代码: {index_code}
- 指数名称: {index_name}
- 当前点位: {current_price}
- 涨跌幅: {change_percent}%

## K线数据（最近{days}天）
{kline_data}

## 技术指标
{indicators_data}

## 资金流向
{fund_flow_data}

## 涨停/跌停统计
- 涨停家数: {limit_up_count}
- 跌停家数: {limit_down_count}

请基于以上数据给出大盘走势分析报告。""",
            max_tokens=8192,
            temperature=0.3,
            output_format="json",
            tags=["大盘", "技术分析", "趋势判断"]
        )
    
    def _create_stock_analysis_prompt(self) -> PromptTemplate:
        """Create individual stock analysis prompt (Short-term T+1 focus)"""
        return PromptTemplate(
            name="stock_analysis_short_term",
            version=PromptVersion.V1_0,
            description="短线T+1个股分析提示词",
            system_prompt="""你是一位专业的股票分析师，专注于短线T+1交易的个股分析。

## 短线T+1分析原则
1. 重点关注当日涨跌停板情况
2. 分析资金流向和主力意图
3. 关注成交量变化和换手率
4. 技术指标超买超卖判断
5. 结合板块热点轮动
6. 设定明确的止损止盈位

## 短线交易信号
- 买入信号：放量突破、主力净流入、指标金叉
- 卖出信号：缩量下跌、主力净流出、指标死叉
- 止损位：买入价下跌5-8%
- 止盈位：买入价上涨10-15%或次日冲高

## 输出要求
请按照以下JSON格式输出分析结果：
```json
{{
    "stock_code": "股票代码",
    "stock_name": "股票名称",
    "analysis_mode": "短线T+1",
    "trend": "强势/弱势/震荡",
    "technical_score": 0.0-100,
    "fund_flow_score": 0.0-100,
    "hot_score": 0.0-100,
    "overall_score": 0.0-100,
    "trading_signal": "买入/卖出/持有/观望",
    "entry_price": "建议买入价格区间",
    "stop_loss": "止损价格",
    "take_profit": "止盈价格",
    "holding_period": "建议持有天数",
    "risk_level": "高/中/低",
    "key_indicators": {{
        "price": "当前价格",
        "change": "涨跌幅",
        "volume_ratio": "量比",
        "turnover_rate": "换手率",
        "macd": "MACD状态",
        "kdj": "KDJ状态",
        "rsi": "RSI值"
    }},
    "reasoning": "详细分析理由",
    "risk_warning": "风险提示"
}}
```""",
            user_template="""请分析以下股票（{analysis_mode}模式）：

## 股票基本信息
- 股票代码: {stock_code}
- 股票名称: {stock_name}
- 当前价格: {current_price}元
- 涨跌幅: {change_percent}%
- 涨跌额: {change_amount}元

## 日K线数据（最近{days}天）
{kline_data}

## 技术指标
{indicators_data}

## 资金流向
{fund_flow_data}

## 基本面数据
{company_info}

## 相关新闻
{news_data}

## 所属板块
{sector_info}

请给出{analysis_mode}交易建议，重点关注明日T+1操作策略。""",
            max_tokens=8192,
            temperature=0.3,
            output_format="json",
            tags=["个股", "短线T+1", "技术分析", "买卖信号"]
        )
    
    def _create_sector_comparison_prompt(self) -> PromptTemplate:
        """Create stock + sector comparison prompt"""
        return PromptTemplate(
            name="sector_comparison",
            version=PromptVersion.V1_0,
            description="个股+板块对比分析提示词",
            system_prompt="""你是专业的股票分析师，擅长进行个股与板块的对比分析。

## 分析框架
1. 个股与板块走势对比（相对强度）
2. 个股在板块中的位置（领涨/跟涨/补涨/领跌）
3. 板块资金流向对个股的影响
4. 板块轮动机会识别

## 相对强度计算
- 个股涨幅 > 板块涨幅 → 相对强度 +
- 个股涨幅 < 板块涨幅 → 相对强度 -

## 输出要求
请按照以下JSON格式输出：
```json
{
    "stock_code": "股票代码",
    "stock_name": "股票名称",
    "sector_name": "板块名称",
    "relative_strength": "强/弱/同步",
    "relative_change": 相对涨跌幅差异,
    "sector_rank": 板块内排名,
    "sector_trend": "上涨/下跌/震荡",
    "stock_vs_sector": "领涨/跟涨/补涨/领跌/抗跌",
    "comparison_points": [
        "对比点1",
        "对比点2"
    ],
    "sector_rotation_outlook": "板块轮动展望",
    "investment_advice": "操作建议",
    "confidence_score": 0.0-1.0
}
```""",
            user_template="""请分析{stock_code}与{sector_name}板块的对比：

## 个股信息
{stock_info}

## 板块信息
{sector_info}

## 个股K线数据
{stock_kline}

## 板块K线数据
{sector_kline}

## 资金流向对比
{fund_flow_comparison}

请给出个股相对于板块的表现分析和操作建议。""",
            max_tokens=8192,
            temperature=0.3,
            output_format="json",
            tags=["板块对比", "相对强度", "轮动分析"]
        )
    
    def _create_sentiment_analysis_prompt(self) -> PromptTemplate:
        """Create market sentiment analysis prompt"""
        return PromptTemplate(
            name="market_sentiment_analysis",
            version=PromptVersion.V1_0,
            description="市场情绪分析提示词",
            system_prompt="""你是专业的市场情绪分析师。

## 情绪分析维度
1. 涨跌停比（市场情绪温度计）
2. 成交量变化（增量/缩量/平量）
3. 资金流向（主力/散户）
4. 涨跌幅分布（集中度/离散度）
5. 板块轮动速度
6. 消息面影响

## 情绪等级
- 狂热：涨停潮、成交量激增、场外资金涌入
- 乐观：涨多跌少、量价配合
- 中性：涨跌互现、量能平稳
- 悲观：跌多涨少、量能萎缩
- 恐慌：跌停潮、成交量放大、恐慌抛售

## 输出要求
请按照以下JSON格式输出：
```json
{
    "sentiment_level": "狂热/乐观/中性/悲观/恐慌",
    "sentiment_score": 0.0-100,
    "market_temperature": "高/中/低",
    "bull_bear_ratio": "多空比",
    "volume_trend": "放量/缩量/平量",
    "fund_flow_trend": "流入/流出/平衡",
    "hot_sectors": ["热点板块1", "热点板块2"],
    "cold_sectors": ["冷门板块1", "冷门板块2"],
    "rotation_speed": "快/中/慢",
    "risk_awareness": "高/中/低",
    "trading_recommendation": "积极/稳健/保守/观望",
    "reasoning": "分析理由",
    "historical_comparison": "与历史对比"
}
```""",
            user_template="""请分析当前市场情绪：

## 整体市场数据
{market_overview}

## 涨跌停统计
{limit_up_down_data}

## 成交量数据
{volume_data}

## 资金流向
{fund_flow_data}

## 涨跌幅分布
{change_distribution}

## 板块轮动
{sector_rotation}

请给出市场情绪分析和交易策略建议。""",
            max_tokens=8192,
            temperature=0.3,
            output_format="json",
            tags=["市场情绪", "多空分析", "风险预警"]
        )
    
    def register_template(self, template: PromptTemplate):
        """Register a prompt template"""
        if template.name not in self._templates:
            self._templates[template.name] = {}
        self._templates[template.name][template.version] = template
        
        # Track version history
        if template.version not in self._version_history:
            self._version_history[template.version] = {}
        self._version_history[template.version][template.name] = template
    
    def get_template(self, name: str, version: Optional[PromptVersion] = None) -> Optional[PromptTemplate]:
        """Get a prompt template by name and version"""
        if name not in self._templates:
            return None
        
        versions = self._templates[name]
        
        if version is None:
            # Return latest version
            return max(versions.values(), key=lambda t: t.version)
        
        return versions.get(version)
    
    def get_latest_version(self, name: str) -> Optional[PromptVersion]:
        """Get the latest version of a template"""
        template = self.get_template(name)
        return template.version if template else None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all registered templates"""
        result = []
        for name, versions in self._templates.items():
            latest = max(versions.values(), key=lambda t: t.version)
            result.append({
                "name": name,
                "description": latest.description,
                "version": latest.version.value,
                "tags": latest.tags,
                "output_format": latest.output_format
            })
        return result
    
    def render_prompt(
        self, 
        name: str, 
        version: Optional[PromptVersion] = None,
        **kwargs
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Render a prompt template with parameters
        
        Args:
            name: Template name
            version: Specific version or None for latest
            **kwargs: Parameters to inject
            
        Returns:
            Tuple of (rendered_system_prompt, messages_list)
        """
        template = self.get_template(name, version)
        if template is None:
            raise ValueError(f"Template '{name}' not found")
        
        # Check token count
        estimated_tokens = template.estimate_token_count(**kwargs)
        if estimated_tokens > template.max_tokens:
            import warnings
            warnings.warn(
                f"Template '{name}' estimated tokens ({estimated_tokens}) "
                f"exceeds max_tokens ({template.max_tokens})"
            )
        
        return template.render(**kwargs)
    
    def get_prompt_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a prompt template"""
        template = self.get_template(name)
        if template is None:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "version": template.version.value,
            "max_tokens": template.max_tokens,
            "temperature": template.temperature,
            "output_format": template.output_format,
            "tags": template.tags,
            "available_versions": [
                v.value for v in self._templates[name].keys()
            ]
        }


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def render_market_analysis_prompt(
    index_code: str,
    index_name: str,
    current_price: float,
    change_percent: float,
    kline_data: str,
    indicators_data: str,
    fund_flow_data: str,
    limit_up_count: int,
    limit_down_count: int,
    days: int = 30
) -> Tuple[str, List[Dict[str, str]]]:
    """Render market trend analysis prompt"""
    manager = get_prompt_manager()
    return manager.render_prompt(
        "market_trend_analysis",
        index_code=index_code,
        index_name=index_name,
        current_price=current_price,
        change_percent=change_percent,
        kline_data=kline_data,
        indicators_data=indicators_data,
        fund_flow_data=fund_flow_data,
        limit_up_count=limit_up_count,
        limit_down_count=limit_down_count,
        days=days
    )


def render_stock_analysis_prompt(
    stock_code: str,
    stock_name: str,
    current_price: float,
    change_percent: float,
    change_amount: float,
    kline_data: str,
    indicators_data: str,
    fund_flow_data: str,
    company_info: str,
    news_data: str,
    sector_info: str,
    analysis_mode: str = "短线T+1",
    days: int = 30
) -> Tuple[str, List[Dict[str, str]]]:
    """Render stock analysis prompt"""
    manager = get_prompt_manager()
    return manager.render_prompt(
        "stock_analysis_short_term",
        stock_code=stock_code,
        stock_name=stock_name,
        current_price=current_price,
        change_percent=change_percent,
        change_amount=change_amount,
        kline_data=kline_data,
        indicators_data=indicators_data,
        fund_flow_data=fund_flow_data,
        company_info=company_info,
        news_data=news_data,
        sector_info=sector_info,
        analysis_mode=analysis_mode,
        days=days
    )


def render_sentiment_analysis_prompt(
    market_overview: str,
    limit_up_down_data: str,
    volume_data: str,
    fund_flow_data: str,
    change_distribution: str,
    sector_rotation: str
) -> Tuple[str, List[Dict[str, str]]]:
    """Render market sentiment analysis prompt"""
    manager = get_prompt_manager()
    return manager.render_prompt(
        "market_sentiment_analysis",
        market_overview=market_overview,
        limit_up_down_data=limit_up_down_data,
        volume_data=volume_data,
        fund_flow_data=fund_flow_data,
        change_distribution=change_distribution,
        sector_rotation=sector_rotation
    )


# Test function
def test_prompt_templates():
    """Test prompt template rendering"""
    print("Testing Prompt Templates...")
    print("=" * 50)
    
    manager = get_prompt_manager()
    
    # List all templates
    print("\nAvailable Templates:")
    for template_info in manager.list_templates():
        print(f"  - {template_info['name']}: {template_info['description']}")
        print(f"    Version: {template_info['version']}")
        print(f"    Tags: {template_info['tags']}")
    
    # Test market analysis prompt
    print("\n" + "=" * 50)
    print("Testing Market Trend Analysis Prompt:")
    system_msg, messages = render_market_analysis_prompt(
        index_code="000001",
        index_name="上证指数",
        current_price=3200.50,
        change_percent=1.25,
        kline_data="""日期        开盘      收盘      涨跌
2026-01-27  3180.25  3195.80  +0.45%
2026-01-28  3195.80  3210.30  +0.52%
2026-01-29  3210.30  3225.60  +0.48%""",
        indicators_data="MACD: 金叉, KDJ: 超买, RSI: 68",
        fund_flow_data="主力净流入: +25.6亿",
        limit_up_count=85,
        limit_down_count=5,
        days=3
    )
    
    print(f"System message length: {len(system_msg)} chars")
    print(f"Messages count: {len(messages)}")
    print(f"User message length: {len(messages[1]['content'])} chars")
    
    # Test stock analysis prompt
    print("\n" + "=" * 50)
    print("Testing Stock Analysis Prompt:")
    system_msg, messages = render_stock_analysis_prompt(
        stock_code="600000",
        stock_name="浦发银行",
        current_price=10.25,
        change_percent=2.15,
        change_amount=0.22,
        kline_data="""日期        开盘      收盘      涨跌
2026-01-27  10.05    10.08    +0.30%
2026-01-28  10.08    10.12    +0.40%
2026-01-29  10.12    10.25    +1.28%""",
        indicators_data="MACD: 底背离, KDJ: 金叉, RSI: 55",
        fund_flow_data="主力净流入: +1.2亿",
        company_info="市盈率: 5.2, 市净率: 0.8",
        news_data="暂无重大新闻",
        sector_info="银行板块: +1.5%",
        days=3
    )
    
    print(f"System message length: {len(system_msg)} chars")
    print(f"User message length: {len(messages[1]['content'])} chars")
    
    print("\n" + "=" * 50)
    print("All prompt templates tested successfully!")
    
    return True


if __name__ == "__main__":
    test_prompt_templates()
