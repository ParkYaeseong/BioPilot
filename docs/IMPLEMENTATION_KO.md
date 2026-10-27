# 로컬 구현 실행 안내 — 2026-10-27

제품 코드와 로컬 통합 테스트를 구현했습니다. 실제 ESM 추론·Modal GPU 통합·실험 정답
평가까지 완료한 제품은 아닙니다. 브랜치는 `implementation/mcp-core-20261027`이며,
원본은 기준 커밋 `5898a2f`와 `compliance/original_package_manifest.sha256`에 보존했습니다.
`BioPilot_Atlas_Local_Start`는 제품에 포함하지 않는 보조 도구입니다.

## 환경과 오프라인 실행

현재 Windows/Python 3.14.0, MCP 1.25.0, PyTorch 2.9.1+cpu, Transformers 5.2.0입니다.
`.venv`는 이미 설치된 패키지를 재사용하는 `--system-site-packages` 환경입니다.
깨끗한 환경 재설치는 미검증이며 직접 의존성은 `requirements-dev.txt`, 과학 런타임은
`requirements-science.txt`에 고정했습니다. Modal SDK 1.6.2는 `.venv`에 설치하여 오프라인
API 형식을 확인했습니다(`requirements-modal.txt`). 로컬 CUDA는 사용할 수 없습니다.

아래 명령은 프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.venv/Scripts/python.exe -m app.cli validate --variant A32V
.venv/Scripts/python.exe -m app.cli validate --variant S108A
.venv/Scripts/python.exe -m app.cli esm-status
.venv/Scripts/python.exe -m app.cli prepare --workspace .runtime/demo_session
.venv/Scripts/python.exe -m app.cli mcp-smoke --workspace .runtime/demo_session
.venv/Scripts/python.exe -m app.cli status --workspace .runtime/demo_session
.venv/Scripts/python.exe -m pytest tests tests_app -q
.venv/Scripts/python.exe checks/validate_package.py
```

`S108A`는 보호 잔기라 차단됩니다. 현재 `esm-status`도 Modal 미설정·미승인으로
`unconfigured`와 종료 코드 2를 반환합니다. `prepare`는 새 폴더만 만들고 기존 실행을
덮어쓰지 않습니다. MCP 검사는 실제 로컬 stdio 호출이며 외부 API/GPU를 사용하지 않습니다.
SDK 1.25.0이 협상한 프로토콜은 2025-11-25입니다.

## 제공자와 점수

```text
Muse Spark -> MCP score_positions -> InferenceService -> ESMInferenceProvider
                                                  -> LocalESMProvider
                                                  -> ModalESMProvider
                                                  -> RunPodESMProvider (unconfigured)
