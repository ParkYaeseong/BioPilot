# BioPilot Bench 시연 자료

## 현재 UI 영상 — 2026-11-03 실제 실행 편집본

[최신 영상 안내](FINAL_VIDEO_20261102_KO.md)와
[기술 검증 영수증](../submission/video_current_ui_20261102_receipt.json)을 확인하세요.
파일 입력 → 승인 → Execute → 실제 RUNNING → COMPLETED → 결과 검토를 180초로 편집했습니다.
영어 AI 음성·실측 자막과 기존 빠른 확대·정확한 강조 박스를 유지했습니다.
이번 실제 실행은 Meta 요청3회·CPU ESM·후보19개이며 GPU 호출은 없습니다.
새 영상과 한영 자막은 로컬에 저장했습니다. 비공개 Release도 2026-11-03 화질 수정본과 최신 자막·체크섬으로 교체했습니다.
저장소 권한이 필요하며 공개 심사자 접근은 아직 확인하지 않았습니다.
아래 예전 영상과 기록은 이전 버전의 제작 이력으로 보존합니다.

## 최신 3분 대본 — 2026-10-29

현재 통합 UI의 파일 입력 → 요청 → 검증 → 실제 실행 기록 → 결과 검토를 보여주는 대본입니다.

- [한국어 화면 조작·설명·낭독 대본](REVIEW_FLOWS_180S_KO.md)
- [영어 내레이션](REVIEW_FLOWS_180S_EN.md)
- [영어 자막](REVIEW_FLOWS_180S_EN.srt) / [한국어 자막](REVIEW_FLOWS_180S_KO.srt)
- [정확히 180초인 촬영 타임라인](review_flows_180s.json)

실제 업로드 입력으로 완료한 새 실행은45.48초, Meta 요청3회, 후보19개입니다.
기본 편집안은 현재 무료 입력 검사와 이 실제 실행 기록을 연결하며, 영상을 보는 동안
새 모델/GPU 호출을 하지 않습니다. 기록된 실행으로의 전환과 생략한 대기를 표시합니다.
실제 음성·녹화·최종 영상 길이는 아직 검증하지 않은 촬영 계획입니다.
이전 NARRATION / WORKBENCH / SPOTLIGHT 자료와 영상은 과거 버전으로 보존합니다.

## 저장된 실제 실행 재생 — 2026-10-28

`artifacts/sequence_review.replay.json`은 2026-10-27에 완료된 Meta → MCP → 로컬
ESM → 설명 실행의 휴대 가능한 재생본입니다. 새 Meta 호출이나 ESM 추론 없이 실제
수치·출처·도구 호출·설명을 검토할 수 있습니다. 합성 예제가 아닙니다.

프로젝트 루트의 PowerShell에서 다음 명령을 실행합니다. 현재 `.venv`에 설치된
Streamlit을 사용하며, 깨끗한 PC의 새 설치 검증을 의미하지는 않습니다.

```powershell
.venv/Scripts/python.exe -m streamlit run app/viewer.py -- --artifact demo/artifacts/sequence_review.replay.json
```

로컬 뷰어는 `localhost`에 바인딩하며 저장된 JSON만 읽습니다. 계정 키, 모델 가중치,
GPU 또는 외부 서비스 연결이 필요하지 않습니다. 화면의 `REPLAY` 표시는 이전에 수행한
실제 실행을 재생한다는 뜻입니다. 재생 화면을 여는 시간을 추론 시간으로 제시하지 마세요.

원본 실행은 Meta Model API의 `muse-spark-1.3`과 MCP 프로토콜 `2025-11-25`를 사용했습니다.
`validation/integration_success_20261027.json`에 당시 실행 영수증이 있습니다.
현재 재생본의 정확한 출처·해시는 JSON의 `replay_export` 필드에 기록했습니다.

- 원본 실행 ID: `5b7c92bc2d364680809713bf8c332f66`
- 원본 파일 SHA256: `d396dd4eb8f75976e5fc61f38e1ffcf0c922397a7cbefc9ee8529cf32ffdb785`
- 원본 내용의 canonical SHA256: `874bfd60afbdac8b9b2eaf078c662e61de1f77808535abe72f192518a75a829e`
- 원본 점수 artifact SHA256: `63a1c3752407d96a54f33b735d72e700839e4b0e9363894597738f6e8531157f`

최상위 `source_mode`, `meta_source_mode`, `esm_source_mode`는 모두 `replay`이고,
`scores_reused_from_saved_artifact`는 `true`입니다. 내부 점수 artifact와 후보의
원본 `live` 출처 표시는 당시 계산 방식을 보존한 것입니다. 내부 점수 artifact는
변경하지 않고 canonical 체크섬을 검증했습니다. 비용은 청구 확인 전이므로 계속
`null` / `unknown`입니다.

ESM 점수는 단위 없는 서열 선호도입니다. T50, 활성, 용해도, Tm, 기능 유지 또는
실험적 개선을 입증하지 않습니다. 평가 정답·평가 보고서는 이 재생본에 포함하지
않으며 제품 런타임에도 제공하지 않습니다.

## 새 재생본을 만들 때

다음 명령은 지정한 로컬 파일만 읽으며 새 파일을 배타적으로 생성합니다.
기존 목적지와 원본 덮어쓰기를 거부합니다. 아래 원본 경로는 현재 개발 PC의 보존
기록이며 공개 재현에 필요한 파일이 아닙니다.

```powershell
.venv/Scripts/python.exe checks/export_demo_replay.py --source .runtime/real_integration3_20261027/attempt3.stdout.json --destination demo/artifacts/another-review.replay.json
```

내보내기는 허용된 보고서 필드와 도구 trace만 복사합니다. 로컬 절대 artifact 경로,
임의 추가 필드, 비공개 추론·인증 필드는 내보내지 않습니다. 점수 artifact에는
허용된 출처 필드만 사용할 수 있고 체크섬과 후보 순위가 맞아야 합니다.
원본 파일은 변경하지 않습니다.

```powershell
.venv/Scripts/python.exe -m pytest tests_app/test_demo_replay.py tests_app/test_viewer.py -q -p no:cacheprovider
```

재생본과 뷰어는 녹화 준비용입니다. 실제 3분 영상, 공개 링크 접근 확인, 권리·자격·
재사용 판정과 최종 제출 승인을 대신하지 않습니다.

## 생성된 로컬 영상 초안

[180초 MP4 초안](../local_artifacts/demo/BioPilot_Bench_180s_LOCAL_DRAFT.mp4)과
[검증 영수증](../submission/video_draft_receipt.json)을 준비했습니다. 실제 재생 UI 캡처와
저장된 로컬 검사 결과를 편집한 영상으로, 연속 화면 녹화나 새 Meta 실행이 아닙니다.
Microsoft Zira Desktop의 오프라인 합성 영어 음성과 자막을 사용하며 화면마다
REPLAY / SAVED REAL RUN, LOCAL DRAFT를 표시합니다.

정확한 길이 180초, H.264/AAC, 1280×720, 비무음 음성 트랙과 검은 프레임 없음까지
검사했습니다. 숫자는 영수증과 artifact에서 렌더링합니다. 전체 영상·음성의 사람 검토,
최종 규칙과 공개 링크 접근은 미완료입니다. 원본 영상은 소스 목록에서 제외한
`local_artifacts/`에 보존하며 자동 업로드하지 않습니다.
