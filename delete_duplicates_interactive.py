# -*- coding: utf-8 -*-
"""
중복 동영상 대화형 삭제 스크립트
- 각 중복 쌍마다 상세 정보를 보여주고
- 사용자가 어느 파일을 삭제할지 선택
"""

import json
import os
import sys
from pathlib import Path
from send2trash import send2trash

# stdout을 UTF-8로 설정
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

def format_size(size_bytes):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_folder_name(file_path):
    """파일이 속한 폴더명 반환"""
    return Path(file_path).parent.name

def get_parent_folders(file_path, depth=2):
    """상위 폴더 경로 반환 (depth 단계까지)"""
    path = Path(file_path)
    parts = path.parts
    if len(parts) > depth + 1:
        return "\\".join(parts[-(depth+1):-1])
    return str(path.parent)

def analyze_duplicate_type(dup):
    """중복 유형 분석"""
    orig_size = dup['original_size']
    dup_size = dup['duplicate_size']
    similarity = dup['similarity']

    size_diff = abs(orig_size - dup_size)
    size_diff_percent = (size_diff / max(orig_size, dup_size)) * 100 if max(orig_size, dup_size) > 0 else 0

    reasons = []

    # 크기 분석
    if size_diff == 0:
        reasons.append("완전히 동일한 파일 (크기 100% 일치)")
    elif size_diff_percent < 1:
        reasons.append(f"거의 동일한 파일 (크기 차이 {size_diff_percent:.2f}%)")
    elif size_diff_percent < 10:
        reasons.append(f"유사한 인코딩 (크기 차이 {size_diff_percent:.1f}%)")
    else:
        if orig_size > dup_size:
            reasons.append(f"중복본이 저화질 버전 (크기 {size_diff_percent:.0f}% 작음)")
        else:
            reasons.append(f"원본이 저화질 버전 (크기 {size_diff_percent:.0f}% 작음)")

    # 유사도 분석
    if similarity == 0:
        reasons.append("영상 내용 완전 일치 (해시 거리: 0)")
    elif similarity <= 2:
        reasons.append(f"영상 내용 거의 일치 (해시 거리: {similarity})")
    else:
        reasons.append(f"영상 내용 유사 (해시 거리: {similarity})")

    return reasons

def print_separator():
    print("\n" + "=" * 70)

def print_file_info(label, file_path, size, marker=""):
    """파일 정보 출력"""
    folder = get_parent_folders(file_path, 2)
    filename = Path(file_path).name

    print(f"\n  [{label}]{marker}")
    print(f"    파일명: {filename}")
    print(f"    폴더:   {folder}")
    print(f"    크기:   {format_size(size)}")
    print(f"    전체경로: {file_path}")

