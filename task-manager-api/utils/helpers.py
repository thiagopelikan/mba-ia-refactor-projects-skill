"""Validadores, constantes e utilitários canônicos do domínio (RP-11/RP-14/RP-15).

Este módulo é a ÚNICA fonte das constantes de negócio e das validações de
entrada — antes duplicadas entre as rotas e uma versão morta deste mesmo
arquivo. Funções mortas da versão original (generate_id, log_action,
sanitize_string, format_date, is_valid_color) foram removidas;
process_task_data foi absorvida por validate_task_payload.
"""
import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constantes de domínio (AP-15 — antes listas/números mágicos espalhados)
# ---------------------------------------------------------------------------
VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
TERMINAL_STATUSES = ('done', 'cancelled')
STATUS_DONE = 'done'
DEFAULT_STATUS = 'pending'

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridade <= 2 conta como "high" nos relatórios

DEFAULT_COLOR = '#000000'
RECENT_ACTIVITY_DAYS = 7
DATE_FORMAT = '%Y-%m-%d'

_EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$')


# ---------------------------------------------------------------------------
# Datetime (RP-10 — substitui datetime.utcnow, deprecated)
# ---------------------------------------------------------------------------
def now_utc():
    """Instante atual timezone-aware em UTC."""
    return datetime.now(timezone.utc)


def ensure_utc(dt):
    """Normaliza datetimes para UTC aware.

    Valores persistidos no SQLite voltam naive (o driver descarta o offset);
    como toda escrita é feita em UTC, naive é interpretado como UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_datetime(dt):
    """Serializa datetime no formato histórico da API ('YYYY-MM-DD HH:MM:SS[.ffffff]')."""
    if dt is None:
        return None
    return str(ensure_utc(dt).replace(tzinfo=None))


def parse_date(date_string):
    """Converte 'YYYY-MM-DD' (único formato do contrato) em datetime UTC, ou None."""
    try:
        return datetime.strptime(date_string, DATE_FORMAT).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Utilitários de cálculo
# ---------------------------------------------------------------------------
def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)


# ---------------------------------------------------------------------------
# Validadores de payload (RP-11) — retornam (campos_normalizados, None)
# ou (None, mensagem_de_erro)
# ---------------------------------------------------------------------------
def validate_email(email):
    return bool(isinstance(email, str) and _EMAIL_REGEX.match(email))


def validate_task_payload(data, partial=False):
    """Valida e normaliza o payload de task (create quando partial=False)."""
    if not isinstance(data, dict) or not data:
        return None, 'Dados inválidos'

    fields = {}

    if not partial or 'title' in data:
        title = data.get('title')
        if not isinstance(title, str) or not title.strip():
            return None, 'Título é obrigatório'
        title = title.strip()
        if len(title) < MIN_TITLE_LENGTH:
            return None, 'Título muito curto'
        if len(title) > MAX_TITLE_LENGTH:
            return None, 'Título muito longo'
        fields['title'] = title

    if 'description' in data:
        fields['description'] = data['description']
    elif not partial:
        fields['description'] = ''

    if not partial or 'status' in data:
        status = data.get('status', DEFAULT_STATUS)
        if status not in VALID_STATUSES:
            return None, 'Status inválido'
        fields['status'] = status

    if not partial or 'priority' in data:
        priority = data.get('priority', DEFAULT_PRIORITY)
        try:
            priority = int(priority)
        except (TypeError, ValueError):
            return None, 'Prioridade deve ser entre 1 e 5'
        if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            return None, 'Prioridade deve ser entre 1 e 5'
        fields['priority'] = priority

    if 'user_id' in data:
        fields['user_id'] = data['user_id']
    if 'category_id' in data:
        fields['category_id'] = data['category_id']

    if 'due_date' in data:
        raw_due_date = data['due_date']
        if raw_due_date:
            parsed = parse_date(raw_due_date)
            if parsed is None:
                return None, 'Formato de data inválido. Use YYYY-MM-DD'
            fields['due_date'] = parsed
        else:
            fields['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        fields['tags'] = ','.join(tags) if isinstance(tags, list) else tags

    return fields, None


def validate_user_payload(data, partial=False):
    """Valida e normaliza o payload de usuário (create quando partial=False)."""
    if not isinstance(data, dict) or not data:
        return None, 'Dados inválidos'

    fields = {}

    if not partial:
        if not data.get('name'):
            return None, 'Nome é obrigatório'
        if not data.get('email'):
            return None, 'Email é obrigatório'
        if not data.get('password'):
            return None, 'Senha é obrigatória'

    if not partial or 'name' in data:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            return None, 'Nome é obrigatório'
        fields['name'] = name

    if not partial or 'email' in data:
        email = data.get('email')
        if not validate_email(email):
            return None, 'Email inválido'
        fields['email'] = email

    if not partial or 'password' in data:
        password = data.get('password')
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            return None, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'
        fields['password'] = password

    if not partial or 'role' in data:
        role = data.get('role', DEFAULT_ROLE)
        if role not in VALID_ROLES:
            return None, 'Role inválido'
        fields['role'] = role

    if 'active' in data:
        if not isinstance(data['active'], bool):
            return None, "Campo 'active' deve ser booleano"
        fields['active'] = data['active']

    return fields, None


def validate_category_payload(data, partial=False):
    """Valida e normaliza o payload de categoria (create quando partial=False)."""
    if not isinstance(data, dict) or not data:
        return None, 'Dados inválidos'

    fields = {}

    if not partial or 'name' in data:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            return None, 'Nome é obrigatório'
        fields['name'] = name

    if 'description' in data:
        fields['description'] = data['description']
    elif not partial:
        fields['description'] = ''

    if 'color' in data:
        fields['color'] = data['color']
    elif not partial:
        fields['color'] = DEFAULT_COLOR

    return fields, None
