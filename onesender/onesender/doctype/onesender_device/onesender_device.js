// Copyright (c) 2025, MKB and contributors
// For license information, please see license.txt

frappe.ui.form.on("Onesender Device", {
    refresh(frm){
        frm.trigger("render_buttons");
    },
	render_buttons(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Set as Default"), function () {
				frappe.call({
					method: "onesender.api.device_set_default",
					args: {
						name: frm.doc.name,
					},
				});
			});
		}
	},
});
