# ESM3·ESMFold2·Atlas 선택 근거 — 2026-10-28

현재 기준 순위는 ESM-2 150M의 `esm150_masked_v1`입니다. ESM3·ESMFold2·Atlas는
추가 검토 근거이며 기존 점수나 순위를 덮어쓰지 않습니다. 예측 구조, pLDDT, pTM은
T50·활성·용해도·기능 유지·실험 검증값이 아닙니다.

## 실제 구현과 실행 상태

| 구성 | 구현 | 실제 실행 증거 |
|---|---|---|
| ESM3 open 1.4B | 공식 SDK 로컬 structure-track adapter, 전체 212개 서열 보존 검사 | 실제 L40S A32V 실행6.478초; 저장 PDB·서열·해시 검증 |
| ESMFold2 | 공식 SDK 로컬 PDB inference adapter, 고정 sampling·seed·chunk | 실제 L40S WT 실행44.776초; 저장 PDB·서열·해시 검증 |
| Biohub ESM Atlas | 등록 WT의 정확한 MD5로 고정 GET, `fold_on_miss=false`; 제품 MCP에는 핀 snapshot만 제공 | HTTP 200, `validation/atlas_registered_reference_20261028.json`; 실제 stdio tool call 검증 |
| BOP GPU | 사용자 지정 서버의 SSH 연결 사전 확인 | 기존 표준 SSH 키로 원래 pipeline 계정 접속; L40S2개 확인; 전용 SDK 환경에서 단일 GPU 작업2건 완료 |
| RunPod | 기존 서버 설정은 명시적 미설정 유지 | Pod·endpoint·이미지 배포·과금 없음 |

Atlas 실제 응답은 등록 WT full_212 서열과 길이·MD5가 모두 일치했습니다. IMG source
accession `2702335490`, SAE feature 10개가 기록되어 있습니다. 저장된 구조의 pTM과
mean pLDDT는 `null`이므로 구조가 존재한다고 주장하지 않습니다. 조회는 새로운 feature나
구조 계산을 요청하지 않았습니다. 원문 header·기능 설명·SAE 설명은 결과성 텍스트나
주입 지시를 호스트에 전달하지 않도록 폐기하고, 원문 bytes의 SHA256만 영수증에 남겼습니다.
이는 원문을 다시 계산 검증할 수 있는 보관본이나 제공자 서명 인증을 뜻하지 않습니다.

현재 앱의 Meta 제품 모델은 그대로 Meta Model API `muse-spark-1.3`입니다. ESM3,
ESMFold2와 현재 Atlas의 운영 주체는 Biohub이며 Meta 제품 모델 사용 실적으로 섞지 않습니다.
기존 `facebookresearch/esm`과 2023 Meta Atlas 경로도 별도 출처입니다.

과거 Atlas 보류 결정 이후 이번 사용자의 명시적인 구현 요청으로, 외부 계산 없는
**고정 WT snapshot 경로**를 활성화했습니다. `reference/atlas_snapshot_policy.json`의
enabled 선언, 코드의 고정 SHA256, 엄격한 안전 필드 검사가 모두 맞을 때만
`retrieve_atlas_evidence`가 catalog에 나타나고 status의 atlas capability가 true입니다.
파일이 바뀌거나 선언이 false면 직접 tool 호출도 거부합니다. 실행 폴더에는 정제된
snapshot과 offline loader만 복사하고 live HTTP client·operator worker·validation·평가
폴더를 넣지 않습니다. snapshot hash 검증은 upstream authenticity 인증이 아닙니다.

## 안전한 로컬 실행 인터페이스

```powershell
# 상태 읽기: GPU·네트워크 호출 없음
.venv/Scripts/python.exe -m app.science.optional_worker status

# 요청 준비만 수행. 출력이 있으면 거부; 서열은 임의 입력을 받지 않고 등록 참조에서 생성.
.venv/Scripts/python.exe -m app.science.optional_worker prepare `
  --model esmfold2 --variant A32V --output .runtime/optional_A32V_request.json

# 등록 WT Atlas 읽기만. 새 파일 이름을 사용해야 함.
.venv/Scripts/python.exe -m app.science.optional_worker atlas-reference `
  --external-read-approved --output .runtime/atlas_reference_context.json
```

