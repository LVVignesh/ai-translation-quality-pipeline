"""Sample benchmark datasets for Voxiis AI Translation & Quality Scoring Pipeline.

Includes the exact 10 context-ambiguous translation strings and 8 candidate evaluation pairs
specified in the Voxiis interview assessment requirements.
"""

from typing import List
from schemas import QualityEvaluationInput, TranslationInput

# 10 Benchmark Context-Aware Translation Test Cases
SAMPLE_TRANSLATION_INPUTS: List[TranslationInput] = [
    TranslationInput(
        key="ticket.button.open",
        context="Button an agent clicks to open a closed support ticket back up",
        english="Open",
    ),
    TranslationInput(
        key="settings.hours.status_label_open",
        context="Label shown when the support desk is currently open for business",
        english="Open",
    ),
    TranslationInput(
        key="ticket.button.close",
        context="Button to mark a ticket as resolved",
        english="Close",
    ),
    TranslationInput(
        key="feed.button.post",
        context="Button to publish a new post to the internal team feed",
        english="Post",
    ),
    TranslationInput(
        key="mail.label.post",
        context="Label for a physical mail correspondence address field",
        english="Post",
    ),
    TranslationInput(
        key="ticket.button.assign",
        context="Button to assign a ticket to a specific agent",
        english="Assign",
    ),
    TranslationInput(
        key="ticket.field.due",
        context="Field showing the due date for resolving a ticket",
        english="Due",
    ),
    TranslationInput(
        key="invoice.field.amount_due",
        context="Field showing the amount of money owed",
        english="Due",
    ),
    TranslationInput(
        key="ticket.button.share",
        context="Button to share a ticket link",
        english="Share",
    ),
    TranslationInput(
        key="report.button.export",
        context="Button to export a report as CSV/PDF",
        english="Export",
    ),
]

# 8 Benchmark Quality Evaluation Candidate Test Cases
SAMPLE_QUALITY_INPUTS: List[QualityEvaluationInput] = [
    QualityEvaluationInput(
        key="ticket.button.open",
        context="Button an agent clicks to open a closed support ticket back up",
        english="Open",
        translation="Abierto",
    ),
    QualityEvaluationInput(
        key="ticket.button.close",
        context="Button to mark a ticket as resolved",
        english="Close",
        translation="Cerrar",
    ),
    QualityEvaluationInput(
        key="invoice.field.amount_due",
        context="Field showing the amount of money owed",
        english="Due",
        translation="Vencido",
    ),
    QualityEvaluationInput(
        key="ticket.field.due",
        context="Field showing the due date for resolving a ticket",
        english="Due",
        translation="Vencimiento",
    ),
    QualityEvaluationInput(
        key="ticket.button.assign",
        context="Button to assign a ticket to a specific agent",
        english="Assign",
        translation="Asignar",
    ),
    QualityEvaluationInput(
        key="ticket.button.share",
        context="Button to share a ticket link",
        english="Share",
        translation="Compartir",
    ),
    QualityEvaluationInput(
        key="feed.button.post",
        context="Button to publish a new post to the internal team feed",
        english="Post",
        translation="Correo",  # Intentionally flawed candidate (translating social post as mail)
    ),
    QualityEvaluationInput(
        key="report.button.export",
        context="Button to export a report as CSV/PDF",
        english="Export",
        translation="Exportar",
    ),
]
