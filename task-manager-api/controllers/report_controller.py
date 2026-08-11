"""Controller de relatórios: agregações via Models (RP-05/RP-09)."""
from datetime import timedelta

from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import (
    HIGH_PRIORITY_THRESHOLD,
    RECENT_ACTIVITY_DAYS,
    STATUS_DONE,
    calculate_percentage,
    format_datetime,
    now_utc,
)

# Rótulos do contrato de /reports/summary para as prioridades 1..5.
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def summary_report():
    status_counts = Task.counts_by_status()
    priority_counts = Task.counts_by_priority()
    total_tasks = sum(status_counts.values())

    overdue_tasks = Task.overdue_tasks()
    overdue_list = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': format_datetime(task.due_date),
            'days_overdue': task.days_overdue(),
        }
        for task in overdue_tasks
    ]

    recent_cutoff = now_utc() - timedelta(days=RECENT_ACTIVITY_DAYS)

    user_stats = [
        {
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        }
        for user_id, user_name, total, completed in User.productivity_stats()
    ]

    report = {
        'generated_at': format_datetime(now_utc()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {
            'pending': status_counts['pending'],
            'in_progress': status_counts['in_progress'],
            'done': status_counts[STATUS_DONE],
            'cancelled': status_counts['cancelled'],
        },
        'tasks_by_priority': {
            label: priority_counts[priority] for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(recent_cutoff),
            'tasks_completed_last_7_days': Task.count_completed_since(recent_cutoff),
        },
        'user_productivity': user_stats,
    }
    return report, 200


def user_report(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.for_user(user_id)
    status_totals = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    overdue = 0
    high_priority = 0
    for task in tasks:
        if task.status in status_totals:
            status_totals[task.status] += 1
        if task.priority is not None and task.priority <= HIGH_PRIORITY_THRESHOLD:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': status_totals[STATUS_DONE],
            'pending': status_totals['pending'],
            'in_progress': status_totals['in_progress'],
            'cancelled': status_totals['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(status_totals[STATUS_DONE], total),
        },
    }
    return report, 200
