"""
1단계: API 연결 테스트
실행: python test_connection.py
"""
import sys
from kanana_client import chat


def test_text():
    print("=" * 50)
    print("[테스트 1] 텍스트 응답")
    print("=" * 50)
    response = chat([
        {"role": "user", "content": "안녕하세요! 간단히 자기소개 해줘."}
    ])
    print(response)
    print()


def test_image():
    """이미지 테스트는 실제 이미지 파일이 있을 때 실행"""
    import pathlib
    sample_path = pathlib.Path("samples/test_image.jpg")
    if not sample_path.exists():
        print("[테스트 2] 이미지 파일 없음 - samples/test_image.jpg 를 넣어주세요")
        return

    from kanana_client import chat_with_image
    image_bytes = sample_path.read_bytes()
    print("=" * 50)
    print("[테스트 2] 이미지 내 텍스트 추출")
    print("=" * 50)
    response = chat_with_image(
        "이 이미지 안에 보이는 텍스트를 모두 추출해줘.",
        image_bytes,
        "image/jpeg",
    )
    print(response)
    print()


if __name__ == "__main__":
    try:
        test_text()
        test_image()
        print("✅ 연결 테스트 완료")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)
