import os
import shutil
import uuid

from flask import current_app

from database import db

from database.models import (
    Document,
    GlobalDocument,
    MessageAttachment,
    SocialSource,
    WebsiteSource,
    user_social_sources,
    user_website_sources
)


class FileTrash:
    def __init__(self, upload_folder):
        self.upload_folder = os.path.abspath(
            upload_folder
        )

        self.trash_folder = os.path.join(
            self.upload_folder,
            ".trash"
        )

        self.entries = []

        os.makedirs(
            self.trash_folder,
            exist_ok=True
        )

    def stage(self, stored_filename):
        if not stored_filename:
            return

        source_path = os.path.abspath(
            os.path.join(
                self.upload_folder,
                stored_filename
            )
        )

        if os.path.commonpath([
            source_path,
            self.upload_folder
        ]) != self.upload_folder:
            raise ValueError(
                "Unsafe upload filename."
            )

        if not os.path.exists(
            source_path
        ):
            return

        trash_name = (
            f"{uuid.uuid4().hex}-"
            f"{os.path.basename(stored_filename)}"
        )

        trash_path = os.path.join(
            self.trash_folder,
            trash_name
        )

        os.replace(
            source_path,
            trash_path
        )

        self.entries.append({
            "source": source_path,
            "trash": trash_path
        })

    def rollback(self):
        for entry in reversed(
            self.entries
        ):
            trash_path = entry["trash"]
            source_path = entry["source"]

            if os.path.exists(
                trash_path
            ):
                os.makedirs(
                    os.path.dirname(
                        source_path
                    ),
                    exist_ok=True
                )

                os.replace(
                    trash_path,
                    source_path
                )

    def commit(self):
        failures = []

        for entry in self.entries:
            trash_path = entry["trash"]

            try:
                if os.path.isdir(
                    trash_path
                ):
                    shutil.rmtree(
                        trash_path
                    )
                elif os.path.exists(
                    trash_path
                ):
                    os.remove(
                        trash_path
                    )
            except OSError as error:
                failures.append(
                    str(error)
                )

        return failures


def delete_chat_with_files(chat):
    trash = FileTrash(
        current_app.config[
            "UPLOAD_FOLDER"
        ]
    )

    for document in list(chat.documents):
        trash.stage(document.stored_filename)

    for attachment in list(chat.attachments):
        trash.stage(attachment.stored_filename)

    try:
        db.session.delete(
            chat
        )
        db.session.commit()

    except Exception:
        db.session.rollback()
        trash.rollback()
        raise

    failures = trash.commit()

    if failures:
        current_app.logger.warning(
            "Some staged chat files could not be removed: %s",
            failures
        )


def delete_document_with_file(document):
    trash = FileTrash(
        current_app.config[
            "UPLOAD_FOLDER"
        ]
    )

    trash.stage(
        document.stored_filename
    )

    try:
        db.session.delete(
            document
        )
        db.session.commit()

    except Exception:
        db.session.rollback()
        trash.rollback()
        raise

    failures = trash.commit()

    if failures:
        current_app.logger.warning(
            "A staged document file could not be removed: %s",
            failures
        )


def delete_global_document_with_file(
    document
):
    trash = FileTrash(
        current_app.config[
            "UPLOAD_FOLDER"
        ]
    )

    trash.stage(
        document.stored_filename
    )

    try:
        db.session.delete(
            document
        )
        db.session.commit()

    except Exception:
        db.session.rollback()
        trash.rollback()
        raise

    failures = trash.commit()

    if failures:
        current_app.logger.warning(
            "A staged global document file could not be removed: %s",
            failures
        )




def delete_attachment_with_file(attachment):
    trash = FileTrash(
        current_app.config["UPLOAD_FOLDER"]
    )
    trash.stage(attachment.stored_filename)

    try:
        db.session.delete(attachment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        trash.rollback()
        raise

    failures = trash.commit()
    if failures:
        current_app.logger.warning(
            "A staged attachment file could not be removed: %s",
            failures
        )



def delete_user_with_files(user):
    trash = FileTrash(
        current_app.config["UPLOAD_FOLDER"]
    )

    website_source_ids = [source.id for source in list(user.website_sources)]
    social_source_ids = [source.id for source in list(user.social_sources)]

    for chat in list(user.chats):
        for document in list(chat.documents):
            trash.stage(document.stored_filename)
        for attachment in list(chat.attachments):
            trash.stage(attachment.stored_filename)

    for document in list(user.global_documents):
        trash.stage(document.stored_filename)

    try:
        db.session.delete(user)
        db.session.flush()

        for source_id in website_source_ids:
            membership = db.session.execute(
                db.select(user_website_sources.c.user_id).where(
                    user_website_sources.c.website_source_id == source_id
                )
            ).first()
            if not membership:
                source = db.session.get(WebsiteSource, source_id)
                if source:
                    db.session.delete(source)

        for source_id in social_source_ids:
            membership = db.session.execute(
                db.select(user_social_sources.c.user_id).where(
                    user_social_sources.c.social_source_id == source_id
                )
            ).first()
            if not membership:
                source = db.session.get(SocialSource, source_id)
                if source:
                    db.session.delete(source)

        db.session.commit()

    except Exception:
        db.session.rollback()
        trash.rollback()
        raise

    failures = trash.commit()
    if failures:
        current_app.logger.warning(
            "Some account files could not be removed: %s",
            failures
        )

def find_orphan_uploads(
    upload_folder
):
    referenced = {
        filename
        for filename, in db.session.query(
            Document.stored_filename
        ).all()
        if filename
    }

    referenced.update({
        filename
        for filename, in db.session.query(
            GlobalDocument.stored_filename
        ).all()
        if filename
    })

    referenced.update({
        filename
        for filename, in db.session.query(
            MessageAttachment.stored_filename
        ).all()
        if filename
    })

    ignored = {
        ".gitkeep"
    }

    orphan_paths = []

    if not os.path.isdir(
        upload_folder
    ):
        return orphan_paths

    for filename in os.listdir(
        upload_folder
    ):
        path = os.path.join(
            upload_folder,
            filename
        )

        if filename in ignored:
            continue

        if filename == ".trash":
            continue

        if os.path.isfile(
            path
        ) and filename not in referenced:
            orphan_paths.append(
                path
            )

    return orphan_paths


def remove_orphan_uploads(
    upload_folder
):
    orphan_paths = find_orphan_uploads(
        upload_folder
    )

    removed = []
    failures = []

    for path in orphan_paths:
        try:
            os.remove(
                path
            )
            removed.append(
                path
            )
        except OSError as error:
            failures.append({
                "path": path,
                "error": str(error)
            })

    return {
        "removed": removed,
        "failures": failures
    }
