// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt
frappe.notification = {
	setup_fieldname_select: function (frm) {
		// get the doctype to update fields
		if (!frm.doc.reference_doctype) {
			return;
		}

		frappe.model.with_doctype(frm.doc.reference_doctype, function () {
			let get_select_options = function (df, parent_field) {
				// Append parent_field name along with fieldname for child table fields
				let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
				let path = parent_field ? parent_field + " > " + df.fieldname : df.fieldname;

				return {
					value: select_value,
					label: path + " (" + __(df.label, null, df.parent) + ")",
				};
			};

			let get_date_change_options = function () {
				let date_options = $.map(fields, function (d) {
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
			let options = $.map(fields, function (d) {
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
	setup_alerts_button: function (frm) {
		// body...
        if(frm.is_new) return;
		frm.add_custom_button(__('Get Alerts for Today'), function () {
            frappe.call({
                method: 'onesender.onesender.doctype.onesender_notification.onesender_notification.call_trigger_notifications',
                args: {
                    method: 'daily' 
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                    } else {
                        frappe.msgprint(__('No alerts for today'));
                    }
                },
                error: function (error) {
                    frappe.msgprint(__('Failed to trigger notifications'));
                }
            });
        });
	}
};


frappe.ui.form.on('Onesender Notification', {
	refresh: function(frm) {
		frappe.notification.setup_fieldname_select(frm);
		frappe.notification.setup_alerts_button(frm);
	},
	template: function(frm){
	},
	reference_doctype: function (frm) {
		frappe.notification.setup_fieldname_select(frm);
	},
});
