"""
TypeSafe Jev 结构化决策客户端

Jev 是 TypeSafe 的 System One 模型：传入 state（自由文本）+ 类型化问题
（Choice / Score / Noul），并行评估后直接返回类型化答案 + 概率分布 + 校准置信度，
无文本生成、无正则解析。文档：https://docs.typesafe.ai/introduction

本模块只提供通用的"决策原语"：客户端、问题模板、state 构建、答案归一化。
降级链（Jev 失败回落 DeepSeek 文本+解析）由各业务调用点的适配层实现。

实现路径（构造时探测，二者返回结构一致）：
1. 优先官方 typesafe-sdk（pip install typesafe-sdk）
2. SDK 不可导入时回退 requests 裸 POST https://api.typesafe.ai/v1/systemone
"""
import logging
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger(__name__)

# ============================================================
# 常量：评级映射与问题模板（与 docs/UNIFIED_ANALYSIS_SPEC.md 值域对齐）
# ============================================================

# Jev Choice 选项 key -> 统一字段 rating 的中文取值
RATING_MAP = {
    "strong_buy": "强烈买入",
    "buy": "买入",
    "hold": "持有",
    "sell": "卖出",
    "strong_sell": "强烈卖出",
}

# Score 五档量表（返回 0-4 档索引，归一化到 0-10 见 normalize_score）
_SCORE_LEVELS = [
    "非常差/风险极高",
    "偏差",
    "中性/一般",
    "偏好",
    "非常好/风险很低",
]


class JevError(RuntimeError):
    """Jev 调用失败（网络异常/超时/HTTP错误/响应结构异常），供适配层捕获后降级。"""


def final_decision_questions(include_scores: bool = True) -> Dict[str, Dict[str, Any]]:
    """最终投资决策问题组：评级(Choice) + 重大风险(Noul)，可选多维打分(Score)。

    一次调用内全部问题并行、独立评估（Jev 特性：加问题几乎不增加延迟）。
    """
    questions: Dict[str, Dict[str, Any]] = {
        "rating": {
            "type": "choice",
            "instructions": "综合团队讨论结论，该股票的最终投资评级是哪一档？",
            "criteria": dict(RATING_MAP),
        },
        "major_risk": {
            "type": "noul",
            "instructions": "讨论结论中存在质押爆仓、商誉减值、立案调查、业绩暴雷等重大风险，需要回避或降仓",
        },
    }
    if include_scores:
        questions["score_technical"] = {
            "type": "score",
            "instructions": "技术面强度（趋势、动量、量价配合）",
            "criteria": list(_SCORE_LEVELS),
        }
        questions["score_fundamental"] = {
            "type": "score",
            "instructions": "基本面质量（盈利、成长、估值）",
            "criteria": list(_SCORE_LEVELS),
        }
        questions["score_fund_flow"] = {
            "type": "score",
            "instructions": "资金面强度（主力/北向资金流向）",
            "criteria": list(_SCORE_LEVELS),
        }
        questions["score_risk"] = {
            "type": "score",
            "instructions": "风险安全度（分数越高风险越低）",
            "criteria": list(_SCORE_LEVELS),
        }
    return questions


def news_stance_questions() -> Dict[str, Dict[str, Any]]:
    """新闻情绪分类问题：立场(Choice) + 紧急度(Score三档) + 相关性(Noul)。"""
    return {
        "stance": {
            "type": "choice",
            "instructions": "这条新闻对该股票整体而言是什么立场？",
            "criteria": {
                "positive": "利好（业绩增长、政策支持、大额订单等）",
                "neutral": "中性（客观报道、影响不明）",
                "negative": "利空（处罚、减持、亏损、事故等）",
            },
        },
        "urgency": {
            "type": "score",
            "instructions": "该新闻需要投资者反应的紧迫程度",
            "criteria": ["不紧迫，可长期观察", "中等着急，数日内需关注", "非常紧急，立即反应"],
        },
        "relevant": {
            "type": "noul",
            "instructions": "新闻主体直接涉及该公司本身（而非泛泛的行业/概念关联）",
        },
    }


def normalize_score(score: Any, levels: int = 5) -> float:
    """把 Jev Score 的档索引（0..levels-1）归一化到 0-10 分。"""
    try:
        return round(float(score) / (levels - 1) * 10, 1)
    except (TypeError, ValueError):
        return 5.0


