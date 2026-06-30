import json
import logging
import os

from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": (
                datetime.now(timezone.utc)
                .isoformat()
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        for attribute in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms"
        ):
            value = getattr(
                record,
                attribute,
                None
            )

            if value is not None:
                payload[attribute] = value

        if record.exc_info:
            payload["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            payload,
            ensure_ascii=False
        )


def configure_logging(app):
    log_folder = app.config[
        "LOG_FOLDER"
    ]

    os.makedirs(
        log_folder,
        exist_ok=True
    )

    level_name = str(
        app.config.get(
            "LOG_LEVEL",
            "INFO"
        )
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO
    )

    formatter = JsonFormatter()

    file_handler = RotatingFileHandler(
        os.path.join(
            log_folder,
            "ai_studio.log"
        ),
        maxBytes=app.config[
            "LOG_MAX_BYTES"
        ],
        backupCount=app.config[
            "LOG_BACKUP_COUNT"
        ],
        encoding="utf-8"
    )

    file_handler.setFormatter(
        formatter
    )
    file_handler.setLevel(
        level
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        formatter
    )
    stream_handler.setLevel(
        level
    )

    app.logger.handlers.clear()
    app.logger.setLevel(
        level
    )
    app.logger.propagate = False
    app.logger.addHandler(
        stream_handler
    )
    app.logger.addHandler(
        file_handler
    )
