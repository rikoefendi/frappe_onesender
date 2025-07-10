frappe.listview_settings["Onesender Device"] = {
	add_fields: ["test", "is_default"],
	get_indicator(doc) {
		statusText = doc.status;
		statusText += doc.is_default ? " • Default" : "";
		if (doc.status == "Online") return [__(statusText), "green"];
		if (doc.status == "Offline") return [__(statusText), "red"];
	},
	hide_name_column: true,
	disable_comment_count: true,
	button: [
		{
			name: 'onesender.device.default',
			show(doc) {
				return !doc.is_default;
			},
			get_label() {
				return __("Set default");
			},
			get_description(doc) {
				return `Test connection Onesender ${__(doc.name)}`;
			},
			action(doc) {
				return frappe.call("onesender.api.device.set_default", {
					name: doc.name,
				});
			},
		},
		{
			name: 'onesender.device.test',
			show(doc) {
				return true;
			},
			get_label() {
				return __("Test");
			},
			get_description(doc) {
				return `Test connection Onesender ${__(doc.name)}`;
			},
			action(doc) {
				return frappe.call("onesender.api.device.test_connection", {
					name: doc.name,
				});
			},
		},
	],
};
