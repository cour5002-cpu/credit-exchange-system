from flask import flash, redirect, url_for


LEGACY_WRITE_MESSAGE = "该旧版操作入口已停用，请使用新版业务入口办理。"


def block_legacy_write(redirect_endpoint, **values):
    """Keep legacy pages readable without allowing them to bypass the V1 state machine."""

    flash(LEGACY_WRITE_MESSAGE, "warning")
    return redirect(url_for(redirect_endpoint, **values))