ESM3에는 `--model esm3`을 선택합니다. WT 구조에는 `--variant WT`를 씁니다.
`S108A`, `G32V`, 보호 잔기, mature 번호, 임의 서열은 기존 제품 가드와 동일하게 거부합니다.
새 요청은 전체 212개 기준이며 예측 PDB residue 1은 full reference 1입니다. 1ISP의
181개 mature construct 번호와 섞으면 안 됩니다. 모델 출력의 chain A CA 잔기명과
번호 1..212가 요청 서열과 정확히 맞아야 완료 영수증을 생성합니다. 이 검사는 좌표
기하·접힘 정확도·측쇄 완전성 검증이 아닙니다.

## GPU worker 준비에 필요한 실제 확인

공식 `esm` **v3.4.1.post1 태그**의 패키지 조건은 Python >=3.12,
`torch>=2.11.0,<2.12.0`, `transformers>=4.57.6,<5.0.0`입니다.
공식 main README의 Transformers >=5.16 경로는 별도 HF 구현 경로입니다. 현재 앱의
torch 2.9.1·transformers 5.2.0 환경을 제자리에서 업그레이드하지 않고 전용 Linux worker
환경을 만들어야 합니다. GPU 커널 extras는 추가 CUDA·driver 조건을 확인한 뒤 선택합니다.
현재 전용 GPU 환경에 해당 버전을 설치하고 공식 revision의 파일 해시를 확인했습니다. UI의 로컬 venv는 변경하지 않았습니다.

ESM3는 `biohub/esm3-sm-open-v1`, ESMFold2는 `biohub/ESMFold2`의 공식 snapshot을
정확한 commit revision으로 받아야 합니다. ESMFold2는 6B ESMC backbone을 포함하므로
weights와 실행 중 activations의 메모리가 모두 필요합니다. L40S 48GB에서 212개 단일 체인
실행을 우선 시험하는 것은 합리적이지만, 실제 실행의 driver·runtime·PyTorch 최대 할당량은 영수증에 기록했습니다. 이 두 입력 이외의 길이·작업의 적합성이나 예상 시간으로 일반화하지 않습니다.

`checkpoint_manifest`는 아래 필드만 허용합니다. `files`는 snapshot의 **전체 파일 목록**과
파일별 SHA256입니다. 공식 Hugging Face revision/LFS hash와 대조한 운영자 receipt에서
만들어야 하며, 로컬 파일의 자기 해시만으로 공식 가중치 인증을 주장하면 안 됩니다.

```json
{
  "schema_version": 1,
  "model_key": "esmfold2",
  "repository": "biohub/ESMFold2",
  "revision": "<verified full 40-character commit>",
  "esm_version": "3.4.1.post1",
  "files": {"config.json": "<sha256>", "<every other snapshot file>": "<sha256>"}
}
```

ESMFold2 config에는 bundled `esmc_config`가 있어야 하며 experimental 구조는 지원하지
않습니다. 임의 원격 코드나 별도 backbone 자동 다운로드 경로를 허용하지 않습니다.
ESM3 SDK는 로컬 경로 인수가 없어 전용 HF cache의
`models--biohub--esm3-sm-open-v1/snapshots/<revision>`을 사용하고, 그 cache의 `refs/main`이
핀 revision과 같아야 합니다. SDK import 전에 offline/cache 환경변수를 적용하는 새 worker
프로세스가 필요합니다. 기존 캐시의 main ref를 무단 변경하지 말고 전용 cache를 준비합니다.

준비된 GPU 서버에서 `python -m app.science.optional_worker run --help`로 인터페이스를
확인할 수 있습니다. 실행에는 request SHA256·manifest SHA256·검증된 로컬 checkpoint·새 출력
폴더·`--execution-approved`가 모두 필요합니다. 기본 wall timeout은 300초, 최대 900초,
한 번에 한 구조입니다. timeout은 자식 worker를 종료하며 재시도·모델 fallback을 하지
않습니다. 출력 PDB와 receipt는 새 폴더에만 쓰며 기존 artifact를 덮어쓰지 않습니다.

