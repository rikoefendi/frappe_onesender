"""Run on each event."""
import frappe
from frappe.core.doctype.server_script.server_script_utils import EVENT_MAP
from croniter import croniter
from datetime import datetime
from datetime import datetime, time
from croniter import croniter
 
from typing import Literal

def build_header(secret: str):
    return {
        "authorization": f"Bearer {secret}"
    }

def run_server_script_for_doc_event(doc, event):
    """Run on each event."""
    if event not in EVENT_MAP:
        return

    if frappe.flags.in_install:
        return

    if frappe.flags.in_migrate:
        return
    
    if frappe.flags.in_uninstall:
        return

    notification = get_notifications_map().get(
        doc.doctype, {}
    ).get(EVENT_MAP[event], None)
    if notification:
        # run all scripts for this doctype + event
        for notification_name in notification:
            frappe.get_doc(
                "Onesender Notification",
                notification_name
            ).notify_event(doc)


def get_notifications_map():
    """Get mapping."""
    if frappe.flags.in_patch and not frappe.db.table_exists("Onesender Notification"):
        return {}

    notification_map = {}
    enabled_onesender_notifications = frappe.get_all(
        "Onesender Notification",
        fields=("name", "reference_doctype", "doctype_event", "notification_type"),
        filters={"disabled": 0},
    )
    for notification in enabled_onesender_notifications:
        if notification.notification_type == "DocType Event":
            notification_map.setdefault(
                notification.reference_doctype, {}
            ).setdefault(
                notification.doctype_event, []
            ).append(notification.name)

    frappe.cache().set_value("onesender_notification_map", notification_map)

    return notification_map

def trigger_device_connection_check():
    devices = frappe.get_all("Onesender Device")
    for device in devices:
        frappe.get_doc("Onesender Device", device.name).check()


from croniter import croniter
from datetime import datetime, time
import frappe

def get_cron_expression_from_notification(doc):
    run_time = frappe.utils.get_time(doc.run_time) if doc.run_time else time(0, 0)
    minute = run_time.minute
    hour = run_time.hour

    freq = doc.event_frequency
    unit = doc.interval_unit or ""
    every = doc.interval_every or 1

    if freq == "Cron" and doc.cron_expression:
        return doc.cron_expression.strip()

    if freq == "Once":
        return None

    if freq == "At Regular Intervals":
        if unit == "Minutes":
            return f"*/{every} * * * *"
        elif unit == "Hours":
            return f"{minute} */{every} * * *"
        elif unit == "Days":
            return f"{minute} {hour} */{every} * *"
        elif unit == "Weeks":
            return f"{minute} {hour} * * */{every}"

    if freq == "Every Day":
        return f"{minute} {hour} * * *"

    if freq == "Days Of The Week" and doc.weekday_days:
        days = ",".join(d.strip() for d in doc.weekday_days.split(",") if d.strip().isdigit())
        return f"{minute} {hour} * * {days}"

    if freq == "Dates Of The Month" and doc.monthday_days:
        days = ",".join(d.strip() for d in doc.monthday_days.split(",") if d.strip().isdigit())
        return f"{minute} {hour} {days} * *"

    return None

def trigger_onesender_notifications_cron(run_now=False):
    now = datetime.now()

    notification_list = frappe.get_all("Onesender Notification",
        filters={"disabled": 0, "notification_type": "Scheduler Event"},
        fields=["name", "event_frequency", "cron_expression", "last_run_at"])

    for job in notification_list:
        doc = frappe.get_doc("Onesender Notification", job.name)
        cron_expr = get_cron_expression_from_notification(doc)
        print(cron_expr)
        if not cron_expr:
            continue

        last_run = doc.last_run_at or now.replace(year=now.year - 1)
        cron = croniter(cron_expr, last_run)
        next_time = cron.get_next(datetime)

        if next_time <= now or run_now:
            doc.db_set("last_run_at", now)
            doc.db_set("next_run_at", next_time)
            doc.notify_scheduled()
def get_attach_doctype_link(doctype, docname, print_format="", no_letterhead=0, filename = None, attach_type: Literal["pdf", "image"] = "pdf"):
    return frappe.utils.quote_urls(f"/api/method/onesender.attach_doctype.download_{attach_type}?doctype={doctype}&name={docname}&format={print_format}&no_letterhead={no_letterhead}&filename={filename or ""}")






