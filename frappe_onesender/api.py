# # myapp/api.py
# import frappe
# import os
# from frappe import _
# import frappe.utils
# import frappe.utils.response
# from werkzeug.exceptions import Forbidden, NotFound
# from frappe.core.doctype.file.utils import find_file_by_url
# from frappe.core.doctype.access_log.access_log import make_access_log

# @frappe.whitelist(allow_guest=True)
# def get_private_file(file_url: str, token: str):
#     """Checks permissions and sends back private file"""
#     expected_token = frappe.cache().get_value(f"access_token::{file_url}")
#     if token != expected_token:
#         raise Forbidden(_("You don't have permission to access this file"))
    
#     # file = find_file_by_url(file_url, name=frappe.form_dict.fid)
#     # if not file:
#     #     raise Forbidden(_("You don't have permission to access this file"))
    
#     make_access_log(doctype="File", file_type=os.path.splitext(file_url)[-1][1:])
#     return frappe.utils.response.send_private_file(file_url.split("/private", 1)[1])
#     # with open(file_path, "rb") as f:
#     #     content = f.read()

#     # frappe.local.response.filename = file_url.split("/")[-1]
#     # frappe.local.response.filecontent = content
#     # frappe.response
#     # frappe.local.response.headers.add("Content-Disposition", "attachment", filename=file_url.split("/")[-1])