def main():
    # 결과 파일 찾기
    script_dir = Path(__file__).parent
    result_files = list(script_dir.glob("duplicate_results_*.json"))

    if not result_files:
        print("중복 검사 결과 파일을 찾을 수 없습니다.")
        print("먼저 find_duplicate_videos.py를 실행하세요.")
        return

    # 가장 최근 결과 파일 사용
    result_file = max(result_files, key=lambda f: f.stat().st_mtime)

    print("=" * 70)
    print("중복 동영상 대화형 삭제 프로그램")
    print("=" * 70)
    print(f"\n결과 파일: {result_file.name}")

    # JSON 로드
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    duplicates = data['duplicates']
    total = len(duplicates)

    print(f"총 {total}쌍의 중복 발견")
    print(f"예상 절약 용량: {format_size(data['total_recoverable_bytes'])}")

    print("\n[안내]")
    print("  각 중복 쌍을 보여드립니다.")
    print("  1 = 파일1 삭제 (휴지통으로)")
    print("  2 = 파일2 삭제 (휴지통으로)")
    print("  s = 건너뛰기 (삭제 안 함)")
    print("  q = 종료")
    print("  a = 모두 건너뛰기 (나머지 전부 스킵)")

    input("\n준비되셨으면 Enter를 눌러 시작하세요...")

    deleted_count = 0
    deleted_size = 0
    skipped_count = 0
    skip_all = False

    for i, dup in enumerate(duplicates, 1):
        if skip_all:
            skipped_count += 1
            continue

        orig_path = dup['original']
        dup_path = dup['duplicate']
        orig_size = dup['original_size']
        dup_size = dup['duplicate_size']

        # 파일 존재 확인
        orig_exists = os.path.exists(orig_path)
        dup_exists = os.path.exists(dup_path)

        if not orig_exists and not dup_exists:
            print(f"\n[{i}/{total}] 두 파일 모두 존재하지 않음 - 건너뜀")
            skipped_count += 1
            continue
        elif not orig_exists:
            print(f"\n[{i}/{total}] 파일1이 존재하지 않음 - 건너뜀")
            skipped_count += 1
            continue
        elif not dup_exists:
            print(f"\n[{i}/{total}] 파일2가 존재하지 않음 - 건너뜀")
            skipped_count += 1
            continue

        print_separator()
        print(f"[{i}/{total}] 중복 발견")

        # 중복 유형 분석
        reasons = analyze_duplicate_type(dup)
        print("\n  [판단 근거]")
        for reason in reasons:
            print(f"    • {reason}")

        # 추천 표시 (크기가 작은 쪽 삭제 추천)
        if orig_size > dup_size:
            recommend = "2"
            print(f"\n  [추천] 파일2 삭제 (저화질/작은 파일)")
        elif orig_size < dup_size:
            recommend = "1"
            print(f"\n  [추천] 파일1 삭제 (저화질/작은 파일)")
        else:
            recommend = "2"
            print(f"\n  [추천] 파일2 삭제 (동일 크기, 아무거나)")

        # 파일 정보 출력
        marker1 = " ← 추천 삭제" if recommend == "1" else ""
        marker2 = " ← 추천 삭제" if recommend == "2" else ""

        print_file_info("파일1", orig_path, orig_size, marker1)
        print_file_info("파일2", dup_path, dup_size, marker2)

        # 크기 차이 표시
        size_diff = abs(orig_size - dup_size)
        if size_diff > 0:
            print(f"\n  크기 차이: {format_size(size_diff)}")

        # 사용자 입력
        while True:
            choice = input("\n  선택 (1/2/s/q/a): ").strip().lower()

            if choice == '1':
                try:
                    send2trash(orig_path)
                    print(f"  ✓ 파일1을 휴지통으로 이동했습니다.")
                    deleted_count += 1
                    deleted_size += orig_size
                except Exception as e:
                    print(f"  ✗ 삭제 실패: {e}")
                break

            elif choice == '2':
                try:
                    send2trash(dup_path)
                    print(f"  ✓ 파일2를 휴지통으로 이동했습니다.")
                    deleted_count += 1
                    deleted_size += dup_size
                except Exception as e:
                    print(f"  ✗ 삭제 실패: {e}")
                break

            elif choice == 's':
                print("  → 건너뜁니다.")
                skipped_count += 1
                break

            elif choice == 'q':
                print("\n프로그램을 종료합니다.")
                print_separator()
                print(f"삭제된 파일: {deleted_count}개")
                print(f"절약된 용량: {format_size(deleted_size)}")
                print(f"건너뛴 항목: {skipped_count}개")
                print(f"처리 안 됨: {total - i}개")
                return

            elif choice == 'a':
                print("  → 나머지 모두 건너뜁니다.")
                skip_all = True
                skipped_count += 1
                break

            elif choice == '':
                # 엔터만 누르면 추천대로
                if recommend == "1":
                    try:
                        send2trash(orig_path)
                        print(f"  ✓ 파일1을 휴지통으로 이동했습니다. (추천대로)")
                        deleted_count += 1
                        deleted_size += orig_size
                    except Exception as e:
                        print(f"  ✗ 삭제 실패: {e}")
                else:
                    try:
                        send2trash(dup_path)
                        print(f"  ✓ 파일2를 휴지통으로 이동했습니다. (추천대로)")
                        deleted_count += 1
                        deleted_size += dup_size
                    except Exception as e:
                        print(f"  ✗ 삭제 실패: {e}")
                break

            else:
                print("  잘못된 입력입니다. 1, 2, s, q, a 중에서 선택하세요.")

    # 최종 결과
    print_separator()
    print("모든 항목 처리 완료!")
    print_separator()
    print(f"삭제된 파일: {deleted_count}개")
    print(f"절약된 용량: {format_size(deleted_size)}")
    print(f"건너뛴 항목: {skipped_count}개")
    print("=" * 70)

if __name__ == "__main__":
    main()
