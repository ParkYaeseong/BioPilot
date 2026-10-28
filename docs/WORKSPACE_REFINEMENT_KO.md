# 화면 사용 안내 — 2026-10-28

기존 8520·8521 프로세스는 작업 보존을 위해 그대로 두었습니다. 이번 코드의
새 미리보기는 **저장 결과 8522 / 대화 8523**입니다. 기존 실행은 fileWatcherType=none으로
시작되어 브라우저 새로고침만으로 Python 변경이 반영되지 않습니다. 다시 실행하면
원래 포트에서도 같은 새 코드를 사용할 수 있습니다.

```powershell
.venv/Scripts/python.exe -m streamlit run app/viewer.py --server.port 8522 --server.address 127.0.0.1 --server.fileWatcherType poll -- --artifact demo/artifacts/sequence_review.replay.json --workspace-url http://127.0.0.1:8522 --session-url http://127.0.0.1:8523

.venv/Scripts/python.exe -m streamlit run app/session.py --server.port 8523 --server.address 127.0.0.1 --server.fileWatcherType poll -- --viewer-url http://127.0.0.1:8522 --session-url http://127.0.0.1:8523
```

## 검토 순서

1. **Input**: A32V 통과, S108A 보호 차단, G32V WT 불일치의 실제 로컬 검사.
   자신의 FASTA·mmCIF 검사는 이 단계의 선택 펼침 안에 있습니다. 파일은 서버 메모리에서
   진단하며 새로운 대상으로 등록하거나 저장 후보를 바꾸지 않습니다. FASTA 진단 한도
   64KiB, mmCIF 8MiB입니다. 구조의 chain FASTA는 full reference와 다를 수 있습니다.
2. **Candidates**: 저장된 첫 5개 또는 전체 19개; 최대 3개 비교와 CSV 다운로드.
   표와 내려받기는 기존 순위·점수를 보존합니다.
3. **Structure**: 실제 1ISP 기준 구조. full32는 원자가 없어 강조하지 않습니다.
   S108은 검증한 join의 author77을 사용합니다. 드래그·스크롤·Rotate·Fit reference를
   사용할 수 있습니다. 구조는 변이의 실험 검증이나 기하 검증 결과가 아닙니다.
4. **Meta trace**: 저장된 Meta와 MCP의 교대, 실제 도구 인수·공개 출력.
5. **Evidence**: 로컬 일관성 검사, 원래 source mode, 알 수 없는 비용과 검증 범위.

**Start guided demo**는 위 입력·비교·구조·도구 상태를 실제로 바꿉니다. 8단계,
기본은 수동 다음/이전이며 배경 딤·영역 강조·실제 단계 이미지가 표시됩니다. 선택한 자동재생은 단계당 7초입니다. 닫기·건너뛰기·Esc로 종료합니다. Exit는 시작 전
입력과 선택을 복구합니다. 이 시간은 시연 간격이며 모델 계산 시간 측정이 아닙니다.
화면에 REPLAY를 표시하고 새 모델 호출·점수 계산·유료 실행 활성화는 하지 않습니다.

## 대화와 저장 결과

같은 디자인과 Saved review / Live session 메뉴로 연결했고 Light/Dark 선택도 링크로
전달합니다. 실행 프로그램은 분리해 저장 결과 화면의 provider·subprocess 접근 차단을
유지합니다. 대화 예시는 전송 없이 입력란만 채웁니다. 세션은 기본 unarmed이며,
실행 승인과 코드 예산은 별도입니다. 현재 제품 모델은 Meta `muse-spark-1.3`입니다.

## 추가 과학 근거

Atlas의 실제 등록 WT 조회를 정제한 해시 고정 snapshot을 MCP에서 제공합니다.
원래 저장 실행보다 나중에 수집한 근거이며 과거 Meta trace에 섞지 않습니다. Atlas
pTM·pLDDT는 null입니다. ESM3·ESMFold2 worker와 실제 GPU 검증 진행 상태는
[선택 근거 실행 안내](OPTIONAL_SCIENCE_KO.md)와 STATUS를 확인하세요.

## 이번 확인

Light의 React Aria 선택·단계 버튼·본문 span·캡션·토글·체크박스·도움말 SVG,
대화 입력과 3D 배경을 확인했습니다. 기본 Chrome 1064×703에서 결과·대화 화면을
캡처했고 좁은 인앱 화면에서도 조작했습니다. 측정한 본문·캡션·입력 대비만의
범위이며 전체 WCAG 인증은 아닙니다. 사진은 local_artifacts/refinement_20261028에
있고 공개 배포물로 게시하지 않았습니다. 이전 영상은 이전 UI 기록으로 보존했습니다.

실제 GPU 예측 두 건도 완료했습니다: ESMFold2 WT44.776초, ESM3 A32V6.478초. Structure → Additional evidence에서 저장된 PDB를 선택해 봅니다. 다른 모델·입력이므로 변이 효과나 모델 정확도의 비교 실험은 아닙니다.
