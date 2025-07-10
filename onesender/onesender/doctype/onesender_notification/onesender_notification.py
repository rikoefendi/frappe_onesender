"""Notification."""

import frappe

from frappe.model.document import Document
from frappe.utils.safe_exec import get_safe_globals, safe_exec
from frappe.utils.jinja import render_template
class OnesenderNotification(Document):
    """Notification."""

    def validate(self):
        """Validate."""
        if self.notification_type == "DocType Event":
            fields = frappe.get_doc("DocType", self.reference_doctype).fields
            if not any(field.fieldname == self.field_name for field in fields): # noqa
                frappe.throw(_("Field name {0} does not exists").format(self.field_name))


    def notify_scheduled(self) -> dict:
        """Specific to API endpoint Server Scripts."""
        if not self.condition:
            return
        safe_exec(
            self.condition, get_safe_globals(), dict(doc=self)
        )
        data_list = self.get("_data_list") or []
        for dl in data_list:
            doc = frappe.get_doc(self.reference_doctype, dl.get("name"))
            self.notify_event(doc, ignore_condition=True)
        return dict(doc=self)


    def notify_event(self, doc: Document, phone_no=None, ignore_condition=False):
        """Specific to Document Event triggered Server Scripts."""
        if self.disabled:
            return

        doc_data = doc.as_dict()
        if self.condition and not ignore_condition:
            # check if condition satisfies
            if not frappe.safe_eval(
                self.condition, get_safe_globals(), dict(doc=doc_data)
            ):
                return

        if self.field_name:
            phone_number = phone_no or doc_data[self.field_name]
        else:
            phone_number = phone_no
        rendered_message = render_template(self.message, {"doc": doc})
        content_type = "text"
        if self.attach_document_print == 1:
            content_type = "document"
            if self.attach_document_print_as_image == 1:
                content_type = "image"
        frappe.get_doc({
            "doctype": "Onesender Message",
            "to": self.format_number(phone_number),
            "os_app": self.os_app,
            "message": rendered_message,
            "content_type": content_type,
            "attach_with_doctype": 1,
            "attach_doctype": doc.doctype,
            "attach_docname": doc.name,
            "attach_document_name": render_template(self.attach_document_name, {"doc": doc}),
            "onesender_notification": self.name
        }).insert(ignore_permissions=True)

    def format_number(self, number):
        """Format number."""
        if (number.startswith("+")):
            number = number[1:len(number)]

        return number
    