def composite_decision_score(answers: Dict[str, Any]) -> Optional[float]:
    """按 config.JEV_SCORE_WEIGHTS 加权合成批量选股总分（0-10，保留1位）。

    对应 Jev 官方最佳实践："原子问题 + 代码侧组合"，权重调整只改系数不改问题。
    """
    weights = config.JEV_SCORE_WEIGHTS
    total = 0.0
    weight_sum = 0.0
    for dim, weight in weights.items():
        answer = answers.get(f"score_{dim}")
        if answer is None:
            continue
        total += normalize_score(answer.get("score")) * weight
        weight_sum += weight
    if weight_sum == 0:
        return None
    return round(total / weight_sum, 1)


# ============================================================
# state 构建（统一截断，避免各调用点格式漂移）
# ============================================================

STATE_MAX_CHARS = 6000  # 超出会截断，防止 state 过长超出模型窗口


_CLIP_SUFFIX = "…(截断)"


def _clip(text: str, limit: int) -> str:
    text = str(text or "")
    if len(text) > limit:
        return text[:max(0, limit - len(_CLIP_SUFFIX))] + _CLIP_SUFFIX
    return text


def build_analysis_state(stock_info: Dict, agents_results: Dict, discussion_result: str,
                         indicators: Dict = None) -> str:
    """把分析师结论 + 团队讨论 + 关键指标序列化为 Jev state 文本。"""
    indicators = indicators or {}
    parts = [
        f"股票：{stock_info.get('name', 'N/A')}（{stock_info.get('symbol', 'N/A')}）",
        f"当前价格：{stock_info.get('current_price', 'N/A')}；"
        f"涨跌幅：{stock_info.get('change_percent', 'N/A')}%",
        f"MA20：{indicators.get('ma20', 'N/A')}；RSI：{indicators.get('rsi', 'N/A')}",
    ]
    per_analyst = max(400, STATE_MAX_CHARS // max(len(agents_results), 1) // 2)
    for key, result in (agents_results or {}).items():
        if isinstance(result, dict):
            parts.append(f"【{result.get('agent_name', key)}结论】{_clip(result.get('analysis', ''), per_analyst)}")
    parts.append(f"【团队讨论结论】{_clip(discussion_result, STATE_MAX_CHARS // 2)}")
    return "\n".join(parts)[:STATE_MAX_CHARS]


def build_news_state(title: str, content: str, stock_name: str) -> str:
    """把单条新闻 + 关联股票序列化为 Jev state 文本。"""
    return _clip(
        f"股票：{stock_name}\n新闻标题：{title}\n新闻内容：{content}",
        STATE_MAX_CHARS,
    )


# ============================================================
# 客户端
# ============================================================

class JevDecisionClient:
    """TypeSafe Jev 决策客户端。

    ask(state, questions) 返回 {问题名: {"type", "choice|score|noul", "confidence", "probabilities"}}。
    任何失败抛出 JevError，由调用点适配层负责降级。
    """

    def __init__(self, model: Optional[str] = None):
        if not config.TYPESAFE_API_KEY:
            raise JevError("未配置 TYPESAFE_API_KEY，Jev 决策引擎不可用")
        self.model = model or config.TYPESAFE_MODEL
        self.base_url = config.TYPESAFE_BASE_URL.rstrip("/")
        self.timeout = config.TYPESAFE_TIMEOUT_SEC
        self._sdk = None
        try:
            from typesafe_sdk import TypeSafeClient  # noqa: 可选依赖探测
            self._sdk = TypeSafeClient()  # SDK 自动读取 TYPESAFE_API_KEY
            logger.info("JevDecisionClient 使用 typesafe-sdk 路径")
        except Exception:
            self._sdk = None
            logger.info("typesafe-sdk 不可用，JevDecisionClient 回退 requests 裸 HTTP 路径")

    @staticmethod
    def is_available() -> bool:
        """能力开关：是否配置了 TYPESAFE_API_KEY。"""
        return bool(config.TYPESAFE_API_KEY)

    # ---------- 对外统一入口 ----------

    def ask(self, state: str, questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """一次调用并行评估全部问题；超时/失败自动重试 1 次后抛 JevError。"""
        last_error: Optional[Exception] = None
        attempts = config.TYPESAFE_MAX_RETRIES + 1
        for attempt in range(attempts):
            try:
                if self._sdk is not None:
                    answers = self._ask_via_sdk(state, questions)
                else:
                    answers = self._ask_via_http(state, questions)
                if not isinstance(answers, dict) or not answers:
                    raise JevError("Jev 返回空答案集")
                return answers
            except JevError as e:
                last_error = e
            except Exception as e:  # 网络/SDK异常统一包装
                last_error = JevError(f"Jev 调用异常: {e}")
            if attempt < attempts - 1:
                logger.warning(f"Jev 调用失败（第{attempt + 1}次），重试中: {last_error}")
        raise last_error if isinstance(last_error, JevError) else JevError(str(last_error))

    def ask_final_decision(self, state: str, include_scores: bool = True) -> Dict[str, Any]:
        """最终决策专用快捷入口：评级 + 重大风险（+ 多维打分）。"""
        return self.ask(state, final_decision_questions(include_scores=include_scores))

    def ask_news_stance(self, state: str) -> Dict[str, Any]:
        """新闻情绪分类快捷入口。"""
        return self.ask(state, news_stance_questions())

    # ---------- 双实现路径 ----------

    def _ask_via_sdk(self, state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
        """官方 SDK 路径：把问题字典转换为 SDK 问题对象。"""
        from typesafe_sdk import Choice, Noul, Score
        sdk_questions = {}
        for name, q in questions.items():
            qtype = q.get("type")
            if qtype == "choice":
                sdk_questions[name] = Choice(instructions=q["instructions"], criteria=q["criteria"])
            elif qtype == "score":
                sdk_questions[name] = Score(instructions=q["instructions"], criteria=q["criteria"])
            elif qtype == "noul":
                sdk_questions[name] = Noul(instructions=q["instructions"])
            else:
                raise JevError(f"未知问题类型: {qtype}")
        response = self._sdk.system_one(state=state, questions=sdk_questions, model=self.model)
        raw_answers = getattr(response, "answers", None) or (response.get("answers") if isinstance(response, dict) else None)
        if raw_answers is None:
            raise JevError("SDK 响应缺少 answers 字段")
        normalized = {}
        for name, ans in raw_answers.items():
            if isinstance(ans, dict):
                normalized[name] = ans
            else:  # SDK 对象 -> dict（属性访问，兼容不同版本字段）
                normalized[name] = {
                    "type": getattr(ans, "type", None),
                    "choice": getattr(ans, "choice", None),
                    "score": getattr(ans, "score", None),
                    "noul": getattr(ans, "noul", None),
                    "confidence": getattr(ans, "confidence", None),
                    "probabilities": getattr(ans, "probabilities", None),
                }
        return normalized

    def _ask_via_http(self, state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
        """requests 裸 POST 路径（SDK 不可用时的兜底，二者返回结构一致）。"""
        import requests
        payload = {"state": state, "model": self.model, "questions": questions}
        headers = {
            "Authorization": f"Bearer {config.TYPESAFE_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                f"{self.base_url}/systemone",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise JevError(f"TypeSafe API 网络异常: {e}")
        if resp.status_code != 200:
            raise JevError(f"TypeSafe API 返回 {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
        except ValueError as e:
            raise JevError(f"TypeSafe API 响应非 JSON: {e}")
        return data.get("answers") or {}


# ============================================================
# 答案便捷读取
# ============================================================

def rating_of(answers: Dict[str, Any]) -> Optional[str]:
    """从决策答案中提取统一字段 rating（中文），失败返回 None。"""
    rating_answer = (answers or {}).get("rating") or {}
    return RATING_MAP.get(rating_answer.get("choice"))


def confidence_of(answers: Dict[str, Any]) -> Optional[float]:
    """取评级 Choice 的校准置信度（0-1），换算信心度请再乘 10。"""
    try:
        conf = (answers or {}).get("rating", {}).get("confidence")
        return float(conf) if conf is not None else None
    except (TypeError, ValueError):
        return None


def stance_label(answers: Dict[str, Any]) -> Optional[str]:
    """新闻立场：positive/neutral/negative -> 利好/中性/利空。"""
    mapping = {"positive": "利好", "neutral": "中性", "negative": "利空"}
    stance_answer = (answers or {}).get("stance") or {}
    return mapping.get(stance_answer.get("choice"))
