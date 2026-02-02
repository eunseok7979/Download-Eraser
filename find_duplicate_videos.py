# -*- coding: utf-8 -*-
"""
중복 동영상 파일 탐지 스크립트
- 1차: 영상 길이(duration)가 같은 파일들을 그룹화
- 2차: 최초 10초 프레임의 이미지 해시를 비교하여 중복 판정
"""

import os
import sys
import warnings

# OpenCV 경고 억제
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
warnings.filterwarnings("ignore")

import cv2
import imagehash
from PIL import Image
from collections import defaultdict
from pathlib import Path
import json
from datetime import datetime

# stdout을 UTF-8로 설정
sys.stdout.reconfigure(encoding='utf-8')

# 지원하는 동영상 확장자
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.3gp'}

def get_video_duration(video_path):
    """동영상의 길이(초)를 반환"""
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()

        if fps > 0 and frame_count > 0:
            duration = frame_count / fps
            return round(duration, 2)  # 소수점 2자리까지
        return None
    except Exception:
        return None

def get_frame_hashes(video_path, max_seconds=10, sample_interval=0.5):
    """
    영상의 최초 max_seconds 초 동안 sample_interval 간격으로 프레임을 추출하여 해시 생성
    반환: 해시 리스트
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            cap.release()
            return None

        hashes = []
        max_frames = int(max_seconds * fps)
        frame_interval = int(sample_interval * fps)

        if frame_interval < 1:
            frame_interval = 1

        frame_num = 0
        while frame_num < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if not ret:
                break

            # OpenCV BGR -> RGB 변환 후 PIL Image로
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # 이미지 해시 계산 (perceptual hash)
            h = imagehash.phash(pil_image)
            hashes.append(str(h))

            frame_num += frame_interval

        cap.release()
        return hashes if hashes else None

    except Exception:
        return None

def compare_hash_lists(hashes1, hashes2, threshold=5):
    """
    두 해시 리스트를 비교하여 유사도 판정
    threshold: 해시 간 허용 거리 (낮을수록 엄격)
    반환: (유사여부, 평균 해시 거리)
    """
    if not hashes1 or not hashes2:
        return False, float('inf')

    # 더 짧은 리스트 기준으로 비교
    min_len = min(len(hashes1), len(hashes2))

    total_distance = 0
    for i in range(min_len):
        h1 = imagehash.hex_to_hash(hashes1[i])
        h2 = imagehash.hex_to_hash(hashes2[i])
        total_distance += (h1 - h2)

    avg_distance = total_distance / min_len
    return avg_distance <= threshold, avg_distance

def find_video_files(root_path):
    """지정된 경로에서 모든 동영상 파일 찾기"""
    videos = []
    root = Path(root_path)

    print(f"\n[1단계] 동영상 파일 검색 중: {root_path}", flush=True)

    for path in root.rglob('*'):
        try:
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                videos.append(path)
                if len(videos) % 100 == 0:
                    print(f"  발견된 동영상 수: {len(videos)}개...", flush=True)
        except (PermissionError, OSError):
            continue

    print(f"  총 {len(videos)}개의 동영상 파일 발견", flush=True)
    return videos

def group_by_duration(videos):
    """동영상을 길이별로 그룹화"""
    print(f"\n[2단계] 영상 길이 분석 중...", flush=True)

    duration_groups = defaultdict(list)

    for i, video in enumerate(videos, 1):
        if i % 50 == 0:
            print(f"  진행: {i}/{len(videos)} ({i*100//len(videos)}%)", flush=True)

        duration = get_video_duration(video)
        if duration is not None:
            duration_groups[duration].append(video)

    # 2개 이상의 파일이 있는 그룹만 필터링
    potential_duplicates = {k: v for k, v in duration_groups.items() if len(v) >= 2}

    total_candidates = sum(len(v) for v in potential_duplicates.values())
    print(f"  길이가 같은 파일 그룹: {len(potential_duplicates)}개 (총 {total_candidates}개 파일)", flush=True)

    return potential_duplicates

def group_by_duration_and_folder(videos):
    """동영상을 (폴더, 길이) 기준으로 그룹화 - 같은 폴더 내에서만 비교"""
    print(f"\n[2단계] 영상 길이 분석 중 (같은 폴더 내 비교 모드)...", flush=True)

    # (폴더경로, 영상길이) -> [파일목록]
    folder_duration_groups = defaultdict(list)

    for i, video in enumerate(videos, 1):
        if i % 50 == 0:
            print(f"  진행: {i}/{len(videos)} ({i*100//len(videos)}%)", flush=True)

        duration = get_video_duration(video)
        if duration is not None:
            folder = str(video.parent)
            folder_duration_groups[(folder, duration)].append(video)

    # 2개 이상의 파일이 있는 그룹만 필터링
    potential_duplicates = {k: v for k, v in folder_duration_groups.items() if len(v) >= 2}

    total_candidates = sum(len(v) for v in potential_duplicates.values())
    unique_folders = len(set(k[0] for k in potential_duplicates.keys()))
    print(f"  같은 폴더+길이 그룹: {len(potential_duplicates)}개 ({unique_folders}개 폴더, 총 {total_candidates}개 파일)", flush=True)

    return potential_duplicates

def find_duplicates_in_group(videos, threshold=5):
    """
    같은 길이를 가진 동영상들 중에서 실제 중복 찾기
    반환: [(원본, 중복본, 유사도), ...]
    """
    duplicates = []
    processed = set()
    hash_cache = {}

    for i, video1 in enumerate(videos):
        if str(video1) in processed:
            continue

        # 해시 캐싱
        if str(video1) not in hash_cache:
            hash_cache[str(video1)] = get_frame_hashes(video1)
        hashes1 = hash_cache[str(video1)]

        if not hashes1:
            continue

        for video2 in videos[i+1:]:
            if str(video2) in processed:
                continue

            if str(video2) not in hash_cache:
                hash_cache[str(video2)] = get_frame_hashes(video2)
            hashes2 = hash_cache[str(video2)]

            if not hashes2:
                continue

            is_similar, avg_distance = compare_hash_lists(hashes1, hashes2, threshold)

            if is_similar:
                # 파일 크기가 큰 것을 원본으로 간주
                try:
                    size1 = video1.stat().st_size
                    size2 = video2.stat().st_size
                except OSError:
                    continue

                if size1 >= size2:
                    original, duplicate = video1, video2
                    orig_size, dup_size = size1, size2
                else:
                    original, duplicate = video2, video1
                    orig_size, dup_size = size2, size1

                duplicates.append({
                    'original': str(original),
                    'duplicate': str(duplicate),
                    'original_size': orig_size,
                    'duplicate_size': dup_size,
                    'similarity': round(avg_distance, 2)
                })
                processed.add(str(duplicate))

    return duplicates

def format_size(size_bytes):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def main():
    # 검색 경로 설정
    search_path = "F:\\"

    if len(sys.argv) > 1:
        search_path = sys.argv[1]

    if not os.path.exists(search_path):
        print(f"오류: 경로를 찾을 수 없습니다: {search_path}", flush=True)
        return

    print("=" * 60, flush=True)
    print("중복 동영상 탐지 프로그램", flush=True)
    print("=" * 60, flush=True)
    print(f"검색 경로: {search_path}", flush=True)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # 1. 동영상 파일 찾기
    videos = find_video_files(search_path)

    if not videos:
        print("동영상 파일을 찾을 수 없습니다.", flush=True)
        return

    # 2. (폴더, 길이)별로 그룹화 - 같은 폴더 내에서만 비교
    duration_groups = group_by_duration_and_folder(videos)

    if not duration_groups:
        print("중복 후보 파일이 없습니다.", flush=True)
        return

    # 3. 각 그룹에서 실제 중복 찾기
    print(f"\n[3단계] 프레임 비교로 중복 확인 중 (같은 폴더 내에서만)...", flush=True)

    all_duplicates = []
    group_num = 0
    total_groups = len(duration_groups)

    for (folder, duration), group_videos in duration_groups.items():
        group_num += 1
        folder_name = os.path.basename(folder) or folder
        print(f"  그룹 {group_num}/{total_groups}: [{folder_name}] 길이 {duration}초, {len(group_videos)}개 파일 비교 중...", flush=True)

        duplicates = find_duplicates_in_group(group_videos)
        all_duplicates.extend(duplicates)

        if duplicates:
            print(f"    -> {len(duplicates)}쌍 중복 발견!", flush=True)

    # 4. 결과 출력
    print("\n" + "=" * 60, flush=True)
    print("검색 결과", flush=True)
    print("=" * 60, flush=True)

    if not all_duplicates:
        print("중복 동영상을 찾지 못했습니다.", flush=True)
        return

    print(f"총 {len(all_duplicates)}쌍의 중복 동영상 발견\n", flush=True)

    total_recoverable = 0

    for i, dup in enumerate(all_duplicates, 1):
        print(f"[{i}] 중복 발견 (유사도 거리: {dup['similarity']})", flush=True)
        print(f"  원본:   {dup['original']}", flush=True)
        print(f"          크기: {format_size(dup['original_size'])}", flush=True)
        print(f"  중복본: {dup['duplicate']}", flush=True)
        print(f"          크기: {format_size(dup['duplicate_size'])}", flush=True)
        print(f"  절약 가능: {format_size(dup['duplicate_size'])}", flush=True)
        print(flush=True)
        total_recoverable += dup['duplicate_size']

    print("=" * 60, flush=True)
    print(f"총 절약 가능 용량: {format_size(total_recoverable)}", flush=True)
    print("=" * 60, flush=True)

    # 5. 결과를 JSON 파일로 저장
    result_file = Path(__file__).parent / f"duplicate_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'search_path': search_path,
            'scan_time': datetime.now().isoformat(),
            'total_videos_scanned': len(videos),
            'duplicates_found': len(all_duplicates),
            'total_recoverable_bytes': total_recoverable,
            'duplicates': all_duplicates
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과가 저장되었습니다: {result_file}", flush=True)
    print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


def save_folder_result(results_dir, folder_path, folder_duplicates, folder_stats):
    """폴더별 결과를 개별 JSON 파일로 저장"""
    # 폴더 이름에서 파일명으로 사용할 수 없는 문자 제거
    folder_name = os.path.basename(folder_path) or "root"
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in folder_name)

    result_file = results_dir / f"{safe_name}.json"

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'folder_path': folder_path,
            'scan_time': datetime.now().isoformat(),
            'files_compared': folder_stats['files_compared'],
            'duplicates_found': len(folder_duplicates),
            'recoverable_bytes': folder_stats['recoverable_bytes'],
            'duplicates': folder_duplicates
        }, f, ensure_ascii=False, indent=2)

    return result_file


def main_incremental():
    """폴더별로 결과를 저장하며 진행하는 버전"""
    # 검색 경로 설정
    search_path = "E:\\"

    if len(sys.argv) > 1:
        search_path = sys.argv[1]

    if not os.path.exists(search_path):
        print(f"오류: 경로를 찾을 수 없습니다: {search_path}", flush=True)
        return

    print("=" * 60, flush=True)
    print("중복 동영상 탐지 프로그램 (폴더별 저장 모드)", flush=True)
    print("=" * 60, flush=True)
    print(f"검색 경로: {search_path}", flush=True)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # 결과 저장 디렉토리 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = Path(__file__).parent / f"results_{timestamp}"
    results_dir.mkdir(exist_ok=True)
    print(f"결과 저장 폴더: {results_dir}", flush=True)

    # 1. 동영상 파일 찾기
    videos = find_video_files(search_path)

    if not videos:
        print("동영상 파일을 찾을 수 없습니다.", flush=True)
        return

    # 2. (폴더, 길이)별로 그룹화
    duration_groups = group_by_duration_and_folder(videos)

    if not duration_groups:
        print("중복 후보 파일이 없습니다.", flush=True)
        return

    # 폴더별로 그룹 재정리
    folders_to_process = defaultdict(list)
    for (folder, duration), group_videos in duration_groups.items():
        folders_to_process[folder].append((duration, group_videos))

    # 이미 처리된 폴더 확인 (재개 기능)
    completed_folders = set()
    for existing_file in results_dir.glob("*.json"):
        if existing_file.name != "summary.json":
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'folder_path' in data:
                        completed_folders.add(data['folder_path'])
            except:
                pass

    if completed_folders:
        print(f"\n이미 처리된 폴더: {len(completed_folders)}개 (스킵)", flush=True)

    # 3. 폴더별로 처리
    print(f"\n[3단계] 프레임 비교로 중복 확인 중 (폴더별 저장)...", flush=True)

    total_folders = len(folders_to_process)
    all_duplicates = []
    total_recoverable = 0

    for folder_idx, (folder, duration_groups_list) in enumerate(folders_to_process.items(), 1):
        folder_name = os.path.basename(folder) or folder

        # 이미 처리된 폴더는 스킵
        if folder in completed_folders:
            print(f"\n[{folder_idx}/{total_folders}] [{folder_name}] - 이미 처리됨, 스킵", flush=True)
            continue

        print(f"\n[{folder_idx}/{total_folders}] [{folder_name}] 처리 중...", flush=True)

        folder_duplicates = []
        folder_files_compared = 0
        folder_recoverable = 0

        for duration, group_videos in duration_groups_list:
            print(f"  - 길이 {duration}초, {len(group_videos)}개 파일 비교 중...", flush=True)
            folder_files_compared += len(group_videos)

            duplicates = find_duplicates_in_group(group_videos)

            if duplicates:
                print(f"    -> {len(duplicates)}쌍 중복 발견!", flush=True)
                folder_duplicates.extend(duplicates)
                for dup in duplicates:
                    folder_recoverable += dup['duplicate_size']

        # 폴더 결과 저장
        folder_stats = {
            'files_compared': folder_files_compared,
            'recoverable_bytes': folder_recoverable
        }

        saved_file = save_folder_result(results_dir, folder, folder_duplicates, folder_stats)
        print(f"  => 저장됨: {saved_file.name} ({len(folder_duplicates)}쌍, {format_size(folder_recoverable)} 절약 가능)", flush=True)

        all_duplicates.extend(folder_duplicates)
        total_recoverable += folder_recoverable

    # 4. 전체 요약 파일 저장
    summary_file = results_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'search_path': search_path,
            'scan_time': datetime.now().isoformat(),
            'total_videos_scanned': len(videos),
            'total_folders_processed': total_folders,
            'duplicates_found': len(all_duplicates),
            'total_recoverable_bytes': total_recoverable,
            'total_recoverable_formatted': format_size(total_recoverable),
            'duplicates': all_duplicates
        }, f, ensure_ascii=False, indent=2)

    # 5. 최종 결과 출력
    print("\n" + "=" * 60, flush=True)
    print("검색 완료!", flush=True)
    print("=" * 60, flush=True)
    print(f"총 {len(all_duplicates)}쌍의 중복 동영상 발견", flush=True)
    print(f"총 절약 가능 용량: {format_size(total_recoverable)}", flush=True)
    print(f"\n결과 폴더: {results_dir}", flush=True)
    print(f"요약 파일: {summary_file}", flush=True)
    print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == "__main__":
    # main()  # 기존 버전
    main_incremental()  # 폴더별 저장 버전
