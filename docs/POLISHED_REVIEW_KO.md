# 화면·영상 개선 후 실행 안내 — 2026-10-28

사용자가 띄운 `http://127.0.0.1:8520`을 직접 확인한 뒤 색상과 실제 조작 흐름을
개선했습니다. 기존 8520 프로세스는 중지하지 않았습니다. 검토용 새 화면은
`http://127.0.0.1:8521`에서 실행했습니다.

## 뷰어

프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.venv/Scripts/python.exe -m streamlit run app/viewer.py --server.port 8521 -- --artifact demo/artifacts/sequence_review.replay.json
```

`python.exe -m streamlit`을 사용합니다. `streamlit.exe run`은 이 환경에서 프로젝트
루트의 `app` 패키지를 찾지 못할 수 있습니다. 이미 사용 중인 포트에는 새 서버를
겹쳐 띄우지 마세요. 이번 색상 설정은 서버 재시작 후 네이티브 표에도 적용됩니다.

- 어두운 기본 테마, 밝은 테마 모두 실제 글자·배경색을 확인했습니다.
  네이티브 표·입력 위젯과 CSS 배경을 같은 체계로 맞췄습니다.
- 예제 A32V/S108A/G32V 버튼은 전체 기준 1-based 번호와 서열 선호 검토 목적의
  **새 로컬 검사**를 실행합니다. 입력 필드도 그 예제에 맞게 바뀝니다.
  직접 입력한 번호를 몰래 변환하지 않습니다. `Last checked`는 마지막으로
  검사한 입력을 표시하며, 입력만 수정했다고 이전 검사 결과를 바꾸지 않습니다.
- `Compare top three`와 `Clear selection`은 저장된 후보 선택만 바꿉니다.
  최대 3개 비교, 저장된 원래 순위, 코드가 만든 CSV를 사용합니다.
- `Previous step`/`Next recorded step`은 이미 저장된 MCP 이벤트를 탐색합니다.
  애니메이션과 화면 이동은 현재 UI 조작에 대한 것이며 새 추론 진행률이 아닙니다.
- 사이드바 닫기/열기를 표시하고 좁은 화면도 확인했습니다. 전환은 짧게 적용하며
  OS의 reduced-motion 요청에서는 모션을 줄입니다.

뷰어와 로컬 검사는 유료 provider 호출이나 ESM 추론을 실행하지 않습니다.
Streamlit 자체의 로컬 웹 통신과 유료 모델 호출을 구분합니다.

## 근거 체인 해석

이전 화면은 일부 해시가 존재한다는 사실을 전체 검증처럼 표시할 수 있었습니다.
현재는 점수 payload의 체크섬을 실제로 다시 계산하고, 화면 후보의 점수·순위를
그 payload와 대조하며, 해당 점수 도구 결과의 digest를 확인합니다.

가중치 파일과 원본 export 파일을 직접 열지 않은 단계는 `recorded only`, 열린
파일 자체의 해시는 `computed locally`로 표시합니다. 외부 진위·전자서명·변조
불가능성을 주장하지 않습니다. 불일치가 있으면 Overview에서도 경고합니다.

## 로컬 ESM 명령을 복사할 때

사용자가 붙여 준 예시의 `--tokenizer-sha256 2`는 잘린 값이며 필수
`--positions`도 빠져 있습니다. 설치 영수증과 현재 CLI 도움말로 확인한 전체 예시는
아래와 같습니다. **이번 UI 작업에서 이 추론 명령을 새로 실행하지는 않았습니다.**

```powershell
.venv/Scripts/python.exe -m app.cli score-local `
  --checkpoint-dir ".cache/models/facebook/esm2_t30_150M_UR50D/a695f6045e2e32885fa60af20c13cb35398ce30c" `
  --weights-sha256 377f67e27c559ef9db8eac8296e0961ba68a98b08d32da9072af3853d193549b `
  --tokenizer-sha256 28bae4e8d8b0225381da7978ca8b341f5ac46cc4f0ca62ad459c7955608b6ea2 `
  --positions 32 `
  --output .runtime/my_score.json
```

출력이 이미 있으면 기존 artifact를 보존하기 위해 거부합니다. `esm-status`의
`unconfigured`는 준비 완료를 자동 선언하지 않는 현재 구현 정책이며, 실제 계산은
별도 `score-local` 명령입니다. 다운로드나 원격 실행 권한을 추가하지 않았습니다.

## 새 영상과 남은 항목

[새 180초 영상](../local_artifacts/polish_demo_20261028/BioPilot_Bench_Polished_180s_LOCAL_DRAFT.mp4)은
실제 브라우저 조작 340개 샘플 프레임을 편집한 초안입니다. 클릭·탭 이동·표 펼치기·
입력 거부·후보 선택을 담고, 화면 확대·자막·오프라인 영어 합성 음성을 적용했습니다.
약 2Hz 샘플 캡처를 25fps 영상으로 편집한 것이며 연속 OS 화면 녹화가 아닙니다.
긴 조작 대기시간은 편집했고, 원래 캡처 시각을 별도 보존했습니다.

Meta/ESM 기록은 계속 REPLAY이고 로컬 입력 검사는 실제 현재 조작입니다.
별도 6개 과제의 기존 결과(고정 가드 6/6, Meta 5/6)는 영상 밖 평가 artifact에서
읽어 영상 주석으로만 표시합니다. 이를 제품 모델의 입력에 넣지 않습니다.
수동 방법은 미측정이고, 이 작은 closed-set 검사는 시간 절감·생물학적 개선이나
일반 모델 성능을 입증하지 않습니다.

실제 새 provider/GPU 호출·외부 업로드·공개·제출은 하지 않았습니다. 남은 단계는
전체 영상·음성의 사람 검수, 새 환경 재현, 권리·자격·최종 양식과 공개 링크 확인입니다.