```

`.env` 또는 환경변수의 `ESM_BACKEND=modal|local|runpod`로 선택합니다. 기본 Modal 선택은
실행 권한을 부여하지 않습니다. RunPod는 같은 인터페이스에서 명확한 미설정 오류만 냅니다.
로컬 장치는 `ESM_DEVICE=cpu|cuda`로 명시하고 자동 fallback하지 않습니다.
설정 예시는 `.env.example`입니다. 실제 `.env` 위에 복사하지 말고 기존 키를 보존하세요.
Meta 키는 `MODEL_API_KEY`와 `META_API_KEY`를 지원하며 로그·worker 요청에 포함하지 않습니다.

| 키 | 체크포인트 | 순위 정책 |
|---|---|---|
| esm35 | esm2_t12_35M_UR50D | esm35_masked_v1 |
| esm150 | esm2_t30_150M_UR50D | esm150_masked_v1 |
| esm650 | esm2_t33_650M_UR50D | esm650_masked_v1 |

35M/150M은 개발에, 650M은 명시적으로 고정한 주요 독립 평가에 사용할 수 있습니다.
기존 기본 기준선은 150M입니다. 일부 후보만 다른 모델 점수로 교체하거나 모델을 섞어
순위를 바꾸지 않습니다. 같은 코호트·문맥·가중치·정책을 정답 열람 전에 고정합니다.

점수는 전체 212개 서열에서 위치 i를 마스킹한
`log P(mutant | mask) - log P(WT | mask)`이며 logit 차이와 같습니다.
위치당 19개 대안을 재사용하고 실행 전체 최대 200개 후보를 허용합니다.
전체 기준 1-based 번호, S108/D164/H187 보호와 실제 토크나이저 정렬을 검사합니다.
점수는 단위 없는 서열 선호도입니다. T50·활성·Tm·기능 유지의 측정값이 아니며 원자 좌표
기능은 계속 차단되어 있습니다. CPU/GPU 수치 일치의 실제 허용오차 검사는 아직 하지 않았습니다.

## 실제 추론 전제와 실행 경로

가중치를 다운로드하지 않았습니다. 로컬 safetensors와 신뢰된 설치 기록의 가중치·
토크나이저 해시가 필요합니다. `LocalHFBackend`는 local-only 로딩, architecture와 해시를
검사하고 누락된 가중치의 무작위 초기화를 거부합니다. 핀은 파일명→SHA256 매핑의
정렬된 JSON 집계 SHA256이며 토크나이저 집계에는 config.json도 포함합니다.
임의의 64자리 문자열은 신뢰된 설치 기록을 대신하지 못합니다.

모델이 준비되면 `app.cli score-local --help`의 필수 인자로 직접 추론할 수 있습니다.
MCP 경로는 `.env`에 local/모델/디렉터리/두 핀/장치를 설정하고 새 계획을 만듭니다.

```powershell
.venv/Scripts/python.exe -m app.cli prepare --workspace .runtime/local_review --review --positions 32 --model-key esm150
.venv/Scripts/python.exe -m app.cli esm-score --workspace .runtime/local_review --approve-plan
```

현재 설정 그대로라면 미설정으로 차단됩니다. 계획과 `.env`의 모델 키는 같아야 합니다.
위치·모델·핀은 계획에 고정되며 기존 실행의 모델을 환경 변경으로 교체할 수 없습니다.
실행 가능한 제공자만 동일한 `score_positions` 도구로 노출합니다. 모델은 백엔드나 승인,
소유자, 경로를 도구 인자로 선택하지 못합니다.

Modal SDK 설치/버전·오프라인 signature 확인은 수행했습니다. 모델 다운로드·볼륨 준비,
GPU/유료 실행·배포는 미수행입니다.
다운로드·GPU·유료 작업·배포는 별도 명시 승인 후 진행합니다. `modal_worker.py`는 import로
실행되지 않습니다. 배포 정의를 만들 때도 배포/기존 볼륨 승인과 실제 SDK 버전 일치가
필요합니다. 컨테이너 1개, 자동 재시도 없음, T4/L4 중 하나, 최대 900초, 읽기 전용 기존
모델 볼륨, 개별 소스 허용목록과 네트워크 차단을 정의했습니다. 실제 SDK 호환성과 배포
성공은 아직 검증하지 않았습니다. 전체 `.env`를 worker secret으로 전달하지 않습니다.
Modal 인증은 Modal 전용 환경변수나 SDK 비밀 저장소로 관리합니다.

원격 실행에는 배포 이름/함수/SDK pin/호환 확인/명시 승인/비용 추정/참조 전송 동의와
실행 예산이 필요합니다. 검증된 배포 상한의 독립 증거 전에는 작업당 900 GPU초를 보수적으로
예약합니다. 짧은 클라이언트 대기시간이 이 예약을 줄이지 않습니다. 실제 공급자 청구액을
완벽하게 강제한다는 뜻은 아닙니다.

SQLite 예약·단일 claim 뒤에 submit하고 provider 작업 ID를 보존합니다. 반복 요청은 같은
task를 사용합니다. 미실행 대기 작업만 안전하게 재개하며, 실행 여부가 불명확한 작업은
재제출하지 않습니다. 상태 조회는 저장된 기록만 읽습니다. 승인된 운영자는
`esm-poll --workspace ... --task-id ...`로 기존 작업을 확인할 수 있습니다.

## Meta, 평가와 남은 범위

`MetaHost(workflow='sequence_review')`는 검증→ESM→도구 없는 설명을 지원합니다.
최종 요청 비용을 먼저 예약하고 pending이면 결정적 부분 보고서로 종료합니다.
수치는 `score_artifacts`/`candidates`, 모델 문장은 `model_narrative`로 분리합니다.
통합 테스트는 synthetic_fixture이며 실제 Meta+ESM 연속 실행은 아직 없습니다.

기존 사용자 보고의 Meta OK/120토큰은 별도 기록입니다. 새 실연결 시도는 키 이름 차이
진단이 있는 부분 artifact이며 자동 재시도하지 않았습니다. 실시간 소규모 경로는
`meta-smoke --live --ack-small-test`, review는 `meta-review --live --ack-small-test`입니다.
외부 호출이 가능한 명령이므로 위 오프라인 재현 절차에는 넣지 않았습니다.
플래그가 별도 GPU/배포 승인을 대신하지 않습니다.

`evaluation/`은 runtime/MCP/worker에 포함하지 않습니다. `freeze_score_artifact()`로 예측
artifact와 코호트를 고정한 후 독립 체크섬을 제공해야 별도 evaluator가 정답을 결합합니다.
합성 지표만 테스트했으며 실제 ProteinGym 정답·논문 결과·held-out 지표를 제품에 제공하지
않았습니다. 실제 기준선·원자료 대조·잔기별 bootstrap은 미완료입니다. 현재 범위는
검증되지 않은 서열 근거 검토 도우미입니다. Streamlit은 추가하지 않고 CLI/JSON을 사용합니다.

허용 파일 실행 폴더는 `.env`, evaluator, 문서·테스트·보조 폴더를 제외합니다. OS ACL
격리는 미검증이며 광범위한 파일 권한의 Native Muse Code는 연결하지 않았습니다.
정답/셸/파일/URL/SQL 도구는 없습니다. LIVE/REPLAY/fixture와 해시를 검사하고 비용 미확인은
null입니다. 대회 규칙·재사용·기관 소속 자격의 최종 판정, 공개·영상·배포·제출은 미완료입니다.
