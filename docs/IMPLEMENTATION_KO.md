# 로컬 구현 실행 안내 — 2026-10-28

**2026-10-29 최신 사용자 진입점은 [통합 워크벤치 안내](UNIFIED_WORKBENCH_KO.md)입니다.**
8522한 화면에서 파일/예제 입력부터 명시적 실행과 최근 결과 확인까지 연결됩니다.
아래 원래 CLI·독립 읽기 전용 뷰어 안내는 보존합니다.

화면·영상과 전체 로컬 추론 명령의 최신 안내는 [통합 워크벤치 안내](UNIFIED_WORKBENCH_KO.md)를
확인하세요. 저장된 Meta/ESM 재생과 별도 현재 로컬 검사를 구분합니다.

실제 Meta → MCP → 로컬 ESM → 최종 설명의 연속 실행과 읽기 전용 Streamlit 뷰어가
구현되어 있습니다. 실제 실행 근거는 [통합 영수증](../validation/integration_success_20261027.json),
제출 준비 상태는 [제출 초안](../submission/README.md)에서 확인합니다.
제품 범위는 `unvalidated_sequence_evidence_assistant`입니다. 내열성 개선이나 검증된
T50 예측 모델을 완성한 것은 아닙니다.

원본 설계 패키지는 기준 커밋 `5898a2f`와 `compliance/original_package_manifest.sha256`에
보존했습니다. `BioPilot_Atlas_Local_Start`는 제품에 포함하지 않는 보조 도구입니다.
2026-10-27 계획과 이전 결정 기록의 날짜는 원래 이력입니다.

## 확인된 환경

2026-10-28 설치 메타데이터 재확인: Windows/Python 3.14.0, MCP 1.25.0, PyTorch 2.9.1,
Transformers 5.2.0, Streamlit 1.66.1. 실제 ESM 실행은 CPU/float32였습니다. 로컬 CUDA는
사용하지 않았습니다. `.venv`는 기존 패키지를 재사용하는 `--system-site-packages`
환경이므로 다른 컴퓨터의 깨끗한 재설치는 아직 검증하지 않았습니다.

직접 의존성은 `requirements/dev.txt`, 과학 런타임은 `requirements/science.txt`, 선택
뷰어는 `requirements/viewer.txt`에 고정했습니다. Modal SDK 1.6.2의 오프라인 API 검사는
원격 배포나 GPU 실행의 증거가 아닙니다.

## 외부 호출 없는 로컬 검사

