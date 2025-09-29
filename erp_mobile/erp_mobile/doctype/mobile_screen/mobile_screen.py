# Copyright (c) 2025, Mantra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MobileScreen(Document):

	def validate(self):
		#To check if display title is blank then set it from title
		if not self.display_title:
			self.display_title= self.title