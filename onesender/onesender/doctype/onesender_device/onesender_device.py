# Copyright (c) 2025, MKB and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OnesenderDevice(Document):
	"""OneSender App Connection"""
	def validate(doc):
		"""Validate only 1 default"""
		if doc.is_default:
			frappe.db.set_value(doc.doctype, {'is_default': 1}, 'is_default', 0)