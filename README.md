# 중복 파일 제거 도구 (Duplicate File Remover)

중복된 파일을 찾아서 제거하는 Python 유틸리티입니다.

## 주요 기능

- ✅ **해시 기반 중복 검사**: SHA256, MD5, SHA1 해시를 사용하여 정확하게 중복 파일 탐지
- 📊 **상세한 정보 제공**: 중복 파일 개수, 절약 가능한 공간 등 통계 정보
- 🔍 **미리보기 모드**: 실제 삭제 전 시뮬레이션으로 안전하게 확인
- 🎯 **보존 전략 선택**: 가장 오래된 파일, 최신 파일, 첫 번째 파일 중 선택하여 보존
- 📝 **로그 기록**: 삭제된 파일 이력을 자동으로 로그 파일에 저장
- 🔄 **재귀 검색**: 하위 디렉토리를 포함한 전체 검색

## 설치 방법

Python 3.6 이상이 필요합니다.

```bash
# 저장소 클론
git clone https://github.com/eunseok7979/Download-Eraser.git
cd Download-Eraser

# 또는 파일을 직접 다운로드하여 사용

추가 패키지 설치는 필요하지 않습니다 (Python 표준 라이브러리만 사용).

사용 방법
기본 사용법
# 1. 중복 파일 찾기 (시뮬레이션 모드)
python duplicate_file_remover.py /path/to/directory

# 2. 중복 파일 목록 보기
python duplicate_file_remover.py /path/to/directory --show

# 3. 중복 파일 실제 삭제 (가장 오래된 파일 보존)
python duplicate_file_remover.py /path/to/directory --remove --keep oldest

Windows에서 사용 예시
# Downloads 폴더에서 중복 파일 찾기
python duplicate_file_remover.py "C:\Users\YourName\Downloads" --show

# OneDrive 폴더에서 중복 파일 삭제 (최신 파일 보존)
python duplicate_file_remover.py "C:\Users\PC\OneDrive\Claude\Download Eraser" --remove --keep newest

Linux/Mac에서 사용 예시
# 홈 디렉토리의 Downloads 폴더
python duplicate_file_remover.py ~/Downloads --show

# 특정 폴더에서 중복 파일 삭제
python duplicate_file_remover.py /path/to/folder --remove --keep oldest

명령어 옵션
옵션	설명	기본값
directory	검색할 디렉토리 경로 (필수)	-
--recursive	하위 디렉토리 포함 검색	True
--hash	해시 알고리즘 선택 (md5, sha1, sha256)	sha256
--show	중복 파일 목록 상세 표시	False
--remove	실제로 파일 삭제 (이 옵션 없으면 시뮬레이션만)	False
--keep	보존 전략 (oldest, newest, first)	oldest
--max-groups	표시할 최대 중복 그룹 수	무제한
보존 전략 설명
oldest: 가장 오래된 파일을 보존하고 나머지 삭제
newest: 가장 최신 파일을 보존하고 나머지 삭제
first: 처음 발견된 파일을 보존하고 나머지 삭제
사용 예시
예시 1: 안전하게 중복 파일 확인
python duplicate_file_remover.py "C:\Users\PC\Downloads" --show

출력:

📂 디렉토리 스캔 중: C:\Users\PC\Downloads
📊 총 1250개 파일 발견
✅ 스캔 완료!

🔍 중복 파일 검색 결과:
  - 중복 파일 그룹: 15개
  - 중복 파일 개수: 32개
  - 절약 가능한 공간: 245.67 MB

================================================================================
📦 중복 그룹 #1 (해시: a3f2d1e4c5b6...)
   파일 크기: 15.23 MB
   중복 개수: 3개
================================================================================
  [1] C:\Users\PC\Downloads\image.jpg
      수정일: 2024-05-15 10:30:45
  [2] C:\Users\PC\Downloads\image(1).jpg
      수정일: 2024-05-15 10:31:22
  [3] C:\Users\PC\Downloads\backup\image.jpg
      수정일: 2024-05-15 10:35:10

예시 2: 시뮬레이션 모드로 삭제 예행연습
python duplicate_file_remover.py "C:\Users\PC\Downloads" --keep newest

출력:

🟡 시뮬레이션 모드 (파일이 삭제되지 않음)
보존 전략: newest

📌 보존: C:\Users\PC\Downloads\backup\image.jpg
  🔄 삭제 예정: C:\Users\PC\Downloads\image.jpg
  🔄 삭제 예정: C:\Users\PC\Downloads\image(1).jpg

================================================================================
📊 요약:
  - 삭제 예정 파일: 32개
  - 확보 가능한 공간: 245.67 MB

예시 3: 실제로 중복 파일 삭제
python duplicate_file_remover.py "C:\Users\PC\Downloads" --remove --keep oldest

출력:

🔴 실제 삭제 모드
보존 전략: oldest

📌 보존: C:\Users\PC\Downloads\image.jpg
  ✅ 삭제됨: C:\Users\PC\Downloads\image(1).jpg
  ✅ 삭제됨: C:\Users\PC\Downloads\backup\image.jpg

================================================================================
📊 요약:
  - 삭제된 파일: 32개
  - 확보된 공간: 245.67 MB

📝 로그 저장됨: C:\Users\PC\.duplicate_remover_logs\removal_log_20260202_153045.txt

안전 기능
시뮬레이션 모드: --remove 옵션 없이 실행하면 파일을 실제로 삭제하지 않습니다
로그 기록: 모든 삭제 작업은 로그 파일에 기록됩니다 (~/.duplicate_remover_logs/)
오류 처리: 파일 읽기/삭제 오류 시 해당 파일을 건너뛰고 계속 진행합니다
로그 파일
삭제된 파일의 이력은 자동으로 저장됩니다:

Windows: C:\Users\YourName\.duplicate_remover_logs\
Linux/Mac: ~/.duplicate_remover_logs/
로그 파일 예시:

Duplicate File Removal Log
================================================================================
Timestamp: 2026-02-02 15:30:45
Directory: C:\Users\PC\Downloads
Total files processed: 32

[2026-02-02T15:30:45] deleted: C:\Users\PC\Downloads\image(1).jpg (15.23 MB)
[2026-02-02T15:30:45] deleted: C:\Users\PC\Downloads\backup\image.jpg (15.23 MB)
...

주의사항
⚠️ 중요:

중복 파일 삭제는 되돌릴 수 없으므로 먼저 시뮬레이션 모드로 확인하세요
중요한 파일이 있는 디렉토리는 백업 후 사용하세요
--show 옵션으로 먼저 중복 파일 목록을 확인하세요
문제 해결
권한 오류
일부 시스템 폴더는 관리자 권한이 필요할 수 있습니다.

Windows: 명령 프롬프트를 관리자 권한으로 실행
Linux/Mac: sudo 사용 (권장하지 않음, 사용자 폴더에서만 사용)

대용량 파일이 많은 경우
MD5 해시가 SHA256보다 빠르므로 속도가 필요한 경우:

python duplicate_file_remover.py /path/to/directory --hash md5

라이선스
MIT License

기여
버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

Made with ❤️ by Claude