프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.venv/Scripts/python.exe -m app.cli validate --variant A32V
.venv/Scripts/python.exe -m app.cli validate --variant S108A
.venv/Scripts/python.exe -m app.cli esm-status
.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider
.venv/Scripts/python.exe checks/validate_package.py
```

`S108A`는 보호 잔기 변경이므로 차단되어야 합니다. `esm-status`는 공개 백엔드 설정만
읽으며 추론을 실행하지 않습니다. 미설정 환경에서는 `unconfigured`/종료 코드 2가 정상이며,
이 컴퓨터에 저장된 개인 설정의 존재를 배포 기본값으로 간주하면 안 됩니다.

새 로컬 MCP 검사 폴더를 만들려면 아직 존재하지 않는 경로를 지정합니다.

```powershell
.venv/Scripts/python.exe -m app.cli prepare --workspace .runtime/new_protocol_check
.venv/Scripts/python.exe -m app.cli mcp-smoke --workspace .runtime/new_protocol_check
.venv/Scripts/python.exe -m app.cli status --workspace .runtime/new_protocol_check
```

`prepare`는 기존 폴더를 덮어쓰지 않습니다. 이 기본 경로는 유료 요청이나 ESM 계산 없이
실제 로컬 stdio MCP를 검사합니다. SDK 1.25.0이 협상한 프로토콜은 `2025-11-25`입니다.
예측 에이전트에는 `product/` 허용 파일만 전달합니다. 이 저장소 전체를 Native Muse Code의
넓은 파일/셸 권한과 연결하는 것은 검증된 실행 경로가 아닙니다.

## 저장된 실제 결과 보기

[시연 안내](../demo/README_KO.md)의 검증된 재생 파일을 사용합니다.

```powershell
.venv/Scripts/python.exe -m streamlit run app/viewer.py -- --artifact demo/artifacts/sequence_review.replay.json
```

뷰어는 저장된 결과만 읽고 API 호출, 추론, 실행 DB 변경을 하지 않습니다. `.streamlit/config.toml`은
`localhost` 바인딩으로 설정되어 있습니다. 저장 기록을 재생할 때는 **REPLAY**로 표시하며,
원래 실행이 실시간이었다는 출처와 현재 화면의 재생 모드를 구분합니다. 다른 컴퓨터의 심사자
접근이나 공개 배포를 검증한 것은 아닙니다.

점수·순위는 저장 artifact에서 코드로 렌더링합니다. 모델 설명에 수치를 새로 작성시키지
않습니다. 실제 청구액은 `null`/`unknown`이면 그대로 표시하며, 예약 예산을 실제 비용으로
바꾸지 않습니다. 미완료 실행은 완료로 표시하지 않습니다.

## 실제로 확인된 통합

2026-10-27 저장 실행 `5b7c92bc2d364680809713bf8c332f66`은 40초 동안 Meta 요청 3회로
다음을 한 실행 안에서 완료했습니다.

1. `muse-spark-1.3`가 `validate_target_context`를 요청하고 MCP 검증에 성공했습니다.
2. 같은 모델이 `score_positions`를 요청하고 로컬 ESM-2 150M이 실제로 계산했습니다.
3. 코드가 19개 대안을 `esm150_masked_v1`로 정렬하고, 모델이 도구 없는 최종 설명을 완료했습니다.

ESM 체크포인트는 `esm2_t30_150M_UR50D`, revision은
`a695f6045e2e32885fa60af20c13cb35398ce30c`, scoring context는 `full_212`입니다.
해당 실행의 cached positions는 비어 있어 새 계산임을 확인합니다. 가중치·토크나이저·결과
SHA256은 통합 영수증에 있습니다. 원본 실행의 `esm_source_mode=live`는 원래 계산 기록이며
지금 뷰어에서 여는 동작은 재생입니다.

같은 최종 설명이 앞선 두 시도에서는 토큰 한도로 실패했습니다. 실패 기록을 보존했고,
성공 시도는 tool stage `reasoning_effort=medium`, final report `low`를 명시했습니다.
최종 설명 한도는 1024토큰이며 성공 응답은 395토큰을 사용했습니다. 이 관측 한 번으로
장기 성공률이나 시간 절감률을 주장할 수는 없습니다.

세 번째 시도의 로컬 예약/commit은 150000 micros였지만 실제 provider 청구액은 미확인입니다.
별도 `final-report` continuation 기능은 저장된 미완료 artifact를 보존하고 새 보고서를 만드는
경로이며, 기존 부분 실행을 완료로 덮어쓰지 않습니다.

## 제공자와 새 실행의 전제

```text
Meta host -> MCP score_positions -> InferenceService -> ESMInferenceProvider
                                                  -> LocalESMProvider
                                                  -> ModalESMProvider (remote readiness pending)
                                                  -> RunPodESMProvider (unconfigured)
