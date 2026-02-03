"""
Prompt Management System for Stock Analysis
============================================

This module provides prompt templates for different analysis scenarios:
- Market trend analysis (大盘走势分析)
- Individual stock analysis (个股分析)
- Stock + sector comparison analysis (个股+板块对比)
- Market sentiment analysis (市场情绪分析)
- Short-term T+1 analysis (短线T+1)
- Band trading analysis (波段交易分析)
- Intraday analysis (分时走势分析)
- Speculative arbitrage analysis (投机套利分析)
- N+1+N limit-up reversal analysis (N+1+N涨停反包分析)
- Company valuation analysis (公司估值分析)

Features:
- Parameterized prompts with dynamic data injection
- Version control for prompts
- Output format specification
- Token usage optimization
- DataFrame to Markdown conversion

Version History:
- v1.0 (2026-01-21): Initial version with basic templates
- v1.1 (2026-02-02): Added 9 analysis mode functions, DataFrame conversion, detailed prompts

Author: AI Assistant
"""

import json
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

# Try to import pandas for DataFrame conversion
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    warnings.warn("pandas not installed, DataFrame conversion disabled")


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
    BAND_TRADING = "波段交易"  # Band trading
    INTRADAY = "分时走势"     # Intraday analysis
    SPECULATIVE = "投机套利"   # Speculative arbitrage
    LIMIT_UP_REVERSAL = "涨停反包"  # N+1+N limit-up reversal
    VALUATION = "公司估值"     # Company valuation


# =============================================================================
# DataFrame Conversion Utilities
# =============================================================================

def dataframe_to_markdown(df: Any, max_rows: int = 50) -> str:
    """Convert DataFrame to Markdown table format
    
    Args:
        df: pandas DataFrame or object with to_markdown() method
        max_rows: Maximum number of rows to display
        
    Returns:
        Markdown formatted table string
    """
    if df is None:
        return "无数据"
    
    # If object has to_markdown method (pandas 1.3.0+)
    if hasattr(df, 'to_markdown') and callable(getattr(df, 'to_markdown')):
        try:
            return df.to_markdown(index=False)
        except Exception:
            pass
    
    # Fallback: convert to markdown manually
    if not HAS_PANDAS:
        return str(df)
    
    try:
        if not isinstance(df, pd.DataFrame):
            return str(df)
        
        # Limit rows
        if len(df) > max_rows:
            df = df.head(max_rows)
        
        # Handle NaN values
        df = df.fillna('')
        
        # Build markdown table
        if df.empty:
            return "无数据"
        
        # Get headers
        headers = list(df.columns)
        
        # Get rows
        rows = df.values.tolist()
        
        # Format each row
        formatted_rows = []
        for row in rows:
            formatted_row = []
            for val in row:
                if isinstance(val, float):
                    formatted_row.append(f"{val:.2f}")
                elif isinstance(val, datetime):
                    formatted_row.append(val.strftime("%Y-%m-%d"))
                elif val is None:
                    formatted_row.append("-")
                else:
                    formatted_row.append(str(val))
            formatted_rows.append(formatted_row)
        
        # Build markdown table
        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in formatted_rows:
                if i < len(row):
                    max_width = max(max_width, len(row[i]))
            col_widths.append(max_width + 2)
        
        # Build header row
        header_row = "|"
        for i, header in enumerate(headers):
            header_row += f" {header.ljust(col_widths[i] - 2)} |"
        
        # Build separator row
        separator = "|"
        for width in col_widths:
            separator += "-" * (width - 2) + " |"
        
        # Build data rows
        data_rows = []
        for row in formatted_rows:
            data_row = "|"
            for i, val in enumerate(row):
                if i < len(col_widths):
                    data_row += f" {val.ljust(col_widths[i] - 2)} |"
                else:
                    data_row += f" {val} |"
            data_rows.append(data_row)
        
        return header_row + "\n" + separator + "\n" + "\n".join(data_rows)
        
    except Exception as e:
        return f"数据转换错误: {str(e)}"


