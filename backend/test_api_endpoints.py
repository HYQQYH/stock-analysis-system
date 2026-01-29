"""
Comprehensive API Endpoint Testing Script
Tests all newly implemented API routes from section 4.2
"""
import requests
import time
import json
from datetime import datetime, timedelta

# API Base URL
BASE_URL = "http://localhost:8000"

# Test stock codes
TEST_STOCK_CODES = ["600000", "000001", "000002"]


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(test_name, success, message="", data=None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if message:
        print(f"  Message: {message}")
    if data:
        print(f"  Data: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")


def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        success = response.status_code == 200 and data.get("status") == "healthy"
        print_result("GET /health", success, response.status_code, data)
        return success
    except Exception as e:
        print_result("GET /health", False, str(e))
        return False


def test_stock_search():
    """Test stock search API"""
    print_section("Testing Stock Search API")
    
    endpoints = [
        ("POST /api/v1/stocks/search - By code", {"keyword": "600000"}),
        ("POST /api/v1/stocks/search - By name", {"keyword": "浦发银行"}),
    ]
    
    results = []
    for name, payload in endpoints:
        try:
            response = requests.post(f"{BASE_URL}/api/v1/stocks/search", json=payload, timeout=10)
            data = response.json()
            success = response.status_code == 200 and data.get("code") == 0
            print_result(name, success, response.status_code, data.get("data"))
            results.append(success)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)


def test_stock_kline():
    """Test stock K-line data API"""
    print_section("Testing Stock K-line API")
    
    endpoints = [
        ("GET /api/v1/stocks/600000/kline - Daily", {"kline_type": "day"}),
        ("GET /api/v1/stocks/000001/kline - Weekly", {"kline_type": "week"}),
        ("GET /api/v1/stocks/000002/kline - With date range", {
            "kline_type": "day",
            "start_date": "20240101",
            "end_date": "20241231"
        }),
    ]
    
    results = []
    for stock_code in TEST_STOCK_CODES[:2]:
        for name, params in endpoints:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/stocks/{stock_code}/kline",
                    params=params,
                    timeout=15
                )
                data = response.json()
                success = response.status_code == 200 and data.get("code") == 200
                if success and data.get("data"):
                    kline_data = data["data"]
                    # Verify data structure
                    has_fields = all(key in kline_data for key in ["stock_code", "kline_type", "data"])
                    if has_fields and kline_data.get("data"):
                        # Verify at least one data point has required fields
                        point = kline_data["data"][0]
                        has_ohlcv = all(k in point for k in ["trade_date", "open_price", "high_price", "low_price", "close_price", "volume"])
                        success = success and has_ohlcv
                print_result(f"{name} - {stock_code}", success, response.status_code)
                results.append(success)
            except Exception as e:
                print_result(f"{name} - {stock_code}", False, str(e))
                results.append(False)
            break  # Test only one stock for K-line to save time
    
    return all(results)


def test_stock_indicators():
    """Test stock technical indicators API"""
    print_section("Testing Stock Indicators API")
    
    endpoints = [
        ("GET /api/v1/stocks/600000/indicators - Daily 30 days", {"kline_type": "day", "days": 30}),
        ("GET /api/v1/stocks/000001/indicators - Weekly 60 days", {"kline_type": "week", "days": 60}),
    ]
    
    results = []
    for name, params in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/stocks/600000/indicators",
                params=params,
                timeout=15
            )
            data = response.json()
            success = response.status_code == 200 and data.get("code") == 200
            if success and data.get("data"):
                indicators = data["data"]
                has_fields = "indicators" in indicators and "stock_code" in indicators
                if has_fields and indicators.get("indicators"):
                    # Check MACD, KDJ, RSI are present
                    macd = indicators["indicators"].get("macd")
                    kdj = indicators["indicators"].get("kdj")
                    rsi = indicators["indicators"].get("rsi")
                    has_all = macd is not None and kdj is not None and rsi is not None
                    success = success and has_all
            print_result(name, success, response.status_code)
            results.append(success)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)


