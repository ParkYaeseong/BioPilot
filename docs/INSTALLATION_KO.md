# 설치와 오프라인 재현

2026-11-02 확인. Windows / Python 3.14.0의 **새 가상환경과 별도 소스 복사본**에서
통합 UI의 5개 결과 화면과 로컬 입력 검증을 확인했습니다. 기존 설치 패키지, 개인
인증정보, 모델 가중치를 복사하지 않았습니다. 다른 PC/운영체제 검증이나 새 실시간
추론 검증은 아닙니다. [검증 영수증](../validation/clean_workbench_reproduction_20261102.json).

## 설치와 실행

저장소를 받은 폴더의 PowerShell에서 실행합니다. Python 3.14를 먼저 설치해야 합니다.
아래 설치는 공개 Python 패키지를 받으며 Meta/ESM 모델을 호출하거나 내려받지 않습니다.
기존 작업용 `.venv`가 있다면 덮어쓰지 말고 별도 체크아웃에서 실행하세요.

```powershell
py -3.14 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/workbench-win-py314.lock.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe checks/check_reproduction.py
.venv/Scripts/python.exe -m streamlit run app/bench.py --server.headless true --browser.gatherUsageStats false --server.address 127.0.0.1 --server.port 8522 -- --state-dir .runtime/judge-review --artifact examples/artifacts/unified_review_20261029.replay.json
```

`--server.headless true`는 새 설치의 Streamlit 이메일 안내가 서버 시작을 막지 않도록 합니다.
주소는 http://127.0.0.1:8522/ 입니다. `python -m streamlit`을 사용합니다.
`streamlit.exe run`만 쓰면 프로젝트의 `app` 모듈을 찾지 못할 수 있습니다.
검증된 전이 의존성 버전은 lock 파일에 있습니다. 최소 직접 의존성 목록은
`requirements/workbench.txt`이며, 별도 읽기 전용 뷰어는 `requirements/viewer.txt`입니다.

## 확인할 동작

1. 기본 Overview에서 실제 저장된 후보 19개와 REPLAY 표시를 확인합니다.
2. Candidates / Structure / Agent Trace / Evidence를 엽니다. 저장된 결과만 탐색합니다.
3. New review → Download example FASTA → Upload FASTA로 해당 파일을 올립니다.
4. `Review S108A for sequence plausibility.` → Validate input: 보호 잔기로 거부됩니다.
5. `Review A32V for sequence plausibility.` → Validate input: 로컬 검증을 통과합니다.
6. 모델 설정이 없는 새 환경에서는 Execute가 비활성입니다. 가이드는 실행 권한을 주지 않습니다.

실행은 등록된 공개 Lipase A 전체 212개 기준 서열만 지원합니다. 임의 단백질이나
181개 mature 서열을 지원한다고 해석하지 마세요. 선택적 구조 업로드도 고정된 공개
1ISP mmCIF만 허용합니다. Structure는 저장된 구조와 확인된 잔기 대응을 표시하며,
A32는 기준 실험 구조에 원자가 없으므로 임의 위치를 표시하지 않습니다.

## 실제 새 실행과의 구분

위 설치는 **저장 결과와 로컬 입력 검증용**입니다. Meta/MCP/ESM 새 실행에는
`requirements/dev.txt`, `requirements/science.txt`, 별도로 검증한 Meta 설정·사용자 본인의
인증정보·해시를 고정한 로컬 ESM 체크포인트와 명시적 승인이 필요합니다.
이 문서는 새 환경의 유료/과학 계산 경로까지 검증했다고 주장하지 않습니다.
설정 방식과 실행 범위는 [통합 작업 안내](../docs/UNIFIED_WORKBENCH_KO.md)를 보세요.
작성자의 키나 `.env`, `.runtime`, `.cache`를 심사자에게 전달하지 않습니다.

확인 스크립트는 임시 로컬 저널을 사용하고 실행 경계를 차단한 Streamlit AppTest입니다.
브라우저의 3D/WebGL·spotlight JavaScript·실제 파일 선택 창을 검증하는 스크린캐스트는
아닙니다. 새 환경의 브라우저 수동 점검은 별도로 기록합니다.