```

`.env`/환경변수의 `ESM_BACKEND=modal|local|runpod`는 백엔드 선택이며 실행 승인이 아닙니다.
장치는 `ESM_DEVICE=cpu|cuda`로 명시하고 자동 fallback하지 않습니다. `.env.example`은
설정 예시입니다. 실제 `.env`를 덮어쓰거나 키를 로그·worker 요청에 포함하지 마세요.
Meta 키 이름은 `MODEL_API_KEY` 또는 `META_API_KEY`입니다.

| 모델 키 | 체크포인트 | 공통 순위 정책 |
|---|---|---|
| esm35 | esm2_t12_35M_UR50D | esm35_masked_v1 |
| esm150 | esm2_t30_150M_UR50D | esm150_masked_v1 |
| esm650 | esm2_t33_650M_UR50D | esm650_masked_v1 |

검증된 기본 경로와 제출 증거는 150M입니다. 다른 모델은 별도 계획·핀·공통 코호트를
고정해야 하며, 일부 후보만 큰 모델 점수로 바꾸어 같은 순위 열에 섞지 않습니다.

로컬 ESM-2 150M 가중치는 [설치 영수증](../validation/real_esm150_install.json)에 기록되어
있습니다. `LocalHFBackend`는 local-only 로딩과 가중치/토크나이저 핀을 확인하고 누락된
가중치의 무작위 초기화를 거부합니다. 핀은 파일명→SHA256 매핑을 정렬한 JSON의 집계
SHA256입니다. 임의의 64자리 문자열은 신뢰된 설치 기록을 대신하지 못합니다.
모델 가중치는 소스 패키지나 재생 파일에 포함하지 않습니다.

새 실행은 `app.cli --help`, `app.cli prepare --help`와 실제 설정/승인 범위를 먼저 검토합니다.
`meta-review --live --ack-small-test`, `esm-score --approve-plan`, `score-local`은 실행을
일으킬 수 있으므로 위 오프라인 검사에 포함하지 않습니다. 새 API 호출·모델 다운로드·GPU·
외부 서열 전송·배포는 대응하는 명시 승인 뒤에만 수행합니다.

Modal은 선택 기능이며 현재 제출 핵심 경로가 아닙니다. SDK 형식·상한의 로컬 검사만 있고
실제 배포/볼륨/GPU 통합은 미완료입니다. 현재 원격 예약 조건과 CLI GPU 한도의 조합도
실행 준비 완료로 검증되지 않았으므로 지금 바로 실행할 수 있다고 안내하지 않습니다.
`modal_worker.py` import만으로 배포하지 않으며, RunPod도 명시적인 미설정 adapter입니다.

SQLite 예약과 단일 claim 뒤에 dispatch하고 provider 작업 ID를 보존합니다. 실행 여부가
불명확한 작업은 재제출하지 않습니다. 저장 상태 조회만으로 새 작업이 생기지 않습니다.

## 과학적 한계와 평가 격리

점수는 전체 212개 서열에서 위치 i를 마스킹한
`log P(mutant | mask) - log P(WT | mask)`입니다. 위치당 19개 대안을 재사용하고 최대
200개 후보 한도를 적용합니다. 입력은 전체 기준 1-based 번호이며 S108/D164/H187을 보호합니다.
이 보호는 기능 유지의 증거가 아닙니다. 원자 좌표·구조 검증과 CPU/GPU 실제 수치 일치도
검증되지 않았습니다.

`evaluation/`은 runtime/MCP/worker에서 제외합니다. 예측 artifact와 코호트를 고정한 뒤
별도 evaluator가 정답을 결합합니다. [평가 요약](../validation/site_bootstrap_summary.json)은
190개 예측 중 측정값이 있는 117개, 9개 잔기의 후향 분석입니다. Spearman 0.288의 95%
잔기별 bootstrap 구간 [-0.058, 0.536]은 0을 포함합니다. Recall@20은 별도 bootstrap하지
않았습니다. 이 분석으로 T50 예측 유용성·일반 성능·실험적 개선을 주장하지 않습니다.
전체 라이브러리 원자료 대조, WT 개선 기준과 독립 전향 검증은 여전히 미완료입니다.

정답, evaluator 문서, 평가 지표, 논문 결과는 예측 에이전트의 허용 파일 폴더에 넣지 않습니다.
OS ACL 기반 격리는 미검증입니다. 제품 도구에는 정답/셸/파일/임의 URL/SQL 접근이 없습니다.
기존 여섯 closed-set 입력 과제에서는 고정 가드6/6, Meta5/6가 기록되었습니다.
수동 방법과 사람 시간은 미측정이며, 전체 과학 검토나 시간 절감의 공정한 비교는 아닙니다.
자세한 범위는 [측정 안내](WORKFLOW_MEASUREMENT_KO.md)를 따릅니다.

최종 규칙·재사용·소속 자격·권리 판정, 실제 영상, 공개 접근과 제출은 별도의 남은 단계입니다.
로컬 구현의 작동과 대회 접수 완료를 구분하고 실제 접수 전에는 `not_submitted`를 유지합니다.