def test_stock_info():
    """Test stock company info API"""
    print_section("Testing Stock Company Info API")
    
    stock_code = "600000"
    try:
        response = requests.get(f"{BASE_URL}/api/v1/stocks/{stock_code}/info", timeout=10)
        data = response.json()
        print("data:", data)
        success = response.status_code == 200 and data.get("code") == 200
        if success and data.get("data"):
            info = data["data"]
            # Verify some expected fields
            has_fields = "stock_code" in info or "公司名称" in info or "business" in info
            success = success and has_fields
        print_result(f"GET /api/v1/stocks/{stock_code}/info", success, response.status_code)
        return success
    except Exception as e:
        print_result(f"GET /api/v1/stocks/{stock_code}/info", False, str(e))
        return False


def test_market_index():
    """Test market index API"""
    print_section("Testing Market Index API")
    
    endpoints = [
        ("GET /api/v1/market/index - Daily", {"kline_type": "day", "days": 30}),
        ("GET /api/v1/market/index - Weekly", {"kline_type": "week", "days": 20}),
    ]
    
    results = []
    for name, params in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/market/index", params=params, timeout=15)
            data = response.json()
            success = response.status_code == 200 and data.get("code") == 200
            if success and data.get("data"):
                index_data = data["data"]
                has_fields = "index_code" in index_data or "data" in index_data
                if has_fields and index_data.get("data"):
                    has_ohlcv = all(k in index_data["data"][0] for k in 
                                   ["trade_date", "open_price", "high_price", "low_price", "close_price", "volume"])
                    success = success and has_ohlcv
            print_result(name, success, response.status_code)
            results.append(success)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)


def test_market_sentiment():
    """Test market sentiment API"""
    print_section("Testing Market Sentiment API")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/market/sentiment", timeout=15)
        data = response.json()
        success = response.status_code == 200 and data.get("code") == 200
        if success and data.get("data"):
            sentiment = data["data"]
            has_fields = "rise_count" in sentiment or "date" in sentiment or "sentiment_score" in sentiment
            success = success and has_fields
        print_result("GET /api/v1/market/sentiment", success, response.status_code)
        return success
    except Exception as e:
        print_result("GET /api/v1/market/sentiment", False, str(e))
        return False


def test_market_fund_flow():
    """Test market fund flow API"""
    print_section("Testing Market Fund Flow API")
    
    # Test with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/market/fund-flow",
            params={"date": today},
            timeout=15
        )
        data = response.json()
        success = response.status_code == 200 and data.get("code") == 200
        if success and data.get("data"):
            fund_flow = data["data"]
            has_fields = "date" in fund_flow or "main_net" in fund_flow
            success = success and has_fields
        print_result(f"GET /api/v1/market/fund-flow - {today}", success, response.status_code)
        return success
    except Exception as e:
        print_result(f"GET /api/v1/market/fund-flow - {today}", False, str(e))
        return False


def test_market_limit_up():
    """Test market limit-up pool API"""
    print_section("Testing Market Limit-up Pool API")
    
    today = datetime.now().strftime("%Y%m%d")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/market/limit-up",
            params={"date": today},
            timeout=15
        )
        data = response.json()
        success = response.status_code == 200 and data.get("code") == 200
        if success and data.get("data"):
            limit_up = data["data"]
            has_fields = "date" in limit_up or "stocks" in limit_up
            success = success and has_fields
        print_result(f"GET /api/v1/market/limit-up - {today}", success, response.status_code)
        return success
    except Exception as e:
        print_result(f"GET /api/v1/market/limit-up - {today}", False, str(e))
        return False


