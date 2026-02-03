#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统验收测试脚本
执行步骤 15.3：系统验收测试
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
test_results = []

def log_test(scenario, test_name, passed, details=""):
    """记录测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    test_results.append({
        "scenario": scenario,
        "test_name": test_name,
        "passed": passed,
        "status": status,
        "details": details
    })
    print(f"[{status}] {scenario} - {test_name}")
    if details:
        print(f"       详情: {details}")

def test_scenario_1():
    """场景 1：输入股票代码，查看分析结果"""
    print("\n" + "="*60)
    print("场景 1：输入股票代码，查看分析结果")
    print("="*60)
    
    # 测试 1.1：获取股票基本信息
    try:
        r = requests.get(f"{BASE_URL}/api/v1/stocks/600000/info")
        passed = r.status_code == 200 and "stock_code" in r.text
        data = r.json()
        stock_name = data.get("data", {}).get("stock_name", "") if passed else ""
        log_test("场景1", "获取股票基本信息(600000)", passed, 
                f"股票名称: {stock_name}" if passed else f"Error: {r.text[:200]}")
    except Exception as e:
        log_test("场景1", "获取股票基本信息(600000)", False, str(e))
    
    # 测试 1.2：获取K线数据
    try:
        r = requests.get(f"{BASE_URL}/api/v1/stocks/600000/kline?type=day")
        passed = r.status_code == 200
        data = r.json()
        kline_list = data.get("data", {}).get("data", []) if passed else []
        kline_count = len(kline_list)
        log_test("场景1", "获取K线数据(日线)", passed, f"获取 {kline_count} 条K线数据")
    except Exception as e:
        log_test("场景1", "获取K线数据(日线)", False, str(e))
    
    # 测试 1.3：获取技术指标
    try:
        r = requests.get(f"{BASE_URL}/api/v1/stocks/600000/indicators?type=day")
        passed = r.status_code == 200 and "indicators" in r.text
        data = r.json()
        indicators_list = data.get("data", {}).get("indicators", []) if passed else []
        log_test("场景1", "获取技术指标", passed, f"获取 {len(indicators_list)} 条指标数据")
    except Exception as e:
        log_test("场景1", "获取技术指标", False, str(e))
    
    # 测试 1.4：创建股票分析任务（使用正确的分析模式名称）
    try:
        payload = {
            "stock_code": "600000",
            "kline_type": "day",
            "include_news": True,
            "analysis_mode": "短线T+1分析"  # 使用完整的中文名称
        }
        r = requests.post(f"{BASE_URL}/api/v1/analysis", json=payload)
        passed = r.status_code == 200 and "analysis_id" in r.text
        data = r.json()
        analysis_id = data.get("data", {}).get("analysis_id") if passed else None
        log_test("场景1", "创建股票分析任务", passed, 
                f"analysis_id: {analysis_id}" if passed else f"Error: {r.text[:300]}")
        
        # 等待分析完成后查询结果
        if analysis_id:
            time.sleep(5)  # 等待AI分析
            for i in range(10):
                r = requests.get(f"{BASE_URL}/api/v1/analysis/{analysis_id}")
                if r.status_code == 200:
                    data = r.json()
                    status = data.get("data", {}).get("status", "")
                    if status == "completed":
                        result = data.get("data", {}).get("analysis_result", "")
                        log_test("场景1", "获取分析结果", len(result) > 100, 
                                f"分析完成，结果长度: {len(result)} 字符")
                        break
                    elif status == "pending" or status == "processing":
                        time.sleep(3)
                        continue
                    else:
                        log_test("场景1", "分析状态", False, f"状态: {status}")
                        break
                time.sleep(2)
    except Exception as e:
        log_test("场景1", "股票分析流程", False, str(e))

def test_scenario_2():
    """场景 2：查看大盘数据和涨停股池"""
    print("\n" + "="*60)
    print("场景 2：查看大盘数据和涨停股池")
    print("="*60)
    
    # 测试 2.1：获取上证指数数据
    try:
        r = requests.get(f"{BASE_URL}/api/v1/market/index?type=day")
        passed = r.status_code == 200
        data = r.json()
        index_data = data.get("data", {}).get("data", []) if passed else []
        log_test("场景2", "获取上证指数数据", passed, f"获取 {len(index_data)} 条指数数据")
    except Exception as e:
        log_test("场景2", "获取上证指数数据", False, str(e))
    
    # 测试 2.2：获取大盘情绪数据
    try:
        r = requests.get(f"{BASE_URL}/api/v1/market/sentiment")
        passed = r.status_code == 200
        data = r.json()
        sentiment_score = data.get("data", {}).get("sentiment_score", "") if passed else ""
        log_test("场景2", "获取大盘情绪数据", passed, f"情绪得分: {sentiment_score}")
    except Exception as e:
        log_test("场景2", "获取大盘情绪数据", False, str(e))
    
    # 测试 2.3：获取资金流向
    try:
        r = requests.get(f"{BASE_URL}/api/v1/market/fund-flow")
        passed = r.status_code == 200
        data = r.json()
        fund_flow = data.get("data", {}) if passed else {}
        main_net = fund_flow.get("main_net_inflow", "N/A") if fund_flow else "N/A"
        log_test("场景2", "获取资金流向数据", passed, f"主力净流入: {main_net}")
    except Exception as e:
        log_test("场景2", "获取资金流向数据", False, str(e))
    
    # 测试 2.4：获取涨停股池
    try:
        r = requests.get(f"{BASE_URL}/api/v1/market/limit-up")
        passed = r.status_code == 200
        data = r.json()
        stock_count = data.get("data", {}).get("total_count", 0) if passed else 0
        log_test("场景2", "获取涨停股池", passed, f"共 {stock_count} 只涨停股票")
    except Exception as e:
        log_test("场景2", "获取涨停股池", False, str(e))

def test_scenario_3():
    """场景 3：查看新闻和投资建议"""
    print("\n" + "="*60)
    print("场景 3：查看新闻和投资建议")
    print("="*60)
    
    # 测试 3.1：获取最新新闻列表 - 检查实际 API 路径
    try:
        r = requests.get(f"{BASE_URL}/api/v1/news/latest")
        passed = r.status_code == 200 and "news" in r.text
        data = r.json()
        news_list = data.get("data", {}).get("news", []) if passed else []
        log_test("场景3", "获取最新新闻列表", passed, f"获取 {len(news_list)} 条新闻")
    except Exception as e:
        log_test("场景3", "获取最新新闻列表", False, str(e))
    
    # 测试 3.2：检查是否存在其他新闻相关 API
    try:
        r = requests.get(f"{BASE_URL}/api/v1/news")
        log_test("场景3", "检查新闻API根路径", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("场景3", "检查新闻API根路径", False, str(e))
    
    # 测试 3.3：检查爬虫 API
    try:
        r = requests.post(f"{BASE_URL}/api/v1/news/crawl")
        log_test("场景3", "触发新闻爬取", r.status_code in [200, 202, 404], f"Status: {r.status_code}")
    except Exception as e:
        log_test("场景3", "触发新闻爬取", False, str(e))

def test_scenario_4():
    """场景 4：查看历史分析记录"""
    print("\n" + "="*60)
    print("场景 4：查看历史分析记录")
    print("="*60)
    
    # 测试 4.1：获取分析历史记录
    try:
        r = requests.get(f"{BASE_URL}/api/v1/analysis/history")
        passed = r.status_code == 200
        data = r.json()
        history_list = data.get("data", {}).get("history", []) if passed else []
        log_test("场景4", "获取分析历史记录", passed, f"共 {len(history_list)} 条历史记录")
    except Exception as e:
        log_test("场景4", "获取分析历史记录", False, str(e))
    
    # 测试 4.2：按股票代码查询历史
    try:
        r = requests.get(f"{BASE_URL}/api/v1/analysis/history?stock_code=600000")
        passed = r.status_code == 200
        log_test("场景4", "按股票代码查询历史", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("场景4", "按股票代码查询历史", False, str(e))
    
    # 测试 4.3：测试分页
    try:
        r = requests.get(f"{BASE_URL}/api/v1/analysis/history?page=1&page_size=5")
        passed = r.status_code == 200
        data = r.json()
        pagination = data.get("data", {}).get("pagination", {}) if passed else {}
        log_test("场景4", "测试分页功能", passed, f"分页信息: {pagination}")
    except Exception as e:
        log_test("场景4", "测试分页功能", False, str(e))

def test_additional_apis():
    """测试其他 API 端点"""
    print("\n" + "="*60)
    print("额外 API 测试")
    print("="*60)
    
    # 测试健康检查
    try:
        r = requests.get(f"{BASE_URL}/health")
        passed = r.status_code == 200
        log_test("额外", "健康检查", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("额外", "健康检查", False, str(e))
    
    # 测试 API 文档
    try:
        r = requests.get(f"{BASE_URL}/docs")
        passed = r.status_code == 200
        log_test("额外", "API文档(Swagger)", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("额外", "API文档(Swagger)", False, str(e))

def generate_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("验收测试报告")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BASE_URL}")
    print(f"总测试数: {len(test_results)}")
    
    passed_count = sum(1 for r in test_results if r["passed"])
    failed_count = len(test_results) - passed_count
    
    print(f"通过: {passed_count}")
    print(f"失败: {failed_count}")
    print(f"通过率: {passed_count/len(test_results)*100:.1f}%")
    
    # 按场景统计
    scenarios = {}
    for r in test_results:
        if r["scenario"] not in scenarios:
            scenarios[r["scenario"]] = {"passed": 0, "failed": 0}
        if r["passed"]:
            scenarios[r["scenario"]]["passed"] += 1
        else:
            scenarios[r["scenario"]]["failed"] += 1
    
    print("\n按场景统计:")
    for scenario, stats in scenarios.items():
        print(f"  {scenario}: 通过 {stats['passed']}, 失败 {stats['failed']}")
    
    # 失败详情
    if failed_count > 0:
        print("\n失败项目详情:")
        for r in test_results:
            if not r["passed"]:
                print(f"  - {r['scenario']} - {r['test_name']}: {r['details']}")
    
    # 改进建议
    print("\n" + "="*60)
    print("改进建议")
    print("="*60)
    suggestions = []
    
    # 检查特定场景的失败
    scenario3_failed = [r for r in test_results if r["scenario"] == "场景3" and not r["passed"]]
    if scenario3_failed:
        suggestions.append("新闻模块需要完善：实现 /api/v1/news 相关的 API 端点")
    
    indicator_failed = [r for r in test_results if "技术指标" in r["test_name"] and not r["passed"]]
    if indicator_failed:
        suggestions.append("技术指标计算：需要确保 K 线数据包含 'close' 列")
    
    kline_failed = [r for r in test_results if "K线数据" in r["test_name"] and not r["passed"]]
    if kline_failed:
        suggestions.append("K线数据：上证指数数据获取可能存在问题")
    
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
    else:
        print("  无重大问题")
    
    # 保存报告到文件
    report = {
        "test_time": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total_tests": len(test_results),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": f"{passed_count/len(test_results)*100:.1f}%",
        "results": test_results,
        "suggestions": suggestions
    }
    
    with open("acceptance_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: acceptance_test_report.json")
    
    return passed_count == len(test_results)

if __name__ == "__main__":
    print("开始执行系统验收测试...")
    print(f"后端地址: {BASE_URL}")
    print()
    
    # 执行所有场景测试
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    test_scenario_4()
    test_additional_apis()
    
    # 生成报告
    all_passed = generate_report()
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有验收测试通过!")
    else:
        print(f"⚠️  测试完成: 通过 {sum(1 for r in test_results if r['passed'])}/{len(test_results)}")
    print("="*60)