SSH 사용자 인증, 전용 환경·공식 weights 검증, 사용 가능한 GPU 확인 후 한 건의 실제
실행을 해야 `runtime_verified`를 true로 보고할 수 있습니다. 현재는 두 실제 GPU 실행 영수증이 추가되어 있습니다. SDK mock 테스트 결과와 별도입니다. 원격 배포나 RunPod allocation은 이 CLI에 없습니다.

## Atlas 호출의 숨은 계산 방지

공식 REST GET의 `fold_on_miss` 기본값은 **true**이므로 이 adapter는 항상 false를
명시합니다. Biohub MCP similarity-search는 부수적으로 최대 여섯 hit의 구조를 예측할 수
있으며 get-protein-details도 miss에 feature를 계산할 수 있습니다. 따라서 broad upstream
MCP 전체를 무심코 제품에 연결하지 않습니다. 현재 구현은 등록 WT hash의 한 건 조회만
허용하고, 다른 sequence·accession·arbitrary URL 입력을 받지 않습니다.

조회 실패·redirect·잘못된 서열·`folded_on_demand=true`·비정상 confidence는 모두
`unavailable`입니다. 실패를 0개 hit나 과학적 부재로 바꾸지 않습니다. HTTP operator client를
제품 catalog에 연결하지 않고, 검증·정제된 기존 snapshot만 제품 MCP에 제공합니다.

MCP 응답은 `source_mode=imported_snapshot`,
`original_acquisition_mode=actual_external_http_response`,
`query_scope=exact_registered_wt_only`를 함께 기록합니다. hit 하나는 reference WT의
accession·source·서열 hash·길이·존재하는 구조 confidence·SAE feature 개수뿐입니다.
`max_hits`가 커도 새 검색이나 계산을 하지 않으며, raw sequence·header·기능 설명·
실험 결과 텍스트를 반환하지 않습니다. 과거 저장 Meta trace에 새 tool 사용이 있었다고
소급 표시하지 않습니다. 새로운 Meta가 이 도구를 실제 호출한 증거는 아직 없습니다.

## 공식 확인 출처

- [Biohub SDK 고정 release](https://github.com/Biohub/esm/releases/tag/v3.4.1.post1)
- [태그의 패키지 의존성](https://github.com/Biohub/esm/blob/v3.4.1.post1/pyproject.toml)
- [ESM3 공식 API 사용](https://github.com/Biohub/esm/blob/v3.4.1.post1/_assets/ESM3_README.md)
- [ESMFold2 모델 카드](https://huggingface.co/biohub/ESMFold2)
- [Atlas GET의 fold_on_miss 옵션](https://docs.biohub.ai/api/protein/atlas/proteins/get)
- [Atlas MCP의 compute-on-miss와 부수적 folding](https://docs.biohub.ai/biohub-mcp/esm-atlas-tools)
- [Biohub 모델과 Atlas의 해석 한계](https://www.biohub.ai/limitations)

모델과 dataset의 배포·재사용 조건은 각각의 모델 카드·데이터 조건으로 확인합니다.
현재 공식 모델 문서에는 MIT가 표시되어 있지만 계정 약관을 대신 수락하거나 사전 작업의
권리·대회 자격을 판정하지 않았습니다.

## 실제 실행 영수증과 화면

`validation/optional_science_runtime_20261028.json`과
`demo/artifacts/structures/{esmfold2_WT,esm3_A32V}/`를 확인하세요.
두 출력은 chainA CA 번호1..212와 정확한 WT/A32V 서열을 확인했습니다. 좌표 기하와
생물학적 효과는 검증하지 않았습니다.44.776/6.478초는 파일 해시 검사 이후의 모델
로딩·추론 구간이며 환경 설치·다운로드·전체 연구 시간 측정이 아닙니다. GPU 비용도
청구서로 확인하지 않았습니다. 선택적 fused kernel은 설치하지 않아 공식 PyTorch
연산 경로를 썼고, 모델·provider를 바꾸는 fallback은 하지 않았습니다.

화면은 저장된 실제 예측을 재생합니다. 로컬 `optional_worker status`의
`requires_pinned_worker/runtime_verified:false`는 현재 로컬 프로세스에 실행용 GPU
backend가 설정됐다는 선언을 하지 않는 보수적 상태이며, 위 원격 실제 실행 기록과
구분합니다. 자동 원격 fold MCP는 아직 활성화하지 않았습니다.