def format_trading_advice(advice: Dict[str, Any]) -> str:
    """Format trading advice output"""
    if not advice:
        return "无法解析具体交易建议"
    
    return f"""
具体交易建议:
------------------------
交易方向: {advice.get('direction', '未指定')}
目标价格: {advice.get('target_price', '未指定')} 元
交易数量: {advice.get('quantity', '未指定')} 股
止损价格: {advice.get('stop_loss', '未指定')} 元
止盈目标: {advice.get('take_profit', '未指定')} 元
持仓时间: {advice.get('holding_period', '未指定')} 个交易日
风险等级: {advice.get('risk_level', '未指定')}
------------------------"""


# =============================================================================
# PromptTemplate and PromptManager Classes
# =============================================================================

@dataclass
class PromptTemplate:
    """Prompt template with versioning and metadata
    
    Version: v1.1 (2026-02-02)
    """
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
            elif hasattr(value, 'to_markdown') and callable(getattr(value, 'to_markdown')):
                formatted_value = dataframe_to_markdown(value)
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
        """Estimate token count for the rendered prompt
        
        Version: v1.0 (2026-01-21)
        """
        _, messages = self.render(**kwargs)
        # Rough estimate: 4 characters per token
        total_chars = sum(len(m["content"]) for m in messages)
        return total_chars // 4


