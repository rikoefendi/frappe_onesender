"""Run on each event."""
import frappe
from PIL import Image
import pdf2image
from frappe.core.doctype.server_script.server_script_utils import EVENT_MAP
from croniter import croniter
from datetime import datetime
from typing import Literal
from frappe.www.printview import validate_print_permission
from frappe.translate import print_language
import io
from werkzeug.wrappers import Response
from datetime import datetime, timedelta, time
from croniter import croniter
from frappe.utils import now_datetime, get_datetime, get_time
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
                "OneSender Notification",
                notification_name
            ).notify_event(doc)


def get_notifications_map():
    """Get mapping."""
    if frappe.flags.in_patch and not frappe.db.table_exists("OneSender Notification"):
        return {}

    notification_map = {}
    enabled_onesender_notifications = frappe.get_all(
        "OneSender Notification",
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

    notification_list = frappe.get_all("OneSender Notification",
        filters={"disabled": 0, "notification_type": "Scheduler Event"},
        fields=["name", "event_frequency", "cron_expression", "last_run_at"])

    for job in notification_list:
        doc = frappe.get_doc("OneSender Notification", job.name)
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

def get_pdf_link_as_image(doctype, docname, print_format="Standard", no_letterhead=0):
    return f"/api/method/frappe_onesender.utils.download_document_print_as_image?doctype={doctype}&name={docname}&format={print_format}&no_letterhead={no_letterhead}"


@frappe.whitelist(allow_guest=True)
def download_document_print_as_image(
	doctype: str,
	name: str,
	format=None,
	doc=None,
	no_letterhead=0,
	language=None,
	letterhead=None,
	pdf_generator: Literal["wkhtmltopdf", "chrome"] | None = None,
):
	doc = doc or frappe.get_doc(doctype, name)
	validate_print_permission(doc)

	with print_language(language):
		pdf_file = frappe.get_print(
			doctype,
			name,
			format,
			doc=doc,
			as_pdf=True,
			letterhead=letterhead,
			no_letterhead=no_letterhead,
			pdf_generator=pdf_generator,
		)

	# Convert all pages to image (list of PIL Images)
	pages = pdf2image.convert_from_bytes(pdf_file, dpi=150)

	if not pages:
		frappe.throw("PDF conversion returned no pages")

	# Get combined image dimensions (vertical stacking)
	width = pages[0].width
	total_height = sum(page.height for page in pages)

	# Create new blank image
	combined = Image.new("RGB", (width, total_height), color=(255, 255, 255))

	# Paste all pages vertically
	y_offset = 0
	for page in pages:
		combined.paste(page, (0, y_offset))
		y_offset += page.height

	# Save to bytes
	raw = io.BytesIO()
	combined.save(raw, format="JPEG")
	raw.seek(0)

	# Create response
	filename = f"{name.replace(' ', '-').replace('/', '-')}.jpeg"
	response = Response()
	response.headers.add("Content-Disposition", "inline", filename=filename)
	response.data = raw.getvalue()
	response.mimetype = "image/jpeg"
	return response