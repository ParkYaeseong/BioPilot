# 현재 UI로 제작한 3분 시연 영상

## 최신 편집: 구조 예측과 Atlas — 2026-11-04

새 편집본은 `local_artifacts/structure_demo_20261103/`에 별도로 제작합니다.
기존 영상과 YouTube 업로드는 보존하며, 이전 제작 기록은 Git 이력에 보존합니다.
최신 [YouTube 영상](https://www.youtube.com/watch?v=tozONY6U15s)은 사용자가 새로 업로드한 편집본입니다.

| 시간 | 최신 편집 흐름 |
|---|---|
| 0–75초 | 기존 실제 입력·검증·승인·Meta/MCP/ESM-2 실행 장면 유지 |
| 75–100초 | 19개 후보 비교와 A32V 선택 |
| 100–108초 | 공개 실험 구조 1ISP의 잔기 대응과 실제 좌표 유무 |
| 약 108–118초 | 저장된 ESMFold2 WT 예측 선택·회전 |
| 약 118–140초 | 별도 실행의 ESM3 A32V 예측 선택·회전 |
| 140–154초 | Atlas의 정확한 WT 일치, 등록 번호·출처·저장 조회 기록 |
| 154–167초 | Meta의 실제 검증·점수 도구 호출 |
| 167–180초 | 입력과 결과 영수증 연결, 통합 검토 가치로 마무리 |

Atlas는 현재 유사 단백질 검색 기능이 아닙니다. ESMFold2 WT와 ESM3 A32V는
서로 다른 모델·입력의 별도 결과이며 변이 효과 비교가 아닙니다. 새 구조 장면은
완료된 서열 검토에 자동 포함된 계산이나 Meta가 호출한 도구처럼 표시하지 않습니다.
반복적인 마지막 한계 설명 음성은 제거하고 모델·입력·저장 결과 표시는 유지합니다.

전달 파일:

- `BioPilot_Bench_180s_YOUTUBE.mp4`: 영어 음성, 화면에 고정하지 않은 한·영 선택 자막 트랙
- `BioPilot_Bench_180s_EN.mp4`: 영어 자막을 화면에 넣은 검토용
- `BioPilot_Bench_180s_EN.srt`, `BioPilot_Bench_180s_KO.srt`: YouTube 별도 자막 업로드용

최신 [영어 자막](STRUCTURE_ATLAS_180S_EN.srt)·[한국어 자막](STRUCTURE_ATLAS_180S_KO.srt)과
[대본·검증 기록](../submission/structure_atlas_video_20261103.json)을 함께 제공합니다.
원본 MP4는 Git 소스에 추가하지 않으며 README에는
새 [구조 예측 GIF](../docs/images/biopilot-predictions.gif)와
[Atlas GIF](../docs/images/biopilot-atlas.gif)를 제공합니다.


이전 시연 제작 기록은 [Git 보관 이력](https://github.com/ParkYaeseong/BioPilot/blob/0086ef9/demo/FINAL_VIDEO_20261102_KO.md)에서 확인할 수 있습니다.
