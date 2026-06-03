import os

from flask import Blueprint, abort, current_app, render_template, send_from_directory
from flask_login import login_required

from app.models.hour_application_attachment import HourApplicationAttachment


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/attachments/<int:attachment_id>")
@login_required
def view_attachment(attachment_id):
    attachment = HourApplicationAttachment.query.filter_by(id=attachment_id).first()
    if not attachment:
        abort(404)

    absolute_path = os.path.join(current_app.root_path, attachment.file_path.replace("/", os.sep))
    directory = os.path.dirname(absolute_path)
    filename = os.path.basename(absolute_path)
    if not os.path.exists(absolute_path):
        abort(404)

    return send_from_directory(directory, filename, as_attachment=False, download_name=attachment.file_name)
