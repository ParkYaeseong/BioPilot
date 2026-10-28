"""Local tutorial presentation; it can only activate existing safe tour controls."""
import base64
import json
from pathlib import Path

from app.guided_tour import STEPS

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'valid_input': '.st-key-tour_input',
    'protected_input': '.st-key-tour_input',
    'compare': '.st-key-comparison_table',
    'unmodelled_position': '.st-key-tour_structure',
    'protected_structure': '.st-key-tour_structure',
    'validation_trace': '.st-key-trace_card_1',
    'scoring_trace': '.st-key-trace_card_2',
    'provenance': '.st-key-tour_provenance',
}
COPY = (
    ('검토할 변이를 입력합니다', 'Input 화면에서 A32V를 입력하고 번호와 목표를 확인합니다. 등록된 참조에 대한 실제 로컬 검사가 실행되어 있습니다.', 'A32V 통과 결과를 확인한 뒤 다음으로 이동하세요.'),
    ('보호 잔기 차단을 확인합니다', '같은 입력 영역에 S108A를 적용했습니다. 촉매 잔기 보호 규칙이 요청을 차단한 이유를 확인하세요.', '이 검사는 코드가 수행합니다. 기능 유지의 실험 증거를 뜻하지 않습니다.'),
    ('후보 세 개를 나란히 비교합니다', 'Candidates로 이동해 저장된 상위 세 후보를 선택했습니다. 순위와 ESM 서열 선호도를 같은 기준으로 비교합니다.', '선택과 CSV 내보내기는 원래 점수와 순위를 유지합니다.'),
    ('실험 구조에 없는 위치도 확인합니다', 'Structure에서 A32 후보를 선택했습니다. 1ISP에서 full 32는 원자가 없어 해당 위치를 강조하지 않습니다.', '보이지 않는 잔기를 주변 원자로 대신 표시하지 않습니다.'),
    ('실제 구조에서 보호 잔기를 찾습니다', 'S108을 선택했습니다. 검증된 번호 연결에 따라 author 77을 강조합니다. 구조를 드래그하거나 Rotate로 회전해 보세요.', '이 화면은 실험 기준 구조이며 변이 단백질의 검증 결과가 아닙니다.'),
    ('Meta가 요청한 검증을 봅니다', 'Meta trace로 이동했습니다. 첫 번째 MCP 호출의 공개 근거와 실제 인수·결과를 확인합니다.', '저장된 실행 기록입니다. 새 Meta 요청을 보내지 않습니다.'),
    ('계산과 모델 설명을 구분합니다', '두 번째 MCP 호출을 열었습니다. ESM은 선호도를 계산하고, 등록된 코드가 공통 정책으로 순위를 정합니다.', 'ESM 점수는 T50·활성·용해도·Tm 측정값이 아닙니다.'),
    ('결과를 뒷받침하는 기록을 확인합니다', 'Evidence에서 저장 점수와 표시된 후보의 일관성 검사를 확인합니다. 알 수 없는 비용과 검증 범위도 남겨 둡니다.', '완료 또는 닫기를 누르면 시작 전 입력과 선택으로 돌아갑니다.'),
)


def spotlight_document(index, *, appearance='Dark', playing=False):
    if index is None:
        return '<script>const d=window.parent.document;d.getElementById("bio-tour-root")?.remove();d.body.classList.remove("tour-overlay-active");</script>'
    step = STEPS[index]
    path = ROOT / 'assets' / 'tour' / (step.id + '.png')
    picture = ('data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')) if path.is_file() else None
    title, body, tip = COPY[index]
    payload = {'index': index, 'count': len(STEPS), 'selector': TARGETS[step.id],
               'title': title, 'body': body, 'tip': tip, 'picture': picture,
               'light': appearance == 'Light', 'playing': playing,
               'focus_height': 340 if step.focus == 'trace' else (450 if step.focus == 'evidence' else None)}
    data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    script = (ROOT/'tour_spotlight.js').read_text(encoding='utf-8')
    return '<script>const tourData=' + data + ';\n' + script + '</script>'
