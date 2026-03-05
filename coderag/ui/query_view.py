"""Query view widgets for asking repository questions."""

from PySide6.QtWidgets import (
    QFrame,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class QueryView(QWidget):
    """UI panel that handles natural language queries."""

    def __init__(self) -> None:
        """Initialize query form and answer output widgets."""
        super().__init__()

        self.title_label = QLabel("Consulta")
        self.subtitle_label = QLabel(
            "Haz preguntas sobre el repositorio indexado y revisa la respuesta sintetizada."
        )
        self.status_chip = QLabel("Lista")
        self.status_chip.setObjectName("queryStatusChip")
        self.status_chip.setProperty("state", "idle")

        self.repo_id = QLineEdit()
        self.repo_id.setPlaceholderText("UUID del repositorio")

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Ejemplo: ¿Qué módulos manejan autenticación?")

        self.query_button = QPushButton("Consultar")

        self.answer_output = QTextEdit()
        self.answer_output.setReadOnly(True)
        self.answer_output.setPlaceholderText("La respuesta aparecerá aquí...")

        form = QFormLayout()
        form.addRow("ID de repositorio", self.repo_id)
        form.addRow("Pregunta", self.query_input)

        card = QFrame()
        card.setObjectName("queryCard")
        card.setLayout(form)

        top_bar = QGridLayout()
        top_bar.addWidget(self.title_label, 0, 0)
        top_bar.addWidget(self.status_chip, 0, 1)
        top_bar.addWidget(self.subtitle_label, 1, 0, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(card)
        layout.addWidget(self.query_button)
        layout.addWidget(self.answer_output)
        self.setLayout(layout)

        self.setStyleSheet(
            """
            QWidget {
                font-size: 13px;
            }
            QLabel {
                color: #E5E7EB;
            }
            QueryView {
                background-color: #111827;
            }
            QFrame#queryCard {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel#queryStatusChip {
                padding: 4px 10px;
                border-radius: 10px;
                font-weight: 600;
                color: #F3F4F6;
                background-color: #4B5563;
                qproperty-alignment: AlignCenter;
            }
            QLabel#queryStatusChip[state="running"] {
                background-color: #1D4ED8;
            }
            QLabel#queryStatusChip[state="success"] {
                background-color: #15803D;
            }
            QLabel#queryStatusChip[state="error"] {
                background-color: #B91C1C;
            }
            QLineEdit, QTextEdit {
                background-color: #0F172A;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-weight: 700;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #CBD5E1;
            }
            """
        )

    def set_status(self, state: str, text: str) -> None:
        """Update query status chip state and text."""
        valid_states = {"idle", "running", "success", "error"}
        selected_state = state if state in valid_states else "idle"
        self.status_chip.setProperty("state", selected_state)
        self.status_chip.setText(text)
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)

    def set_running(self, running: bool) -> None:
        """Enable and disable controls while query request is in progress."""
        self.repo_id.setDisabled(running)
        self.query_input.setDisabled(running)
        self.query_button.setDisabled(running)
        self.query_button.setText("Consultando..." if running else "Consultar")

    def set_answer(self, text: str) -> None:
        """Render answer or informational message."""
        self.answer_output.setPlainText(text)
