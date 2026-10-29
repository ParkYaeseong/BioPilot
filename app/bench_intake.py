"""Freeze only executable public registered input; never dispatch or upload files."""
import hashlib
from pathlib import PurePosixPath

from app.core.targets import REFERENCE_SHA256, COORDINATE_SOURCE_SHA256
from app.review_flow import prepare_review
from app.upload_checks import check_sequence, MAX_SEQUENCE_BYTES, MAX_STRUCTURE_BYTES
from app.viewer_structure import verify_reference


def freeze_input(message, *, input_kind, fasta=None, filename=None, cif=None, model_key='esm150'):
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 800:
        raise ValueError('Enter a request with 1–800 characters; nothing was sent.')
    if input_kind not in ('example', 'upload'):
        raise ValueError('Select the registered example or upload its full-reference FASTA.')
    if input_kind == 'upload':
        if not isinstance(fasta, bytes) or not fasta or len(fasta) > MAX_SEQUENCE_BYTES:
            raise ValueError('Upload one full-reference FASTA of at most 64 KB.')
        try:
            checked = check_sequence(fasta.decode('utf-8-sig'))
        except UnicodeError as error:
            raise ValueError('FASTA must be UTF-8 text.') from error
        if not checked['reviewable']:
            raise ValueError(checked['detail'])
    elif fasta is not None:
        raise ValueError('An uploaded file must use the upload input path; no hidden substitution.')
    if cif is not None:
        if not isinstance(cif, bytes) or len(cif) > MAX_STRUCTURE_BYTES:
            raise ValueError('Optional mmCIF is limited to 8 MB.')
        try:
            structure = verify_reference(cif_text=cif.decode('utf-8'))
        except UnicodeError as error:
            raise ValueError('mmCIF must be UTF-8 text.') from error
        if structure['status'] != 'verified_index_join':
            raise ValueError('Optional structure must match the pinned public 1ISP mmCIF. Remove it to review the registered sequence alone; uploaded coordinates are never guessed.')
    request = prepare_review(message.strip(), model_key)
    name = PurePosixPath(str(filename or 'reference.fasta').replace('\\', '/')).name
    name = ''.join(c for c in name if c.isprintable())[:120]
    return {**request, 'objective_id':'sequence_plausibility_review',
            'input_kind':input_kind, 'filename':name if input_kind=='upload' else 'Registered public Lipase A',
            'reference_sha256':REFERENCE_SHA256, 'sequence_context':'full_212',
            'fasta_sha256':hashlib.sha256(fasta).hexdigest() if fasta is not None else None,
            'structure_sha256':COORDINATE_SOURCE_SHA256 if cif is not None else None,
            'external_file_upload':False}


def validate_frozen(request):
    expected = prepare_review(request['message'], request['model_key'])
    if (request['reference_sha256'] != REFERENCE_SHA256 or request['sequence_context'] != 'full_212'
            or request['positions'] != expected['positions']
            or request['objective_id'] != 'sequence_plausibility_review'
            or request['input_kind'] not in ('example','upload')
            or request.get('structure_sha256') not in (None, COORDINATE_SOURCE_SHA256)
            or request.get('external_file_upload') is not False):
        raise ValueError('Frozen input does not match the registered execution contract.')
    if request['input_kind']=='upload' and not request.get('fasta_sha256'):
        raise ValueError('Uploaded input must retain its source-file hash.')
    return request
