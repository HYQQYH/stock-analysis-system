#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：中信证券投机套利分析

功能：
- 对中信证券(600030)进行投机套利分析
- 使用MiniMax接口进行AI分析
- 验证完整的数据获取和大模型分析流程

股票信息：
- 股票代码：600030
- 股票名称：中信证券
- 所属板块：参股券商

分析模式：投机套利

运行方式：
    cd backend
    python test_minimax_analysis.py

依赖配置（.env）：
    LLM_PROVIDER=minimax
    MINIMAX_API_KEY=your_api_key_here
"""

import os
import sys
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.analysis_pipeline import run_stock_analysis_pipeline
from app.llm_config import (
    get_llm_manager, 
    initialize_llm, 
    LLMProvider,
    invoke_llm,
    create_chat_message
)


def test_minimax_connection():
    """测试 MiniMax 连接"""
    print("=" * 60)
    print("测试 1: MiniMax API 连接")
    print("=" * 60)
    
    # 初始化 MiniMax
    print(f"\n当前配置: LLM_PROVIDER={settings.llm_provider}")
    print(f"MiniMax API Key 状态: {'已配置' if settings.minimax_api_key else '未配置'}")
    
    if not settings.minimax_api_key:
        print("\n⚠️  警告: MiniMax API Key 未配置!")
        print("请在 .env 文件中设置: MINIMAX_API_KEY=your_api_key")
        return False
    
    # 初始化 LLM 管理器
    manager = get_llm_manager()
    success = manager.initialize("minimax")
    
    if success:
        print(f"\n✓ MiniMax 初始化成功!")
        print(f"  当前 Provider: {manager.current_provider.value}")
        
        model_info = manager.get_model_info()
        print(f"  模型信息: {json.dumps(model_info, indent=2, ensure_ascii=False)}")
        
        # 测试简单调用
        print("\n测试简单对话...")
        messages = [
            create_chat_message("system", "你是一位专业的股票分析师"),
            create_chat_message("user", "你好，请做一个简单的自我介绍")
        ]
        response = manager.invoke(messages, provider="minimax")
        
        if response.success:
            print(f"\n✓ API 调用成功!")
            print(f"  响应时间: {response.response_time_ms:.2f}ms")
            print(f"  Token使用: {response.token_usage.total_tokens}")
            print(f"  LLM Provider: {response.provider}")
            print(f"  响应内容:\n{response.content[:200]}...")
        else:
            print(f"\n✗ API 调用失败: {response.error_message}")
            return False
    else:
        print("\n✗ MiniMax 初始化失败!")
        return False
    
    return True


def test_stock_data_collection():
    """测试股票数据采集"""
    print("\n" + "=" * 60)
    print("测试 2: 股票数据采集")
    print("=" * 60)
    
    stock_code = "600030"  # 中信证券
    sector_name = "参股券商"
    
    print(f"\n股票代码: {stock_code}")
    print(f"股票名称: 中信证券")
    print(f"所属板块: {sector_name}")
    
    # 使用 pipeline 获取数据
    print("\n开始采集数据...")
    result = run_stock_analysis_pipeline(
        stock_code=stock_code,
        sector_name=sector_name,
        analysis_mode="投机套利"
    )
    
    print(f"\n执行结果:")
    print(f"  成功: {result.success}")
    print(f"  耗时: {result.execution_time_ms}ms")
    
    if result.success:
        pipeline_result = result.result
        
        print(f"\n数据采集详情:")
        print(f"  缓存键数量: {len(pipeline_result.data_cache_keys)}")
        
        if pipeline_result.analysis_result:
            ar = pipeline_result.analysis_result
            print(f"\n  K线数据: {'✓' if ar.kline_data and ar.kline_data.daily is not None else '✗'}")
            print(f"  公司信息: {'✓' if ar.company_info else '✗'}")
            print(f"  技术指标: {'✓' if ar.indicators else '✗'}")
            print(f"  相关新闻: {'✓' if ar.related_news and ar.related_news.count > 0 else '✗'}")
            print(f"  板块数据: {'✓' if ar.sector_data else '✗'}")
        
        if pipeline_result.ai_result:
            ai = pipeline_result.ai_result
            print(f"\nAI 分析结果:")
            print(f"  趋势: {ai.trend}")
            print(f"  LLM Provider: {ai.llm_provider}")
            print(f"  置信度: {ai.confidence_score}")
            print(f"  分析内容长度: {len(ai.analysis_content) if ai.analysis_content else 0} 字符")
            
            if ai.trading_advice:
                ta = ai.trading_advice
                print(f"\n交易建议:")
                print(f"  方向: {ta.direction}")
                print(f"  目标价: {ta.target_price}")
                print(f"  止损价: {ta.stop_loss}")
                print(f"  持仓时间: {ta.holding_period}个交易日")
                print(f"  风险等级: {ta.risk_level}")
        else:
            print(f"\n⚠️  AI 分析结果为空")
            
        # 显示缓存键
        if pipeline_result.data_cache_keys:
            print(f"\nRedis 缓存键:")
            for key in pipeline_result.data_cache_keys[:5]:
                print(f"  - {key}")
        
        # 显示执行日志
        if result.execution_log:
            print(f"\n执行日志:")
            print(f"  Pipeline: {result.execution_log.get('pipeline_name')}")
            print(f"  状态: {result.execution_log.get('status')}")
            print(f"  执行步骤数: {result.execution_log.get('steps_executed')}")
            
            print(f"\n  步骤详情:")
            for step in result.execution_log.get('steps', []):
                step_name = step.get('step', '')
                step_msg = step.get('message', '')
                step_duration = step.get('duration_ms', 0)
                print(f"    [{step_name}] {step_msg}" + 
                      (f" ({step_duration}ms)" if step_duration else ""))
        
        return True
    else:
        print(f"\n✗ 执行失败: {result.error_message}")
        if result.execution_log:
            print(f"执行日志: {json.dumps(result.execution_log, indent=2, ensure_ascii=False)}")
        return False


def test_full_analysis():
    """完整的短线T+1分析测试"""
    print("\n" + "=" * 60)
    print("测试 3: 完整短线T+1分析流程")
    print("=" * 60)
    
    stock_code = "300671"
    stock_name = "富满微"
    sector_name = "第三代半导体"
    analysis_mode = "短线T+1"
    
    print(f"\n分析配置:")
    print(f"  股票: {stock_code} ({stock_name})")
    print(f"  板块: {sector_name}")
    print(f"  模式: {analysis_mode}")
    
    print("\n开始完整分析流程...")
    print("-" * 40)
    
    start_time = datetime.now()
    result = run_stock_analysis_pipeline(
        stock_code=stock_code,
        sector_name=sector_name,
        analysis_mode=analysis_mode
    )
    end_time = datetime.now()
    
    print(f"\n分析完成!")
    print(f"总耗时: {(end_time - start_time).total_seconds():.2f}秒")
    print(f"Pipeline耗时: {result.execution_time_ms}ms")
    
    if result.success:
        print("\n" + "=" * 60)
        print("分析结果汇总")
        print("=" * 60)
        
        ai_result = result.result.ai_result
        
        if ai_result:
            print(f"\n【基本信息】")
            print(f"  股票代码: {stock_code}")
            print(f"  股票名称: {stock_name}")
            print(f"  所属板块: {sector_name}")
            print(f"  分析模式: {analysis_mode}")
            
            print(f"\n【AI 分析结果】")
            print(f"  趋势判断: {ai_result.trend}")
            print(f"  LLM Provider: {ai_result.llm_provider}")
            print(f"  LLM Model: {ai_result.llm_model}")
            print(f"  置信度: {ai_result.confidence_score}")
            
            if ai_result.trading_advice:
                ta = ai_result.trading_advice
                print(f"\n【交易建议】")
                print(f"  交易方向: {ta.direction}")
                print(f"  目标价格: {ta.target_price}元")
                print(f"  止损价格: {ta.stop_loss}元")
                print(f"  止盈目标: {ta.take_profit}元")
                print(f"  持仓时间: {ta.holding_period}个交易日")
                print(f"  风险等级: {ta.risk_level}")
            
            print(f"\n【分析内容】")
            print("-" * 40)
            content = ai_result.analysis_content
            if content:
                # 打印前2000个字符
                print(content[:2000])
                if len(content) > 2000:
                    print(f"\n... (共 {len(content)} 字符)")
            else:
                print("无分析内容")
            
            if ai_result.risk_warning:
                print(f"\n【风险提示】")
                print(f"  {ai_result.risk_warning}")
            
            print(f"\n【Token 使用统计】")
            print(f"  Prompt Tokens: {ai_result.token_usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion Tokens: {ai_result.token_usage.get('completion_tokens', 'N/A')}")
            print(f"  Total Tokens: {ai_result.token_usage.get('total_tokens', 'N/A')}")
            
            print(f"\n【数据缓存】")
            print(f"  缓存键数量: {len(result.result.data_cache_keys)}")
            for key in result.result.data_cache_keys:
                print(f"    - {key}")
            
            print(f"\n【执行日志】")
            print(f"  总步骤数: {result.execution_log.get('steps_executed')}")
            print(f"  总耗时: {result.execution_log.get('total_duration_ms')}ms")
            
            print("\n" + "=" * 60)
            print("✓ 完整分析流程测试通过!")
            print("=" * 60)
            
        else:
            print("\n✗ AI 分析结果为空")
            return False
    else:
        print(f"\n✗ 分析失败: {result.error_message}")
        return False
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("中信证券投机套利分析测试")
    print("股票代码: 600030")
    print("所属板块: 参股券商")
    print("LLM Provider: MiniMax")
    print("=" * 60)
    
    # 检查配置
    print("\n【环境检查】")
    print(f"  当前工作目录: {os.getcwd()}")
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  MiniMax API Key: {'已配置' if settings.minimax_api_key else '未配置'}")
    
    # 运行测试
    tests_passed = 0
    tests_total = 3
    
    # 测试 1: MiniMax 连接
    # if test_minimax_connection():
    #     tests_passed += 1
    
    # 测试 2: 数据采集
    # if test_stock_data_collection():
    #     tests_passed += 1
    
    # 测试 3: 完整分析
    if test_full_analysis():
        tests_passed += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"  通过: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print(f"\n✗ {tests_total - tests_passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