@dataclass
class PromptManager:
    """Manager for prompt templates with versioning and selection
    
    Version: v1.1 (2026-02-02)
    """
    
    # Version tracking
    _current_version: PromptVersion = PromptVersion.V1_0
    _version_history: Dict[PromptVersion, Dict[str, PromptTemplate]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize prompt templates
        
        Version: v1.1 (2026-02-02) - Added all 9 analysis mode templates
        """
        self._templates: Dict[str, Dict[PromptVersion, PromptTemplate]] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register all default prompt templates
        
        Version: v1.1 (2026-02-02) - Registered all 4 template types
        """
        # Market Trend Analysis Prompt
        self.register_template(self._create_market_trend_prompt())
        
        # Individual Stock Analysis Prompt
        self.register_template(self._create_stock_analysis_prompt())
        
        # Stock + Sector Comparison Prompt
        self.register_template(self._create_sector_comparison_prompt())
        
        # Market Sentiment Analysis Prompt
        self.register_template(self._create_sentiment_analysis_prompt())
    
    def _create_market_trend_prompt(self) -> PromptTemplate:
        """Create market trend analysis prompt
        
        Version: v1.0 (2026-01-21)
        """
        return PromptTemplate(
            name="market_trend_analysis",
            version=PromptVersion.V1_0,
            description="大盘走势分析提示词",
            system_prompt="""你是一位专业的股票分析师，专注于中国A股市场的大盘走势分析。

## 分析原则
1. 客观中立，基于数据说话
2. 关注技术面与基本面结合
3. 识别关键支撑位和压力位
4. 给出明确的投资建议（买入/5. 风险提示要到位

## 分析框架
- 趋势判断卖出/持有）
：上涨/下跌/震荡
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
        """Create individual stock analysis prompt (Short-term T+1 focus)
        
        Version: v1.0 (2026-01-21)
        """
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
        """Create stock + sector comparison prompt
        
        Version: v1.0 (2026-01-21)
        """
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
        """Create market sentiment analysis prompt
        
        Version: v1.0 (2026-01-21)
        """
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
        """Register a prompt template
        
        Version: v1.0 (2026-01-21)
        """
        if template.name not in self._templates:
            self._templates[template.name] = {}
        self._templates[template.name][template.version] = template
        
        # Track version history
        if template.version not in self._version_history:
            self._version_history[template.version] = {}
        self._version_history[template.version][template.name] = template
    
    def get_template(self, name: str, version: Optional[PromptVersion] = None) -> Optional[PromptTemplate]:
        """Get a prompt template by name and version
        
        Version: v1.0 (2026-01-21)
        """
        if name not in self._templates:
            return None
        
        versions = self._templates[name]
        
        if version is None:
            # Return latest version
            return max(versions.values(), key=lambda t: t.version)
        
        return versions.get(version)
    
    def get_latest_version(self, name: str) -> Optional[PromptVersion]:
        """Get the latest version of a template
        
        Version: v1.0 (2026-01-21)
        """
        template = self.get_template(name)
        return template.version if template else None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all registered templates
        
        Version: v1.0 (2026-01-21)
        """
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
        
        Version: v1.0 (2026-01-21)
        """
        template = self.get_template(name, version)
        if template is None:
            raise ValueError(f"Template '{name}' not found")
        
        # Check token count
        estimated_tokens = template.estimate_token_count(**kwargs)
        if estimated_tokens > template.max_tokens:
            warnings.warn(
                f"Template '{name}' estimated tokens ({estimated_tokens}) "
                f"exceeds max_tokens ({template.max_tokens})"
            )
        
        return template.render(**kwargs)
    
    def get_prompt_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a prompt template
        
        Version: v1.0 (2026-01-21)
        """
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


# =============================================================================
# Global Prompt Manager Instance
# =============================================================================

_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the global prompt manager instance
    
    Version: v1.0 (2026-01-21)
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


# =============================================================================
# Prompt Building Functions (build_* format as per tech-stack.md)
# =============================================================================

def build_analysis_prompt(stock_info, stock_status, news_list, financial_data) -> str:
    """构建分析提示词 - 基础面技术面综合分析
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_analysis_prompt() - 个股基础面技术面综合分析
    """
    # Convert DataFrame to markdown
    stock_status_md = dataframe_to_markdown(stock_status)
    financial_data_md = dataframe_to_markdown(financial_data) if financial_data else "无财务数据"
    
    prompt = f"""请分析以下股票的投资价值并给出具体的交易建议：

1. 股票基本信息:
代码: {stock_info.get('code', stock_info.get('stock_code', 'N/A'))}
名称: {stock_info.get('name', stock_info.get('stock_name', 'N/A'))}
所属行业: {stock_info.get('business', stock_info.get('industry', 'N/A'))}

2. 股票近7日成交数据信息：
{stock_status_md}

3. 最新相关新闻:
"""

    if isinstance(news_list, list):
        for i, news in enumerate(news_list[:3], 1):
            prompt += f"""
新闻{i}:
标题: {news.get('title') or news.get('news_title', 'N/A')}
时间: {news.get('time') or news.get('publish_time', 'N/A')}
内容: {news.get('content') or news.get('news_content', 'N/A')[:200]}
"""
    else:
        prompt += f"\n{news_list}\n"

    prompt += f"""
4. 主要财务指标:
{financial_data_md}

请从以下几个方面进行分析并给出具体建议：

1. 公司基本面分析
2. 行业发展前景
3. 最新消息影响
4. 财务指标分析
5. 具体交易建议

你必须严格按照以下格式给出交易建议（包含所有字段且不能为空）：

交易建议：
交易方向：[买入/卖出]
目标价格：[具体数字，单位：元]
交易数量：[具体数字，单位：股]
止损价格：[具体数字，单位：元]
止盈目标：[具体数字，单位：元]
持仓时间：[具体数字，单位：个交易日]
风险等级：[高/中/低]

注意：
1. 所有数值必须是具体的数字，不能使用范围或描述性语言
2. 价格必须精确到小数点后两位
3. 交易数量必须是100的整数倍
4. 持仓时间必须是具体的交易日数
5. 必须包含上述所有字段，且格式要完全一致

请先给出分析，然后在最后给出严格按照上述格式的交易建议。
"""
    return prompt


def market_analysis_prompt(news_list: List[str], topk: float = 10) -> str:
    """市场新闻挖掘提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: market_analysis_prompt() - 市场新闻挖掘
    """
    prompt = f"""请分析以下最新市场新闻,并推荐3-5只值得关注的股票：
1. 最新市场新闻：
"""
    if isinstance(news_list, list):
        for i, news in enumerate(news_list[:int(topk)], 1):
            if isinstance(news, dict):
                prompt += f"""
新闻{i}:
标题: {news.get('title', 'N/A')}
时间: {news.get('time', 'N/A') or news.get('publish_time', 'N/A')}
内容: {news.get('content', 'N/A') or news.get('news_content', 'N/A')[:200]}
"""
            else:
                prompt += f"\n新闻{i}: {news}\n"
    else:
        prompt += f"\n{news_list}\n"

    prompt += """
请根据以上新闻分析当前市场环境，并推荐3-5只值得关注的股票。
对于每只推荐的股票，请提供：
1. 股票代码（格式为6位数字，如000001、600000等）
2. 推荐理由
3. 所属行业

注意：请不要假设或猜测股票的当前价格，我们会在后续分析中获取实时数据。
"""
    return prompt


def recommend_prompt(stock_details) -> str:
    """股票推荐分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: recommend_prompt() - 股票推荐分析
    """
    if isinstance(stock_details, (dict, list)):
        details_str = json.dumps(stock_details, ensure_ascii=False, indent=2)
    else:
        details_str = str(stock_details)
    
    prompt = f"""请对以下股票进行深入分析并给出具体交易建议：

推荐股票详细信息：
{details_str}

请针对每只股票给出以下分析：
1. 基本面分析 - 基于公司情况、行业前景等
2. 技术面分析 - 基于提供的技术指标
3. 市场情绪分析 - 基于相关新闻
4. 风险提示 - 明确指出投资风险
5. 具体交易建议

交易建议必须包含:
- 建议买入价格区间（基于技术分析给出合理区间，不要假设当前价格）
- 止损位（明确的价格点位）
- 止盈目标（明确的价格点位）
- 建议持仓时间
- 风险等级（高/中/低）

重要提示：
1. 不要假设或猜测当前股票价格，请基于提供的技术指标进行分析
2. 给出的买入价格区间必须合理，与技术指标相符
3. 交易建议必须具体、可执行，不要使用模糊表述
"""
    return prompt


def build_guzhi_prompt(infos: str, stock_details: List[dict], pred_logit: str, 
                       guzhi_method: str, other_infos: str) -> str:
    """公司估值分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_guzhi_prompt() - 公司估值分析
    """
    prompt = f"""以下是获取到的信息流：
{infos}

从信息流中挖掘到的个股信息如下:
"""
    for i, stock_detail in enumerate(stock_details, 1):
        prompt += f"""
个股{i}
基本信息: {stock_detail.get("basic_info", "N/A")}
近7日指标数据:
{stock_detail.get("technical_indicators", "N/A")}

"""

    prompt += f"""
根据信息流挖掘的逻辑分类为:{pred_logit},
对应的估值方式是: {guzhi_method}
潜在涨幅计算方法：未来估值/当下估值-1

其他信息:
{other_infos}

请从以下几个方面进行分析并给出具体建议：

1. 公司基本面分析
2. 行业发展前景
3.产能、产量、 过去1年售价、销售成本、未来新增产能
4. 行业格局与各家份额
5. 潜在涨幅预估
6. 具体交易建议

你必须严格按照以下格式给出交易建议（包含所有字段且不能为空）：

交易建议：
交易方向：[买入/卖出]
目标价格：[具体数字，单位：元]
交易数量：[具体数字，单位：股]
止损价格：[具体数字，单位：元]
止盈目标：[具体数字，单位：元]
持仓时间：[具体数字，单位：个交易日]
风险等级：[高/中/低]
预估涨幅：[百分数]

注意：
1. 所有数值必须是具体的数字，不能使用范围或描述性语言
2. 价格必须精确到小数点后两位
3. 交易数量必须是100的整数倍
4. 持仓时间必须是具体的交易日数
5. 必须包含上述所有字段，且格式要完全一致

请先给出分析，然后在最后给出严格按照上述格式的交易建议。
"""
    return prompt


def build_touji_prompt(stock_info, stock_status, stock_weekly_status, news_list, 
                       dapan, market_activity, concept_name: str = "", 
                       concept_status=None, latest_analysis: str = None) -> str:
    """投机套利分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_touji_prompt() - 投机套利分析
    """
    stock_status_md = dataframe_to_markdown(stock_status)
    stock_weekly_md = dataframe_to_markdown(stock_weekly_status)
    dapan_md = dataframe_to_markdown(dapan)
    market_activity_md = dataframe_to_markdown(market_activity)
    concept_status_md = dataframe_to_markdown(concept_status) if concept_status else "无板块数据"
    
    # Format stock info
    if isinstance(stock_info, dict):
        stock_code = stock_info.get('code', stock_info.get('stock_code', 'N/A'))
        stock_name = stock_info.get('name', stock_info.get('stock_name', 'N/A'))
        business = stock_info.get('business', stock_info.get('industry', 'N/A'))
    else:
        stock_code = stock_name = business = str(stock_info)
    
    prompt = f"""你是一个顶级的投机套利高手，根据如下信息分析标的的套利机会：

1. 标的基本信息:
代码: {stock_code}
名称: {stock_name}
所属行业: {business}

2. 标的近14日成交数据信息：
{stock_status_md}

3. 标的周k线数据如下：
{stock_weekly_md}

4. 最新相关新闻:
"""

    if isinstance(news_list, list):
        for i, news in enumerate(news_list[:2], 1):
            if isinstance(news, dict):
                prompt += f"""
新闻{i}:
标题: {news.get('title', 'N/A')}
时间: {news.get('time', 'N/A')}
内容: {news.get('content', 'N/A')[:200]}
"""
            else:
                prompt += f"\n新闻{i}: {news}\n"

    prompt += f"""
5. 大盘近期情况:
{dapan_md}

6. 赚钱效应分析：
{market_activity_md}

"""
    if concept_name:
        prompt += f"""
7. 概念: {concept_name} 板块近期情况：
{concept_status_md}

"""
    if latest_analysis:
        prompt += f"""
8. 该标的近期技术分析结果如下：
{latest_analysis}
"""
    
    prompt += """
分析上述数据，再根据标的的近期走势，判断标的是否有买点，并给出买卖点以及操作手法。
注意：分析中的数据必须符合事实，特别是需要符合不同日期的历史数据，如最高点，跳空缺口等。
"""
    return prompt


def build_fenshi_prompt(stock_info, stock_status, stock_weekly_status, 
                        dapan, market_activity, stock_fenshi_status) -> str:
    """分时走势分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_fenshi_prompt() - 分时走势分析
    """
    stock_status_md = dataframe_to_markdown(stock_status)
    stock_weekly_md = dataframe_to_markdown(stock_weekly_status)
    dapan_md = dataframe_to_markdown(dapan)
    market_activity_md = dataframe_to_markdown(market_activity)
    stock_fenshi_md = dataframe_to_markdown(stock_fenshi_status)
    
    # Format stock info
    if isinstance(stock_info, dict):
        stock_code = stock_info.get('code', stock_info.get('stock_code', 'N/A'))
        stock_name = stock_info.get('name', stock_info.get('stock_name', 'N/A'))
        business = stock_info.get('business', stock_info.get('industry', 'N/A'))
    else:
        stock_code = stock_name = business = str(stock_info)
    
    prompt = f"""你是一个顶级的股票超短选手(T+1)，根据如下信息分析标的的套利机会：

1. 标的基本信息:
代码: {stock_code}
名称: {stock_name}
所属行业: {business}

2. 标的近14日成交数据信息：
{stock_status_md}

3. 标的周k线数据如下：
{stock_weekly_md}

4. 大盘近期情况:
{dapan_md}

5. 赚钱效应分析：
{market_activity_md}

6. 标的分时走势：
{stock_fenshi_md}

分析上述数据，再根据标的的分时走势，判断标的是否有买点，并给出买卖点以及操作手法。
特别注意：你根据的是标的的分时走势分析，当日收盘时间是15:00，如果第6点给出的最后一个数据不是15:00的，说明当天还未收盘，属于盘中走势。
分析套利机会时应该考虑到这一点，以此判断是否有日内买点。
"""
    return prompt


def build_boduan_prompt(stock_info, financial_status, stock_status, 
                        stock_weekly_status, dapan, concept_name: str = "", 
                        concept_status=None) -> str:
    """波段交易分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_boduan_prompt() - 波段交易分析
    """
    financial_md = dataframe_to_markdown(financial_status)
    stock_status_md = dataframe_to_markdown(stock_status)
    stock_weekly_md = dataframe_to_markdown(stock_weekly_status)
    dapan_md = dataframe_to_markdown(dapan)
    concept_status_md = dataframe_to_markdown(concept_status) if concept_status else "无板块数据"
    
    # Format stock info
    if isinstance(stock_info, dict):
        stock_code = stock_info.get('code', stock_info.get('stock_code', 'N/A'))
        stock_name = stock_info.get('name', stock_info.get('stock_name', 'N/A'))
        business = stock_info.get('business', stock_info.get('industry', 'N/A'))
    else:
        stock_code = stock_name = business = str(stock_info)
    
    prompt = f"""你是一位拥有15年实战经验的顶级股票波段交易专家，擅长结合技术分析和市场情绪捕捉短期趋势。
请以专业交易员的思维框架分析标的的波段机会：

1. 标的基本信息:
代码: {stock_code}
名称: {stock_name}
所属行业: {business}

2. 标的的财务情况：
{financial_md}

3. 标的近期日成交数据信息：
{stock_status_md}

4. 标的周k线数据如下：
{stock_weekly_md}

5. 大盘近期情况:
{dapan_md}
"""

    if concept_name:
        prompt += f"""
6. 概念: {concept_name} 板块近期情况：
{concept_status_md}

"""

    prompt += """
【分析框架】
请按专业顺序评估：
一、趋势判定
1. 多周期共振：周线趋势方向与日线是否一致？
2. 均线系统：当前价格与关键均线的乖离率是否合理？
3. 大盘关联性：个股走势与基准指数的偏离程度

二、波段结构识别
1. 震荡区间：近期是否形成明显支撑/压力位？（标注具体价格区间）
2. 量价配合：上涨放量/下跌缩量特征是否显著？
3. 指标背离：MACD/RSI是否出现底背离或顶背离信号？

三、买卖点策略
1. 理想建仓区域（结合支撑位与风险回报比）
2. 止损位置设置（技术止损与波动率止损双维度）
3. 目标价位测算（基于前高压力、黄金分割位、ATR波动幅度）

四、风险警示
1. 需要重点关注的潜在变盘信号
2. 重大事件时间窗口（如财报披露、限售解禁）
3. 市场流动性风险预警

【输出要求】
用交易员术语呈现结构化分析，关键位置精确到小数点后两位，时间窗口标注具体日期。最后用★符号对机会等级进行1-5星评价。
"""
    return prompt


def build_duanxian_prompt(stock_info, stock_status, stock_weekly_status, 
                          news_list, dapan, market_activity, concept_name: str = "", 
                          concept_status=None) -> str:
    """短线T+1分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_duanxian_prompt() - 短线T+1分析
    """
    stock_status_md = dataframe_to_markdown(stock_status)
    stock_weekly_md = dataframe_to_markdown(stock_weekly_status)
    dapan_md = dataframe_to_markdown(dapan)
    market_activity_md = dataframe_to_markdown(market_activity)
    concept_status_md = dataframe_to_markdown(concept_status) if concept_status is not None and not concept_status.empty else "无板块数据"
    
    # Format stock info
    if isinstance(stock_info, dict):
        stock_code = stock_info.get('code', stock_info.get('stock_code', 'N/A'))
        stock_name = stock_info.get('name', stock_info.get('stock_name', 'N/A'))
        business = stock_info.get('business', stock_info.get('industry', 'N/A'))
    else:
        stock_code = stock_name = business = str(stock_info)
    
    prompt = f"""你是一位拥有15年经验的顶级T+1短线交易员，精通多维度共振策略和量化风控模型。
请基于以下结构化数据，对{stock_code}未来1-5个交易日的投机潜力进行专业分析：
【基础数据层】
1. 标的核心信息：
   代码: {stock_code} | 名称: {stock_name} | 行业: {business}
2. 近期交易数据（日频）：
{stock_status_md}
3. 周K线技术形态：
{stock_weekly_md}
4. 最新市场催化剂：
"""
    
    if isinstance(news_list, list):
        for i, news in enumerate(news_list[:4], 1):
            if isinstance(news, dict):
                prompt += f"""
   新闻{i}: [{news.get('time', 'N/A')}] {news.get('title', 'N/A')}
   关键摘要：{news.get('content', 'N/A')[:200]}...
"""
            else:
                prompt += f"\n   新闻{i}: {news}\n"

    prompt += f"""
5. 大盘环境扫描：
{dapan_md}
6. 市场温度计：
{market_activity_md}
"""
    if concept_name:
        prompt += f"""
7. 板块动能追踪：{concept_name}
{concept_status_md}
"""

    prompt += """
【量化分析框架】
1. 趋势定位系统
   1.1 相对强度矩阵：个股 vs 行业(5日涨跌幅差值+RSI背离度) vs 沪深300(10日波动率差)
   1.2 关键位置标注：当前价格与BOLL(20,2)/MA50/前高的空间距离(%)
   1.3 时间窗口敏感度：距离财报/除权/解禁等事件日历天数
2. 量价动能诊断
   2.1 量能异动系数：(近3日均量/20日均量-1)*100% + 量价背离信号
   2.2 订单流分析：主力资金净流入3日趋势 + 北向资金边际变化
   2.3 波动率预测：ATR(14)当前值 vs 历史分位数 + 隐含波动率偏离度
3. 市场情绪共振
   3.1 舆情热度：百度指数周环比 + 雪球/东方财富讨论量突增幅度
   3.2 板块轮动：行业资金流向排名 + 概念指数相对强度
   3.3 催化剂验证：新闻事件与价格走势的关联性分析
【决策输出要求】
1. 机会评级（三选一，打勾）：
   □ 高确定性机会（概率>70%） | □ 观望信号（概率40-70%） | □ 规避风险（概率<40%）
   评级依据：[必填3个核心指标验证]
2. 精确交易计划：
   入场价位：______元（触发条件：______）
   止损位：______元（最大回撤≤______%）
   目标位：______元（基于ATR测算：______倍ATR）
   持仓周期：预计______个交易日
3. 动态仓位模型：
   凯利公式建议仓位：______% 
   （胜率______% + 赔率______：1 + 风险系数______）
   实际调整仓位：______% （考虑大盘关联度/流动性风险）
4. 实时监控清单：
   指标1：______（预警阈值：______ → 应对方案：______）
   指标2：______（预警阈值：______ → 应对方案：______）
   指标3：______（预警阈值：______ → 应对方案：______）
【风险警示】
• 强制止损纪律：单笔亏损不得超过总资金2%
• 隔夜风险敞口评估：______（高/中/低）
• 流动性风险：当前日均换手率______% vs 需求换手率______%
"""
    return prompt


def build_n1n_prompt(stock_info, stock_zt_info, stock_status, stock_weekly_status, 
                     news_list, dapan, market_activity, concept_name: str = "", 
                     concept_status=None) -> str:
    """N+1+N涨停反包分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: build_n1n_prompt() - N+1+N涨停反包分析
    """
    stock_status_md = dataframe_to_markdown(stock_status)
    stock_weekly_md = dataframe_to_markdown(stock_weekly_status)
    dapan_md = dataframe_to_markdown(dapan)
    market_activity_md = dataframe_to_markdown(market_activity)
    concept_status_md = dataframe_to_markdown(concept_status) if concept_status else "无板块数据"
    
    # Format stock info
    if isinstance(stock_info, dict):
        stock_code = stock_info.get('code', stock_info.get('stock_code', 'N/A'))
        stock_name = stock_info.get('name', stock_info.get('stock_name', 'N/A'))
        business = stock_info.get('business', stock_info.get('industry', 'N/A'))
    else:
        stock_code = stock_name = business = str(stock_info)
    
    # Format limit-up info
    if isinstance(stock_zt_info, dict):
       封板资金 = stock_zt_info.get("封板资金", stock_zt_info.get("limit_up_funds", "N/A"))
       炸板次数 = stock_zt_info.get("炸板次数", stock_zt_info.get("burst_count", "N/A"))
       首次封板时间 = stock_zt_info.get("首次封板时间", stock_zt_info.get("first_limit_time", "N/A"))
       最后封板时间 = stock_zt_info.get("最后封板时间", stock_zt_info.get("last_limit_time", "N/A"))
    else:
       封板资金 = 炸板次数 = 首次封板时间 = 最后封板时间 = str(stock_zt_info)
    
    prompt = f"""你是一位专攻超短反包形态的顶级交易员，当前标的{stock_code}已确认符合N+1+N形态（昨日涨停+今日断板长上影）。
请基于以下数据预测分析反包概率并制定交易方案：
【核心形态数据】
1. 标的基本信息：
    代码: {stock_code} | 名称: {stock_name} | 行业: {business}
    涨停质量：封单额{封板资金}亿 | 炸板次数{炸板次数} | 首次封板时间{首次封板时间} | 最后封板时间{最后封板时间}
2. 关键K线数据：
{stock_status_md}
3. 周线位置定位：
{stock_weekly_md}
4. 个股相关新闻：
"""
    
    if isinstance(news_list, list):
        for i, news in enumerate(news_list[:3], 1):
            if isinstance(news, dict):
                prompt += f"""
   新闻{i}: [{news.get('time', 'N/A')}] {news.get('title', 'N/A')}
   关键摘要：{news.get('content', 'N/A')[:200]}...
"""
            else:
                prompt += f"\n   新闻{i}: {news}\n"

    prompt += f"""
5. 大盘环境：
{dapan_md}
6. 市场温度计：
{market_activity_md}
"""
    if concept_name:
        prompt += f"""
7. 板块详情：{concept_name}
{concept_status_md}
"""

    prompt += """
综合以上数据给出买卖点分析、仓位建议、止损点等，给出相应的理由。
"""
    return prompt


def dapan_analysis_prompt(daily_data, weekly_data, monthly_data) -> str:
    """大盘分析提示词
    
    Version: v1.1 (2026-02-02)
    根据 tech-stack.md 要求: 大盘走势分析
    """
    daily_md = dataframe_to_markdown(daily_data)
    weekly_md = dataframe_to_markdown(weekly_data)
    monthly_md = dataframe_to_markdown(monthly_data)
    
    prompt = f"""你是一个顶级的股票操盘手，请根据大盘的近期日线、周线、月线数据分析大盘走势，
如果有波段做多机会需重点指出，并指出上涨预期点位，压力位支撑位等。
如果有较大下跌风险，需要重点指出，并给出压力位支撑位等。
给出详细分析报告。

1. 大盘的日k线走势如下：
{daily_md}

2. 大盘的周k线走势如下：
{weekly_md}

3. 大盘的月k线走势如下：
{monthly_md}

"""
    return prompt


# =============================================================================
# Convenience Functions (render_* format)
# =============================================================================

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
    """Render market trend analysis prompt
    
    Version: v1.0 (2026-01-21)
    """
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
    """Render stock analysis prompt
    
    Version: v1.0 (2026-01-21)
    """
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
    """Render market sentiment analysis prompt
    
    Version: v1.0 (2026-01-21)
    """
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


# =============================================================================
# Test Function
# =============================================================================

def test_prompt_templates():
    """Test prompt template rendering
    
    Version: v1.1 (2026-02-02)
    """
    print("=" * 60)
    print("Testing Prompt Templates...")
    print("=" * 60)
    
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
    
    # Test DataFrame conversion
    print("\n" + "=" * 50)
    print("Testing DataFrame to Markdown conversion:")
    if HAS_PANDAS:
        test_df = pd.DataFrame({
            '日期': ['2026-01-27', '2026-01-28', '2026-01-29'],
            '收盘价': [10.08, 10.12, 10.25],
            '涨跌幅': [0.30, 0.40, 1.28]
        })
        md_table = dataframe_to_markdown(test_df)
        print(f"DataFrame converted to Markdown:\n{md_table}")
    else:
        print("pandas not installed, skipping DataFrame test")
    
    # Test build_* functions
    print("\n" + "=" * 50)
    print("Testing build_* functions:")
    
    test_stock_info = {
        'code': '600000',
        'name': '浦发银行',
        'business': '银行业'
    }
    
    prompt = build_duanxian_prompt(
        stock_info=test_stock_info,
        stock_status=test_df if HAS_PANDAS else "无数据",
        stock_weekly_status="",
        news_list=[{'title': '测试新闻', 'time': '2026-01-29', 'content': '测试内容'}],
        dapan="",
        market_activity=""
    )
    print(f"build_duanxian_prompt length: {len(prompt)} chars")
    
    print("\n" + "=" * 50)
    print("All prompt templates tested successfully!")
    
    return True


if __name__ == "__main__":
    test_prompt_templates()
