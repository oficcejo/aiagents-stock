"""
TypeSafe Jev 结构化决策接入单元测试

覆盖 openspec/changes/add-typesafe-jev-decision 的关键行为：
- JevDecisionClient 请求/归一化/重试/JevError（mock requests，不触真网络）
- 评级映射、置信度换算、多维 Score 加权合成
- compute_price_fields 与统一规范解析（split("-") / re.findall）兼容性
- make_final_decision 适配层：Jev 成功路径 / 低置信度降级 / 网络失败降级
- 新闻立场分类降级链与告警置信度门控

运行：venv\\Scripts\\python.exe -m pytest test_typesafe_decision_client.py -v
"""
import json

import pytest

import config
import typesafe_decision_client as tdc
from typesafe_decision_client import (
    JevDecisionClient, JevError, RATING_MAP,
    final_decision_questions, news_stance_questions,
    normalize_score, composite_decision_score,
    rating_of, confidence_of, stance_label,
    build_analysis_state, build_news_state,
)
from llm_client import compute_price_fields, get_jev_client


# ============================================================
# 工具：mock responses.post
# ============================================================

class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or json.dumps(payload or {})

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def _jev_answers_payload():
    return {
        "answers": {
            "rating": {"type": "choice", "choice": "buy", "confidence": 0.82,
                       "probabilities": {"buy": 0.82, "hold": 0.18}},
            "major_risk": {"type": "noul", "noul": 0.1},
            "score_technical": {"type": "score", "score": 3.0},
            "score_fundamental": {"type": "score", "score": 2.0},
            "score_fund_flow": {"type": "score", "score": 4.0},
            "score_risk": {"type": "score", "score": 3.0},
        }
    }


@pytest.fixture
def key_env(monkeypatch):
    """强制启用 Jev（写入假 Key），并禁用 SDK 路径保证走 requests。"""
    monkeypatch.setattr(config, "TYPESAFE_API_KEY", "test-key")
    monkeypatch.setattr(config, "TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1")


@pytest.fixture
def client(key_env, monkeypatch):
    c = JevDecisionClient()
    monkeypatch.setattr(c, "_sdk", None)  # 强制 requests 路径
    return c


# ============================================================
# 1. 客户端：请求构造 / 归一化 / 重试 / JevError
# ============================================================

