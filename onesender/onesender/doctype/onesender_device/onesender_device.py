# Copyright (c) 2025, MKB and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from onesender.utils import build_header
from frappe.integrations.utils import make_get_request
class OnesenderDevice(Document):
	"""Onesender App Connection"""
	def validate(self):
		"""Validate only 1 default"""
		if self.is_default:
			frappe.db.set_value(self.doctype, {'is_default': 1}, 'is_default', 0)
	def before_save(self):
		old = self.get_doc_before_save()
		if(self.secret != old.secret or self.url != old.url):
			self.check(False)
	def check(self, is_check = True):
		headers = build_header(self.secret)
		res = make_get_request(f"{self.url}/api/feeds", headers=headers)
		if not isinstance(res, dict):
			raise frappe.throw(title="Device Connection Error", msg=res)
		res_data = res["data"]
		
		self.is_online = res_data["status"] == "online"
		self.phone = res_data["phone"]
		if is_check:
			self.save()