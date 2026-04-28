"""
Kanana-o 스미싱 보안 평가기
한국어 특화 모델이 단독으로 문자 메시지를 분석하고 판정
"""
import re
from dataclasses import dataclass
import kanana_client


@dataclass
class LLMResult:
    verdict: str        # SAFE / SUSPICIOUS / BLOCK
    confidence: float   # 0.0 ~ 1.0
    smishing_type: str  # 수법 유형
    analysis: str       # 상세 분석 (자유형식 한국어)
    danger_points: list[str]   # 위험 요소 목록
    action_guide: str   # 사용자 행동 지침
    raw: str            # 원본 응답


_PROMPT_TEMPLATE = """너는 한국 스미싱(SMS 피싱) 보안 전문가야. 아래 문자 메시지를 철저히 분석해줘.

[분석할 문자]
{text}

다음 항목을 순서대로 작성해:

1. **발신자 사칭 분석**
   누구를 사칭하는지, 한국에서 실제로 사용되는 기관·기업 명칭과 비교해서 설명해.

2. **언어·표현 분석**
   한국어 표현이 자연스러운지, 실제 해당 기관이 쓸 법한 문체인지, 번역체나 어색한 표현이 있는지 분석해.

3. **URL·링크 위험도**
   포함된 URL이 있다면 도메인 구조, 단축 URL 여부, 정상 기관 도메인과의 차이를 분석해.

4. **사회공학 기법**
   긴박감 조성, 공포 유발, 권위 이용, 호기심 자극 등 어떤 심리 조작 기법이 사용됐는지 설명해.

5. **종합 판정**
   위 분석을 바탕으로 스미싱 여부와 수법을 명확히 정리해.

분석을 마친 후, 반드시 마지막에 아래 두 줄을 정확히 출력해:
DANGER: <위험 요소를 세미콜론(;)으로 구분한 목록. 없으면 없음>
VERDICT: <SAFE 또는 SUSPICIOUS 또는 BLOCK> | CONFIDENCE: <0.0~1.0> | TYPE: <정상 또는 택배사칭 또는 금융사칭 또는 기관사칭 또는 플랫폼사칭 또는 사회공학 또는 복합>"""


def _parse_result(raw: str) -> tuple[str, float, str, list[str]]:
    """VERDICT 줄과 DANGER 줄 파싱"""
    verdict, confidence, stype = "SUSPICIOUS", 0.5, "알 수 없음"
    danger_points = []

    v_match = re.search(
        r"VERDICT\s*:\s*(SAFE|SUSPICIOUS|BLOCK)\s*\|\s*CONFIDENCE\s*:\s*([0-9.]+)\s*\|\s*TYPE\s*:\s*(.+)",
        raw, re.IGNORECASE
    )
    if v_match:
        verdict = v_match.group(1).upper()
        confidence = min(max(float(v_match.group(2)), 0.0), 1.0)
        stype = v_match.group(3).strip()

    d_match = re.search(r"DANGER\s*:\s*(.+)", raw, re.IGNORECASE)
    if d_match:
        raw_danger = d_match.group(1).strip()
        # 세미콜론과 쉼표 모두 구분자로 처리, "없음" 항목 제거
        tokens = re.split(r"[;,]", raw_danger)
        danger_points = [t.strip() for t in tokens if t.strip() and t.strip() != "없음"]

    # 폴백
    if not v_match:
        if re.search(r"스미싱\s*(확실|명백|분명)", raw):
            verdict, confidence = "BLOCK", 0.85
        elif re.search(r"정상\s*(문자|메시지)", raw):
            verdict, confidence = "SAFE", 0.15

    return verdict, confidence, stype, danger_points


def classify(text: str) -> LLMResult:
    prompt = _PROMPT_TEMPLATE.format(text=text)
    messages = [{"role": "user", "content": prompt}]
    raw = kanana_client.chat(messages, temperature=0.2)

    verdict, confidence, smishing_type, danger_points = _parse_result(raw)

    # DANGER / VERDICT 태그 이후 내용 제거 — 줄 중간에 붙어도 처리
    analysis = re.sub(r"\s*DANGER\s*:.*", "", raw, flags=re.IGNORECASE | re.DOTALL)
    analysis = re.sub(r"\s*VERDICT\s*:.*", "", analysis, flags=re.IGNORECASE | re.DOTALL)
    analysis = analysis.strip()

    return LLMResult(
        verdict=verdict,
        confidence=confidence,
        smishing_type=smishing_type,
        analysis=analysis,
        danger_points=danger_points,
        action_guide="",
        raw=raw,
    )
