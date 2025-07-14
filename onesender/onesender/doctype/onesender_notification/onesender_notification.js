// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt
frappe.notification = {
	setup_fieldname_select: (frm) => {
		// get the doctype to update fields
		if (!frm.doc.reference_doctype) {
			return;
		}

		frappe.model.with_doctype(frm.doc.reference_doctype, () => {
			let get_select_options = (df, parent_field) => {
				// Append parent_field name along with fieldname for child table fields
				let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
				let path = parent_field ? parent_field + " > " + df.fieldname : df.fieldname;

				return {
					value: select_value,
					label: path + " (" + __(df.label, null, df.parent) + ")",
				};
			};

			let get_date_change_options = () => {
				let date_options = $.map(fields, (d) => {
					return d.fieldtype == "Date" || d.fieldtype == "Datetime"
						? get_select_options(d)
						: null;
				});
				// append creation and modified date to Date Change field
				return date_options.concat([
					{ value: "creation", label: `creation (${__("Created On")})` },
					{ value: "modified", label: `modified (${__("Last Modified Date")})` },
				]);
			};

			let fields = frappe.get_doc("DocType", frm.doc.reference_doctype).fields;
			let options = $.map(fields, (d) => {
				return frappe.model.no_value_type.includes(d.fieldtype)
					? null
					: get_select_options(d);
			});

			// set date changed options
			frm.set_df_property("reference_date", "options", get_date_change_options());

			// set value changed options
			frm.set_df_property("value_changed", "options", [""].concat(options));
			frm.set_df_property("set_property_after_alert", "options", [""].concat(options));
		});
	},
	setup_alerts_button: (frm) => {
		// body...
		if (frm.is_new() || !frm.doc.reference_doctype) return;
		frm.add_custom_button(__("Get Alerts for Today"), () => {
			frappe.call({
				method: "onesender.api.get_alert_today",
				callback: (response) => {
					console.log(response.message);
					
					if (response.message && response.message.length > 0) {
						frappe.msgprint(response.message);
					} else {
						frappe.msgprint(__("No alerts for today"));
					}
				},
				error: (error) => {
					frappe.msgprint(__("Failed to trigger notifications"));
				},
			});
		});
	},
	test_notification: (frm) => {
		if(frm.is_new() || frm.doc.notification_type != "Scheduler Event") return
		frm.add_custom_button(__("Test"), () => {
			frappe.call({
				method: "onesender.api.test_notification",
				args: {
					name: frm.doc.name,
				},
				callback() {
					frappe.msgprint("Sucess run Notification")
				},
			});
		});
	},
};

frappe.ui.form.on("Onesender Notification", {
	refresh: (frm) => {
		frappe.notification.setup_fieldname_select(frm);
		frappe.notification.setup_alerts_button(frm);
		frappe.notification.test_notification(frm)
	},
	template: (frm) => {},
	reference_doctype: (frm) => {
		frappe.notification.setup_fieldname_select(frm);
	},
});
