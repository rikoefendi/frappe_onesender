# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt
import frappe.utils
import frappe
import json
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request
from onesender.utils import get_attach_doctype_link
from frappe.utils import get_request_session

class OnesenderMessage(Document):
    """Send Onesender messages."""
    def validate(self):
        """validate attach"""
        if self.attach_with_doctype == 1 and self.content_type not in ["Image", "Document"]:
            self.content_type = "Document"
        if self.content_type == "Image" or self.content_type == "Document":
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
        if self.content_type == "Image" or self.content_type == "Document":
            data_attach = {
                "to": self.format_number(self.to),
            }
            # generate attach link
            filename = self.name

            if self.attach_with_doctype:
                doctype = frappe.get_doc("DocType", self.attach_doctype)
                doc = frappe.get_doc(self.attach_doctype, self.attach_docname)
                key = doc.get_document_share_key()  # noqa
                frappe.db.commit()


                attach_type = "pdf"
                if self.content_type == "Image":
                    attach_type = "image"
                
                attach_link = get_attach_doctype_link(
                        doctype.name,
                        doc.name,
                        filename=filename,
                        attach_type=attach_type
                    )
                
                filename = self.attach_document_name or doc.name
                link = frappe.utils.get_url(uri=f"{attach_link}&key={key}", full_address=False)
                caption = self.caption or filename
                data_attach["type"] = self.content_type.lower()
                data_attach[self.content_type.lower()] = {
                    "link": link,
                    "filename": filename,
                    "caption": caption
                }
        try:
            self.notify(data_text)
            if data_attach is not None:
                self.notify(data_attach)
            self.status = "Complete"
            self.details = ""
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
        dt = "Onesender Device"
        device = None
        if self.device is None:
            device = frappe.get_all(dt, filters={"is_default": 1}, fields="*", limit=1)
        else:
            device = frappe.get_doc(dt, self.device)
        if type(device) is list:
            if len(device) > 0:
                device = device[0]
            else:
                device = None
        if device is None:
            frappe.throw(f"Please set {dt}")
        token = device.secret
        headers = {
            "authorization": f"Bearer {token}",
        }
        response = make_post_request(
            url=f"{device.url}/api/v1/messages",
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

        table = frappe.qb.DocType("Onesender Message")
        frappe.db.delete(table, filters=(table.modified < (Now() - Interval(days=days)) and table.status == "Complete"))

@frappe.whitelist()
def resend_message(docname = ""):
    try:
        frappe.get_doc("Onesender Message", docname).send_message()
        return {
            "message": "Successfully resend message"
        }
    except Exception as e:
        raise e
    