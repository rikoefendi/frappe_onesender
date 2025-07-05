# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt
import frappe.utils
import frappe
import json
from frappe.model.document import Document
from frappe.desk.form.utils import get_pdf_link
from frappe.integrations.utils import make_post_request
from frappe_onesender.utils import get_pdf_link_as_image
class OneSenderMessage(Document):
    """Send OneSender messages."""
    def validate(self):
        """validate attach"""
        if self.attach_with_doctype == 1 and self.content_type not in ["image", "document"]:
            self.content_type = "document"
        if self.content_type == "image" or self.content_type == "document":
            throwMsg = f"Message Type: {str(self.content_type)},"
            if self.attach_with_doctype == 1 and (self.attach_doctype is None or self.attach_docname is None):
                frappe.throw(f"{throwMsg} Attach with DocType, Please Set DocType and DocName")
            elif self.attach_with_doctype != 1 and self.attach is None:
                frappe.throw(f"{throwMsg} Please Attach")
    def after_insert(self):
        """Trigger Send message."""
        self.send_message()
    def send_message(self):
        self.validate()

        # self.bd
        """Build Message"""
        # send text 
        data_text = {
            "to": self.format_number(self.to),
            "type": "text",
            "text": {
                "body": self.message
            }
        }
        data_attach = None
        if self.content_type == "image" or self.content_type == "document":
            data_attach = {
                "to": self.format_number(self.to),
            }
            link = frappe.utils.get_url()
            # generate attach link
            filename = self.name
            caption = filename
            if self.attach is not None:
                link += self.attach
                filename = self.attach.split("/")[-1]
                caption = filename

            if self.attach_with_doctype:
                doctype = frappe.get_doc("DocType", self.attach_doctype)
                doc = frappe.get_doc(self.attach_doctype, self.attach_docname)
                key = doc.get_document_share_key()  # noqa
                frappe.db.commit()
                print_format = "Standard"
                if doctype.custom:
                    if doctype.default_print_format:
                        print_format = doctype.default_print_format
                else:
                    default_print_format = frappe.db.get_value(
                        "Property Setter",
                        filters={
                            "doc_type": doctype.name,
                            "property": "default_print_format"
                        },
                        fieldname="value"
                    )
                    print_format = default_print_format if default_print_format else print_format
                attach_link = ""
                if self.content_type == "document":
                    attach_link = get_pdf_link(
                        doctype.name,
                        doc.name,
                        print_format=print_format,
                    )
                elif self.content_type == "image":
                    attach_link = get_pdf_link_as_image(
                        doctype.name,
                        doc.name,
                        print_format=print_format,
                    )
                link += f"{attach_link}&key={key}"
                filename = self.attach_document_name or doc.name
                caption = filename
            data_attach["type"] = self.content_type
            data_attach[self.content_type] = {
                "link": link,
                "filename": filename,
                "caption": caption
            }
        try:
            self.notify(data_text)
            if data_attach is not None:
                self.notify(data_attach)
                self.status = "Complete"
        except Exception as e:
            self.details = e
            self.status = "Failed"
            self.save()
        finally:
            self.data = json.dumps({
                "text": data_text,
                "attach": data_attach
            })
            self.save()
    def notify(self, data):
        """Notify."""
        dt = "OneSender App"
        os_app = None
        if self.os_app is None:
            os_app = frappe.get_all(dt, filters={"is_default": 1}, fields="*", limit=1)
        else:
            os_app = frappe.get_doc(dt, self.os_app)
        if type(os_app) is list:
            if len(os_app) > 0:
                os_app = os_app[0]
            else:
                os_app = None
        if os_app is None:
            frappe.throw(f"Please set {dt}")
        token = os_app.secret
        headers = {
            "authorization": f"Bearer {token}",
        }
        response = make_post_request(
            url=f"{os_app.url}/api/v1/messages",
            headers=headers,
            data=json.dumps(data)
        )
        if response["code"] != 200:
            frappe.throw(msg=json.dumps(response), title="Send Message Onesender Fail")


    def format_number(self, number):
        """Format number."""
        if number.startswith("+"):
            number = number[1 : len(number)]

        return number
    
    @staticmethod
    def clear_old_logs(days=7):
        from frappe.query_builder import Interval
        from frappe.query_builder.functions import Now

        table = frappe.qb.DocType("OneSender Message")
        frappe.db.delete(table, filters=(table.modified < (Now() - Interval(days=days)) and table.status == "Complete"))

@frappe.whitelist()
def resend_message(docname = ""):
    try:
        frappe.get_doc("OneSender Message", docname).send_message()
        return {
            "message": "Successfully resend message"
        }
    except Exception as e:
        raise e
    