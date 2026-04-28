"""
스미싱 탐지 파이프라인
Kanana-o 단독 분석 → 최종 판정
"""
from dataclasses import dataclass
from detectors import llm_classifier
from detectors.llm_classifier import LLMResult


@dataclass
class ScanReport:
    text: str
    llm_result: LLMResult
    final_verdict: str   # SAFE / SUSPICIOUS / BLOCK
    final_score: float   # 0.0 ~ 1.0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "final_verdict": self.final_verdict,
            "final_score": round(self.final_score, 3),
            "llm_result": {
                "verdict": self.llm_result.verdict,
                "confidence": self.llm_result.confidence,
                "smishing_type": self.llm_result.smishing_type,
                "analysis": self.llm_result.analysis,
                "danger_points": self.llm_result.danger_points,
                "action_guide": self.llm_result.action_guide,
            },
        }


_ACTION_GUIDE = {
    "BLOCK":      "즉시 문자를 삭제하고 링크를 클릭하지 마세요. 발신 번호를 차단하고, 이미 링크를 눌렀다면 한국인터넷진흥원(118)에 신고하세요.",
    "SUSPICIOUS": "링크 클릭 전 해당 기관 공식 번호로 직접 전화해 사실을 확인하세요. 개인정보나 금융 정보는 절대 입력하지 마세요.",
    "SAFE":       "현재 스미싱 패턴이 탐지되지 않았습니다. 그래도 출처가 불분명한 링크 클릭은 주의하세요.",
}


def _verdict_from_confidence(confidence: float) -> str:
    if confidence >= 0.75:
        return "BLOCK"
    if confidence >= 0.40:
        return "SUSPICIOUS"
    return "SAFE"


def scan(text: str) -> ScanReport:
    text = text.strip()
    result = llm_classifier.classify(text)
    verdict = _verdict_from_confidence(result.confidence)
    result.action_guide = _ACTION_GUIDE[verdict]
    return ScanReport(
        text=text,
        llm_result=result,
        final_verdict=verdict,
        final_score=result.confidence,
    )
