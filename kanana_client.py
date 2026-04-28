"""
Kanana-o API 클라이언트
모든 API 호출을 여기서 관리
"""
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("KANANA_API_KEY"),
            base_url=os.getenv("KANANA_BASE_URL"),
        )
    return _client


MODEL = os.getenv("KANANA_MODEL", "kanana-o")


def chat(messages: list[dict], temperature: float = 0.2) -> str:
    """텍스트 기반 채팅 요청 (쿼터 초과 시 최대 3회 재시도)"""
    import time
    for attempt in range(3):
        try:
            response = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg:
                wait = 10 * (attempt + 1)
                print(f"  [API] 쿼터 제한 - {wait}초 후 재시도 ({attempt+1}/3)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API 쿼터 초과 - 잠시 후 다시 시도하세요.")


def chat_with_image(text: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """이미지 + 텍스트 요청 (쿼터 초과 시 최대 3회 재시도)
    Kanana-o는 data URL 접두사 없이 raw base64 문자열을 사용
    """
    import time
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": b64}},
                {"type": "text", "text": text},
            ],
        }
    ]
    for attempt in range(3):
        try:
            response = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg:
                wait = 10 * (attempt + 1)
                print(f"  [API] 쿼터 제한 - {wait}초 후 재시도 ({attempt+1}/3)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API 쿼터 초과 - 잠시 후 다시 시도하세요.")


def chat_with_audio(
    audio_bytes: bytes,
    fmt: str = "wav",
    prompt: str = "이 오디오에서 사람이 말하는 내용을 한국어로 그대로 받아쓰기(전사)해줘. 설명이나 요약 없이 발화 내용만 출력해.",
) -> str:
    """오디오 입력 → 텍스트 응답 (ASR/SER용, 쿼터 초과 시 최대 3회 재시도)
    prompt: 오디오와 함께 전달할 지시문 (기본값: ASR 변환 요청)
    오디오 출력(스트리밍)은 보안 게이트웨이에서 불필요하므로 미구현
    """
    import time
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    for attempt in range(3):
        try:
            response = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg:
                wait = 10 * (attempt + 1)
                print(f"  [API] 쿼터 제한 - {wait}초 후 재시도 ({attempt+1}/3)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API 쿼터 초과 - 잠시 후 다시 시도하세요.")