def test_ask_via_http_success(client, monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured.update(url=url, payload=json, headers=headers, timeout=timeout)
        return FakeResponse(200, _jev_answers_payload())

    monkeypatch.setattr("requests.post", fake_post)
    answers = client.ask("测试state", final_decision_questions())

    assert captured["url"].endswith("/systemone")
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["state"] == "测试state"
    assert captured["payload"]["model"] == config.TYPESAFE_MODEL
    assert answers["rating"]["choice"] == "buy"


def test_ask_retries_once_then_succeeds(client, monkeypatch):
    calls = {"n": 0}

    def flaky_post(url, json=None, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("boom")
        return FakeResponse(200, _jev_answers_payload())

    monkeypatch.setattr("requests.post", flaky_post)
    answers = client.ask("s", {"rating": final_decision_questions()["rating"]})
    assert calls["n"] == 2
    assert answers["rating"]["choice"] == "buy"


def test_ask_raises_jev_error_after_retries(client, monkeypatch):
    def bad_post(*a, **k):
        return FakeResponse(503, None, text="service unavailable")

    monkeypatch.setattr("requests.post", bad_post)
    with pytest.raises(JevError):
        client.ask("s", news_stance_questions())


def test_client_requires_api_key(monkeypatch):
    monkeypatch.setattr(config, "TYPESAFE_API_KEY", "")
    with pytest.raises(JevError):
        JevDecisionClient()
    assert get_jev_client() is None  # 未配置 Key 时工厂返回 None（零侵入）


# ============================================================
# 2. 答案读取与合成
# ============================================================

def test_rating_and_confidence_mapping():
    answers = _jev_answers_payload()["answers"]
    assert rating_of(answers) == RATING_MAP["buy"] == "买入"
    assert confidence_of(answers) == pytest.approx(0.82)
    assert stance_label({"stance": {"choice": "negative"}}) == "利空"


def test_normalize_score_and_composite():
    assert normalize_score(4, levels=5) == 10.0
    assert normalize_score(0, levels=5) == 0.0
    answers = _jev_answers_payload()["answers"]
    # 3->7.5, 2->5.0, 4->10.0, 3->7.5，权重 0.3/0.3/0.25/0.15
    expected = (7.5 * 0.30 + 5.0 * 0.30 + 10.0 * 0.25 + 7.5 * 0.15) / sum(config.JEV_SCORE_WEIGHTS.values())
    assert composite_decision_score(answers) == pytest.approx(round(expected, 1))
    assert composite_decision_score({}) is None


def test_state_builders_truncate():
    long_text = "讨" * (tdc.STATE_MAX_CHARS + 500)
    state = build_analysis_state({"name": "X", "symbol": "600000", "current_price": 10}, {}, long_text, {})
    assert len(state) <= tdc.STATE_MAX_CHARS
    news_state = build_news_state("标题", "内容" * 9000, "贵州茅台")
    assert len(news_state) <= tdc.STATE_MAX_CHARS


# ============================================================
# 3. 价位字段：格式与统一规范解析兼容（任务 8.5）
# ============================================================

def test_compute_price_fields_downstream_parsing():
    import re
    fields = compute_price_fields(10.0)
    # entry_range 可被 split("-") 解析
    lo, hi = [float(x) for x in fields["entry_range"].split("-")]
    assert lo == pytest.approx(9.80) and hi == pytest.approx(10.00)
    # take_profit / stop_loss 可被 re.findall(r'\d+\.?\d*') 解析
    assert float(re.findall(r'\d+\.?\d*', fields["take_profit"])[0]) == pytest.approx(10.80)
    assert float(re.findall(r'\d+\.?\d*', fields["stop_loss"])[0]) == pytest.approx(9.50)
    # 数值字段直接可用
    assert fields["take_profit_value"] == 10.8 and fields["stop_loss_value"] == 9.5
    assert compute_price_fields("N/A") is None
    assert compute_price_fields(-1) is None


# ============================================================
# 4. make_final_decision 适配层（任务 8.2 / 8.3 / 8.4）
# ============================================================

class FakeJevClient:
    def __init__(self, answers=None, error=None):
        self._answers, self._error = answers, error

    def ask_final_decision(self, state, include_scores=True):
        if self._error:
            raise self._error
        return self._answers


class FakeTextClient:
    def final_decision(self, discussion, stock_info, indicators):
        return {"rating": "买入", "confidence_level": "7", "entry_range": "9.8-10.0",
                "take_profit": "止盈: 10.8元", "stop_loss": "止损: 9.5元"}


def _make_agents_obj():
    from ai_agents import StockAnalysisAgents
    obj = StockAnalysisAgents.__new__(StockAnalysisAgents)  # 跳过 __init__（不建真实LLM客户端）
    obj.deepseek_client = FakeTextClient()
    return obj


def test_final_decision_via_jev(monkeypatch):
    obj = _make_agents_obj()
    monkeypatch.setattr("ai_agents.get_jev_client", lambda: FakeJevClient(_jev_answers_payload()["answers"]))
    decision = obj.make_final_decision("讨论结论", {"current_price": 10.0, "symbol": "600000", "name": "测试"}, {})
    assert decision["decision_source"] == "jev"
    assert decision["rating"] == "买入"
    assert decision["confidence_level"] == pytest.approx(8.2)  # 0.82 * 10
    assert decision["entry_range"] == "9.80-10.00"
    assert decision["jev_composite_score"] is not None
    assert "_jev_confidence" not in decision  # 内部键不外泄


def test_final_decision_low_confidence_falls_back(monkeypatch):
    obj = _make_agents_obj()
    weak = _jev_answers_payload()["answers"]
    weak["rating"]["confidence"] = 0.3  # 低于 JEV_MIN_CONFIDENCE
    monkeypatch.setattr("ai_agents.get_jev_client", lambda: FakeJevClient(weak))
    decision = obj.make_final_decision("讨论", {"current_price": 10.0}, {})
    assert decision["decision_source"] == "deepseek_fallback"
    assert decision["rating"] == "买入"


def test_final_decision_network_error_falls_back(monkeypatch):
    obj = _make_agents_obj()
    monkeypatch.setattr("ai_agents.get_jev_client", lambda: FakeJevClient(error=JevError("网络不可达")))
    decision = obj.make_final_decision("讨论", {"current_price": 10.0}, {})
    assert decision["decision_source"] == "deepseek_fallback"


def test_final_decision_no_jev_config_untouched(monkeypatch):
    """未配置 Key：get_jev_client 返回 None，行为与主干一致（任务 8.1 核心断言）。"""
    obj = _make_agents_obj()
    monkeypatch.setattr("ai_agents.get_jev_client", lambda: None)
    decision = obj.make_final_decision("讨论", {"current_price": 10.0}, {})
    assert decision["decision_source"] == "deepseek_fallback"


# ============================================================
# 5. 新闻立场分类与告警门控（任务 6.x）
# ============================================================

class FakeNewsJevClient:
    def __init__(self, answers=None, error=None):
        self._answers, self._error = answers, error

    def ask_news_stance(self, state):
        if self._error:
            raise self._error
        return self._answers


def _analyzer_with(fake_client):
    from news_flow_sentiment import SentimentAnalyzer
    a = SentimentAnalyzer()
    a._jev_initialized = True
    a._jev_client = fake_client
    return a


def test_news_stance_jev_path():
    a = _analyzer_with(FakeNewsJevClient({
        "stance": {"choice": "negative", "confidence": 0.9},
        "urgency": {"score": 2.0},
        "relevant": {"noul": 1.0},
    }))
    r = a.classify_news_stance("公司财务造假被立案调查", "详情……")
    assert r["stance"] == "利空" and r["decision_source"] == "jev" and r["confidence"] == 0.9


def test_news_stance_falls_back_to_text_then_keyword(monkeypatch):
    a = _analyzer_with(FakeNewsJevClient(error=JevError("挂了")))

    def broken_llm(*args, **kwargs):
        raise RuntimeError("无DeepSeek环境")

    monkeypatch.setattr("llm_client.get_llm_client", broken_llm)
    r = a.classify_news_stance("公司业绩预增80%", "利好")
    # 文本链路失败 -> 关键词兜底（"利好"/"增"类关键词命中）
    assert r["decision_source"] == "keyword_fallback"
    assert r["stance"] in ("利好", "中性", "利空")


def test_stance_summary_alert_gating():
    """告警候选仅收录 confidence >= JEV_ALERT_MIN_CONFIDENCE 的 Jev 结论。"""
    a = _analyzer_with(FakeNewsJevClient({
        "stance": {"choice": "positive", "confidence": 0.4},  # 低于0.6门限
        "urgency": {"score": 1.0},
        "relevant": {"noul": 1.0},
    }))
    summary = a._apply_stance_refinement([{"title": "获得大订单", "content": "合同1亿"}])
    assert summary["positive"] == 1
    assert summary["alerts"] == []  # 低置信度不进入告警

    a2 = _analyzer_with(FakeNewsJevClient({
        "stance": {"choice": "positive", "confidence": 0.85},
        "urgency": {"score": 2.0},
        "relevant": {"noul": 1.0},
    }))
    summary2 = a2._apply_stance_refinement([{"title": "获得大订单", "content": "合同1亿"}])
    assert len(summary2["alerts"]) == 1 and summary2["alerts"][0]["stance"] == "利好"


def test_alert_system_second_gate():
    """NewsFlowAlertSystem 二次门控：db 阈值过滤。"""
    from news_flow_alert import NewsFlowAlertSystem
    sys_ = NewsFlowAlertSystem.__new__(NewsFlowAlertSystem)  # 跳过 __init__（不连db/通知）
    sys_.default_thresholds = {'jev_min_alert_confidence': 0.6}
    sys_.get_threshold = lambda k: sys_.default_thresholds.get(k, 0)

    sentiment_data = {"sentiment": {"stance_summary": {"alerts": [
        {"stance": "利空", "confidence": 0.9, "title": "立案调查", "urgency": 2.0},
        {"stance": "利好", "confidence": 0.95, "title": "业绩预增", "urgency": 1.0},
    ]}}}
    alert = sys_._check_news_stance_alert(sentiment_data)
    assert alert is not None
    assert alert["alert_level"] == "warning" and "利空" in alert["title"]  # 利空优先

    # 全部低于阈值 -> 不告警
    sentiment_data["sentiment"]["stance_summary"]["alerts"] = [
        {"stance": "利空", "confidence": 0.55, "title": "某消息", "urgency": 1.0}]
    assert sys_._check_news_stance_alert(sentiment_data) is None
