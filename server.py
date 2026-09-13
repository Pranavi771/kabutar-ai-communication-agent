"""
Flask backend for the Kabutar Agent web UI.

This file only wraps agent_core.py in HTTP/SSE plumbing. All LLM calls,
contact resolution, and the Selenium-based WhatsApp / smtplib email send
logic live in agent_core.py and only there.
"""
import json

from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
    stream_with_context,
)

import agent_core as core

app = Flask(__name__, static_folder="static", static_url_path="")


# --------------------------------------------------------------------------
# Frontend
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# --------------------------------------------------------------------------
# Contacts API -- thin wrappers around agent_core's existing contact functions
# --------------------------------------------------------------------------
@app.route("/api/contacts", methods=["GET"])
def api_list_contacts():
    # Returns the raw {key: {display_name, phone, email}} dict as-is --
    # the frontend's loadContacts() does Object.entries() on this directly.
    return jsonify(core.load_contacts())


@app.route("/api/contacts", methods=["POST"])
def api_upsert_contact():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    core.upsert_contact(name, data.get("phone", ""), data.get("email", ""))
    return jsonify({"ok": True})


@app.route("/api/contacts/<name>", methods=["DELETE"])
def api_delete_contact(name):
    core.delete_contact(name)
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Send -- Server-Sent Events, so the frontend's notification bar can show
# live stage-by-stage progress while the (blocking, visible) automation runs.
#
# Note on granularity: agent_core.send_whatsapp() is one blocking call with
# no internal progress hooks, so the events below mark the stage BEFORE and
# AFTER that call, not what's happening inside the Selenium automation
# second-by-second. The actual browser automation is still visible on
# screen the whole time.
# --------------------------------------------------------------------------
def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _send_stream(command: str, platform_key: str, contact_name: str):
    try:
        yield _sse("status", {"text": "Interpreting your request..."})

        try:
            intent = core.extract_intent(command, platform_key, contact_name)
        except Exception as e:
            yield _sse("failed", {"text": f"Couldn't interpret that: {e}"})
            return

        message = intent.get("message", "").strip() or command
        subject = intent.get("subject", "").strip() or "Message from Kabutar Agent"

        yield _sse("status", {"text": f"Looking up {contact_name}..."})
        resolved = core.resolve_contact(contact_name, platform_key)

        if not resolved:
            yield _sse("failed", {"text": f"No {platform_key} contact saved for {contact_name}."})
            return

        if platform_key == "whatsapp":
            yield _sse("status", {
                "text": "Opening WhatsApp Web -- automation is running live on screen, "
                        "please leave the mouse and keyboard alone until it finishes.",
            })
            result = core.send_whatsapp(resolved, message)
        else:
            yield _sse("status", {"text": f"Sending email to {resolved}..."})
            result = core.send_email(resolved, subject, message)

        ok = core.is_success(result)
        yield _sse("done" if ok else "failed", {"text": result, "message": message})
    except Exception as e:
        # Safety net: anything unanticipated (e.g. a corrupted contacts.json)
        # still ends the stream cleanly instead of raising raw inside a
        # generator Flask is actively streaming to the client.
        yield _sse("failed", {"text": f"Unexpected error: {e}"})


@app.route("/api/send")
def api_send():
    command = request.args.get("command", "")
    platform_key = request.args.get("platform", "whatsapp")
    contact_name = request.args.get("contact", "")

    if not command.strip() or not contact_name.strip():
        return jsonify({"error": "command and contact are required"}), 400

    return Response(
        stream_with_context(_send_stream(command, platform_key, contact_name)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    try:
        print("Opening WhatsApp Web (scan the QR code now if this is the first run)...")
        core.ensure_whatsapp_ready()
        print("WhatsApp Web is ready.")
    except Exception as e:
        print(
            f"WARNING: WhatsApp Web didn't come up cleanly ({e}). "
            "Email will still work; WhatsApp sends will retry the browser on first use."
        )

    # debug=False deliberately: Werkzeug's reloader spawns a second watcher
    # process, and its interactive debugger holds onto request/traceback
    # state across requests -- both are a bad match for a long-running
    # session that's also holding a persistent browser automation open.
    # threaded=True still applies so the SSE connection doesn't block the
    # contact-list requests firing from the same browser tab. Local/single
    # user by design -- do not expose this beyond 127.0.0.1.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)