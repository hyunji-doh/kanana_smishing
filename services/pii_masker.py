"""
PII(개인식별정보) 마스킹 모듈
Kanana-o API 전송 전에 개인정보를 토큰으로 치환.
원문은 로컬에만 보관하고, API에는 마스킹본만 전달.

Kanana-o API 이용 약관 준수:
- 이름/전화번호/이메일/주소/계좌번호/주민번호 등 개인정보 전송 금지
"""
import re
from dataclasses import dataclass, field


@dataclass
class MaskResult:
    masked_text: str                          # API에 전송할 마스킹된 텍스트
    replacements: dict[str, str] = field(default_factory=dict)  # 토큰 → 원본 (로컬 전용)
    pii_found: list[str] = field(default_factory=list)           # 발견된 PII 유형 목록


# (토큰, 설명, 패턴) 순서대로 정의
# 순서 중요: 주민번호처럼 더 구체적인 패턴을 먼저 배치
_PII_RULES: list[tuple[str, str, str]] = [
    # 주민등록번호 (6자리-7자리) — 가장 먼저 처리
    (
        "[SSN]",
        "주민등록번호",
        r"\b\d{6}[-\s]?\d{7}\b",
    ),
    # 한국 전화번호 (010-xxxx-xxxx, 02-xxx-xxxx 등) — 계좌번호보다 먼저
    (
        "[PHONE]",
        "전화번호",
        r"(?<!\d)(0\d{1,2})[-\s.]?(\d{3,4})[-\s.]?(\d{4})(?!\d)",
    ),
    # 신용카드번호 (4자리-4자리-4자리-4자리) — 계좌번호보다 더 구체적이므로 먼저
    (
        "[CARD]",
        "카드번호",
        r"\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b",
    ),
    # 계좌번호 (은행 계좌 형태: 숫자-숫자-숫자, 전화번호·카드번호 처리 후 남은 패턴)
    (
        "[ACCOUNT]",
        "계좌번호",
        r"\b\d{3,6}[-\s]\d{2,6}[-\s]\d{2,7}\b",
    ),
    # 이메일
    (
        "[EMAIL]",
        "이메일",
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    ),
    # IP 주소
    (
        "[IP]",
        "IP주소",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    ),
    # 한국 주소 패턴 (시/도 + 구/군/시)
    (
        "[ADDRESS]",
        "주소",
        r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*(?:특별시|광역시|특별자치시|도)?\s*\S+(?:구|군|시)\s*\S+(?:동|읍|면|로|길)\s*\d+",
    ),
    # 한국인 이름 패턴 (성씨 + 1~2글자, 홍길동 형태)
    # 너무 광범위하면 오탐이 많아서 명시적 앞뒤 문맥 패턴만 잡음
    (
        "[NAME]",
        "이름",
        r"(?:이름|성명|담당자|작성자|신청인|수신인|발신인)[\s:：]*([가-힣]{2,4})",
    ),
]

_COMPILED_RULES: list[tuple[str, str, re.Pattern]] = [
    (token, desc, re.compile(pattern, re.IGNORECASE | re.UNICODE))
    for token, desc, pattern in _PII_RULES
]


def mask(text: str) -> MaskResult:
    """
    텍스트에서 PII를 탐지하고 토큰으로 치환.
    반환값의 masked_text만 API로 전송하고,
    replacements는 절대 외부로 전송하지 말 것.
    """
    result = MaskResult(masked_text=text)
    counters: dict[str, int] = {}

    for token, desc, pattern in _COMPILED_RULES:
        def _replacer(m: re.Match, _token: str = token, _desc: str = desc) -> str:
            base = _token.rstrip("]")
            n = counters.get(_token, 0)
            counters[_token] = n + 1
            numbered = f"{base}_{n}]" if n > 0 else _token
            result.replacements[numbered] = m.group(0)
            if _desc not in result.pii_found:
                result.pii_found.append(_desc)
            return numbered

        result.masked_text = pattern.sub(_replacer, result.masked_text)

    return result


def has_pii(text: str) -> bool:
    """PII 포함 여부만 빠르게 확인 (마스킹 없이)"""
    return any(pattern.search(text) for _, _, pattern in _COMPILED_RULES)
