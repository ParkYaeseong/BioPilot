# 현재 UI로 제작한 3분 시연 영상

2026-11-02 제작. 2026-11-03 안내 갱신: MP4와 한·영 자막, 체크섬을
[비공개 Release](https://github.com/ParkYaeseong/BioPilot/releases/tag/demo-2026-11-02)의
첨부파일로 제공합니다. 저장소 권한이 있어야 접근할 수 있습니다. MP4는 Git 소스 기록에
넣지 않았으며 원본 캡처·음성 파일은 로컬에 남깁니다.
[기술 검증 영수증](../submission/video_current_ui_20261102_receipt.json)에
실제 파일 길이, SHA-256, 오디오 수준, 자막·챕터와 촬영 범위를 기록합니다.
공개 링크나 최종 제출 접수 확인을 뜻하지 않습니다.

[영상 다운로드](https://github.com/ParkYaeseong/BioPilot/releases/download/demo-2026-11-02/BioPilot_Bench_180s_EN.mp4)
· [업로드 검증 기록](../submission/demo_release_20261102.json).

![실제 MP4에서 추출한 기준 구조 회전 프레임](../docs/images/final-video-preview.jpg)

로컬 결과 위치:

```text
local_artifacts/final_demo_20261102/BioPilot_Bench_180s_EN.mp4
local_artifacts/final_demo_20261102/BioPilot_Bench_180s_EN.srt
local_artifacts/final_demo_20261102/BioPilot_Bench_180s_KO.srt
```

## 구성

- 실제 길이 180초, 1920×1080, 30fps, H.264/AAC, 챕터 9개입니다.
- 영어 내레이션은 본인 녹음이 아닌 `en-US-AndrewNeural` 합성 음성입니다.
  공개 대본만 Microsoft Edge 온라인 음성 서비스로 생성했습니다. 제품의 Meta 모델과
  내레이션 생성 도구는 별개이며 비공개 대화·인증정보·단백질 파일을 음성 서비스에 보내지 않았습니다.
- 영어 자막을 화면에 넣고, 영어/한국어 SRT를 별도로 제공합니다. 플레이어가 자막을
  자동으로 이중 표시하지 않도록 MP4의 선택 자막 트랙은 넣지 않았습니다.
  27개 문장의 시간은 실제 음성 생성 메타데이터와 편집된 오디오에서 계산했습니다.
  과거 `REVIEW_FLOWS_180S_*.srt`는 촬영 전 계획이며 이 영상의 실측 자막은 위 새 파일입니다.
- 부드러운 확대·팬, 강조 박스가 그려지는 효과, 화면 간 디졸브와 여백 있는 프레임을 사용합니다.
  [AionUi 참고 GIF](https://github.com/iOfficeAI/AionUi/blob/main/resources/AionUi_team.gif)는
  편집 스타일 참고용으로 확인했으며 영상에 삽입하지 않았습니다.

## 보여 주는 실제 동작

| 시간 | 화면과 확인할 점 |
|---|---|
| 0–15초 | New Review: 파일과 요청을 한 작업 공간에서 시작 |
| 15–35초 | 실제 공개 FASTA 업로드와 S108A의 로컬 보호 규칙 거부 |
| 35–55초 | A32V 검증, 위치32·esm150·호출 상한4·별도 실행 승인 |
| 55–75초 | 실제 완료 기록: Meta3회,19후보,45.48초; 대기 생략 표시 |
| 75–100초 | 저장된 후보 순위, 상위3개 비교, A32V 선택 |
| 100–125초 | A32 원자 없음, S108→author77 대응, 실제 기준 구조 회전 |
| 125–145초 | Meta의 실제 MCP 검증/점수 요청과 저장된 인수·출력 |
| 145–165초 | 업로드 입력 영수증, 보고서 해시, 공개 구조 잔기 대응 |
| 165–180초 | COMPLETED 기록 재열기, 근거 검토와 생물학적 한계 |

실제 브라우저 화면을 CUA로 샘플링해 편집했습니다. 연속 OS 스크린캐스트는 아닙니다.
확대·강조·화면 타이밍은 편집 효과이며, UI 상태·모델 답변·실행 진행률을 합성하지 않았습니다.
구조 회전은 실제 뷰어에서 촬영한 프레임입니다. 원자 위치가 없는 A32에 가짜 마커를
넣지 않았고, 구조 화면은 실험 기준 WT 시각화이며 새 변이체 예측이 아닙니다.

## 실제 실행과 재생의 구분

촬영 때는 새 Meta 요청이나 GPU 작업을 하지 않았습니다. 입력 가드·FASTA 업로드는
현재 로컬 UI에서 직접 조작했고, 실제 계산 결과는 기존 완료 실행
`14014be81e934c0ab4236268d013ad19`를 열었습니다. 제품의 실제 모델은
`muse-spark-1.3`이며 계산은 로컬 CPU ESM-2 150M이 수행했습니다.
사용한 업로드 파일은 그 실행에 기록된 공개 FASTA와 바이트 해시가 같습니다.

로컬 검증으로 새 VALIDATED 초안1개가 생겼지만 실행 승인은 체크하지 않았습니다.
기존 COMPLETED/PARTIAL 기록은 보존했고 실행 사용량은 촬영 전후2건으로 같습니다.
남은 실행 허용량을 초기화하거나 새 계산을 촬영한 것처럼 연결하지 않았습니다.
ESM 점수는 실험적 내열성·활성·기능 유지의 검증값이 아닙니다.

## 게시 전 최종 확인

전체 파일 디코딩, 음성 존재·음량, 실측 자막 타임스탬프, 24개 인코딩 프레임과 원본
캡처 해시를 검사했습니다. 사람이 전체 음성을 듣고 최종 싱크를 확인한 상태는 아직
아닙니다. 최종 시청과 공식 폼의 조건·공개 링크 접근을 확인한 뒤 게시/제출합니다.

영상 설명에 사용할 영어 문구:

> AI-generated English narration over actual application captures. Camera movement,
> highlights and timing are edited. The scientific execution is shown as recorded
> evidence; no new Meta or GPU inference is performed during capture.
