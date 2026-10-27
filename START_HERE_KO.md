# BioPilot Atlas v3: 먼저 읽어 주세요

2026-10-27 실제 로컬 구현을 시작했습니다. [실행 안내](docs/IMPLEMENTATION_KO.md)와
[현재 상태](docs/STATUS.md)를 먼저 확인하세요. 아래는 원본 패키지 설명을 보존한 내용입니다.

수정일: 2026-10-27. 이 ZIP은 v2 전체를 대체하는 수정본입니다.

| 항목 | 적용 방향 |
|---|---|
| Track | Indie Developer |
| Theme | Push the Frontier |
| 핵심 구성 | Meta runtime + BioPilot MCP Server + ESM |
| 시연 화면 | Streamlit (선택 기능) |
| 심사 비중 | Impact 30% / Meta 25% / Technical 20% / Demo 25% |
| 영상 | 3분 (180초) |

**완성된 앱이나 검증된 내열성 예측 모델이 아닙니다.** 설계서, 프롬프트, 설정과 오프라인 검증 예제가 들어 있습니다.

## 시작 순서

1. `BIOPILOT_ATLAS_KO.md`, `docs/14_hackathon_rules_and_strategy.md`, `docs/15_mcp_contract_and_hosts.md`를 읽습니다.
2. 아래 명령으로 오프라인 검사를 실행합니다.
3. WORK / Muse Code / Codex / Claude Code에서 폴더를 열고 `prompts/coding/00_bootstrap_ko.txt`를 전달합니다.
4. `docs/superpowers/plans/2026-10-27-v3-mcp-hackathon.md`의 순서로 구현합니다.

```bash
python -m unittest discover -s tests -v
python checks/validate_package.py
```

## 주의할 점

심사 기준은 대화에서 직접 확인한 공식 참가자 안내를 반영했습니다. 이번에는 브라우저 연결이 되지 않아 제출 전 최종 규칙과 양식을 다시 확인해야 합니다.

v2의 서열 대응, 촉매 잔기 보호, T50 정의와 정답 분리 원칙은 유지합니다. ESM 점수를 내열성 개선의 증거로 바꾸어 표현하지 않습니다.

**ProteinGym 실험 정답은 MCP 도구로 공개하지 않습니다.** 예측 에이전트에게 이 패키지 전체를 연결하지 말고, 허용된 자료만 별도 폴더에 놓습니다.

유료 호출, GPU 생성, 배포, 저장소 공개와 대회 제출은 별도 승인이 필요합니다. 사전 준비물을 대회 중 새로 만든 코드로 표시하지 않습니다.

기존 폴더에 일부만 덮어쓰지 말고, 새 폴더에 전체 압축을 해제해 사용하세요.