def test_analysis_create_and_poll():
    """Test analysis creation and polling"""
    print_section("Testing Analysis API - Create and Poll")
    
    analysis_modes = [
        "基础面技术面综合分析",
        "波段交易分析",
        "短线T+1分析",
        "涨停反包分析",
        "投机套利分析",
        "公司估值分析"
    ]
    
    results = []
    analysis_ids = []
    
    # Test creating analysis tasks
    print("\n--- Creating Analysis Tasks ---")
    for mode in analysis_modes[:2]:  # Test 2 modes to save time
        try:
            payload = {
                "stock_code": "600000",
                "analysis_mode": mode,
                "kline_type": "day",
                "sector_names": ["银行板块"],
                "include_news": True
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/analysis",
                json=payload,
                timeout=10
            )
            data = response.json()
            print("data:", data)
            success = response.status_code == 200 and data.get("code") == 200
            if success and data.get("data"):
                analysis_data = data["data"]
                has_fields = "analysis_id" in analysis_data and "status" in analysis_data
                success = success and has_fields
                if success and analysis_data.get("analysis_id"):
                    analysis_ids.append(analysis_data["analysis_id"])
                    print(f"✓ Created analysis task: {analysis_data['analysis_id']} ({mode})")
                results.append(success)
            else:
                print_result(f"POST /api/v1/analysis - {mode}", False, response.status_code)
                results.append(False)
        except Exception as e:
            print_result(f"POST /api/v1/analysis - {mode}", False, str(e))
            results.append(False)
    
    # Test polling for results
    print("\n--- Polling for Analysis Results ---")
    if analysis_ids:
        for analysis_id in analysis_ids[:1]:  # Poll only one to save time
            max_attempts = 12  # 12 * 2.5 = 30 seconds max
            for attempt in range(max_attempts):
                try:
                    time.sleep(2.5)  # Wait before polling
                    response = requests.get(
                        f"{BASE_URL}/api/v1/analysis/{analysis_id}",
                        timeout=10
                    )
                    data = response.json()
                    print("******************")
                    print("data:", data)
                    success = response.status_code == 200 and data.get("code") == 200
                    if success and data.get("data"):
                        detail = data["data"]
                        status = detail.get("status")
                        print(f"  Poll {attempt + 1}: Status = {status}")
                        
                        if status == "completed":
                            # Verify result structure
                            result = detail.get("result")
                            if result:
                                has_fields = "analysis_result" in result and "trading_advice" in result
                                if has_fields:
                                    trading_advice = result.get("trading_advice", {})
                                    has_advice = all(k in trading_advice for k in 
                                                   ["direction", "target_price", "stop_loss"])
                                    success = success and has_advice
                            print_result(f"GET /api/v1/analysis/{analysis_id}", success, 
                                       "Analysis completed")
                            results.append(success)
                            break
                        elif status in ["failed", "timeout"]:
                            error_msg = detail.get("error_message", "Unknown error")
                            print_result(f"GET /api/v1/analysis/{analysis_id}", False, 
                                       f"Status: {status}, Error: {error_msg}")
                            results.append(False)
                            break
                        # Continue polling for pending/running
                        results.append(success)
                    else:
                        results.append(False)
                        break
                except Exception as e:
                    print_result(f"GET /api/v1/analysis/{analysis_id}", False, str(e))
                    results.append(False)
                    break
    else:
        print("  No analysis IDs to poll")
    
    return all(results)


def test_analysis_history():
    """Test analysis history API"""
    print_section("Testing Analysis History API")
    
    # First create an analysis task
    try:
        payload = {
            "stock_code": "000001",
            "analysis_mode": "波段交易分析",
            "kline_type": "day",
            "sector_names": ["金融板块"],
            "include_news": False
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis",
            json=payload,
            timeout=10
        )
        data = response.json()
        if data.get("code") != 200 or not data.get("data"):
            print_result("POST /api/v1/analysis (for history test)", False, "Failed to create task")
            return False
    except Exception as e:
        print_result("POST /api/v1/analysis (for history test)", False, str(e))
        return False
    
    # Test history endpoints
    endpoints = [
        ("GET /api/v1/analysis/history - All", {}),
        ("GET /api/v1/analysis/history - Filter by stock", {"stock_code": "600000"}),
        ("GET /api/v1/analysis/history - Page 1", {"page": 1, "page_size": 5}),
    ]
    
    results = []
    for name, params in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/analysis/history",
                params=params,
                timeout=10
            )
            data = response.json()
            success = response.status_code == 200 and data.get("code") == 200
            if success and data.get("data"):
                history = data["data"]
                has_fields = "total" in history and "page" in history and "data" in history
                success = success and has_fields
            print_result(name, success, response.status_code)
            results.append(success)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)


