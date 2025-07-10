# myapp/api.py
import json
import frappe
@frappe.whitelist()
def device_check(name: str):
    doc = frappe.get_doc("Onesender Device", name)
    doc.check()
    # doc.save(doc=doc)
    statusText = "Offline"
    if doc.is_online:
        statusText = "Online"
    return f"Device is {statusText}, Phone {doc.phone} bind"
@frappe.whitelist()
def device_set_default(name: str):
    doc = frappe.get_doc("Onesender Device", name)
    doc.is_default = 1
    doc.save()
    return f"Succes set as default Device: {name}"