def test_analysis_delete():
    """Test analysis delete API"""
    print_section("Testing Analysis Delete API")
    
    # First create an analysis task
    analysis_id = None
    try:
        payload = {
            "stock_code": "000002",
            "analysis_mode": "公司估值分析",
            "kline_type": "day",
            "include_news": False
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis",
            json=payload,
            timeout=10
        )
        data = response.json()
        if data.get("code") == 200 and data.get("data"):
            analysis_id = data["data"].get("analysis_id")
    
    except Exception as e:
        print_result("POST /api/v1/analysis (for delete test)", False, str(e))
        return False
    
    if not analysis_id:
        print_result("DELETE /api/v1/analysis/{id}", False, "No analysis ID to delete")
        return False
    
    # Test delete
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/analysis/{analysis_id}",
            timeout=10
        )
        data = response.json()
        success = response.status_code == 200 and data.get("code") == 200
        print_result(f"DELETE /api/v1/analysis/{analysis_id}", success, response.status_code)
        
        # Verify deletion
        time.sleep(0.5)
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/{analysis_id}",
            timeout=10
        )
        verify_deleted = response.status_code == 404
        print_result(f"Verify deleted - {analysis_id}", verify_deleted, "Should return 404")
        
        return success and verify_deleted
    except Exception as e:
        print_result(f"DELETE /api/v1/analysis/{analysis_id}", False, str(e))
        return False


def test_error_handling():
    """Test error handling for various invalid requests"""
    print_section("Testing Error Handling")
    
    test_cases = [
        ("Invalid stock code (not 6 digits)", 
         "POST", "/api/v1/stocks/search", {"stock_code": "123"}, 422),
        ("Invalid date format", 
         "GET", "/api/v1/stocks/600000/kline", {"start_date": "20240101"}, 200),
        ("Non-existent analysis ID", 
         "GET", "/api/v1/analysis/nonexistent-id", {}, 404),
        ("Delete non-existent analysis", 
         "DELETE", "/api/v1/analysis/nonexistent-id", {}, 404),
    ]
    
    results = []
    for name, method, endpoint, params, expected_status in test_cases:
        try:
            if method == "POST":
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json=params,
                    timeout=10
                )
            elif method == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    params=params,
                    timeout=10
                )
            elif method == "DELETE":
                response = requests.delete(
                    f"{BASE_URL}{endpoint}",
                    timeout=10
                )
            
            success = response.status_code == expected_status
            print_result(name, success, f"Expected {expected_status}, got {response.status_code}")
            results.append(success)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  STOCK ANALYSIS SYSTEM - API ENDPOINT TESTING")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Server is not running!")
        print("Please start the server first:")
        print("  cd backend && ../backend/aistock_env/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Run all tests
    test_results = {
        # "Health Check": test_health_check(),
        # "Stock Search API": test_stock_search(),
        # "Stock K-line API": test_stock_kline(),
        # "Stock Indicators API": test_stock_indicators(),
        # "Stock Info API": test_stock_info(),
        # "Market Index API": test_market_index(),
        # "Market Sentiment API": test_market_sentiment(),
        # "Market Fund Flow API": test_market_fund_flow(),
        # "Market Limit-up API": test_market_limit_up(),
        # "Analysis Create & Poll": test_analysis_create_and_poll(),
        # "Analysis History": test_analysis_history(),
        # "Analysis Delete": test_analysis_delete(),
        "Error Handling": test_error_handling(),
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    print("\n")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"\n" + "-" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    return all(test_results.values())


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)