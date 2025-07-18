frappe.listview_settings["Onesender Device"] = {
	add_fields: ["is_online", "is_default"],
	get_indicator(doc) {
		statusText = doc.is_online ? "Online" : "offline";
		statusText += doc.is_default ? " • Default" : "";
		if (doc.is_online) return [__(statusText), "green"];
		if (!doc.is_online) return [__(statusText), "red"];
	},
	hide_name_column: true,
	disable_comment_count: true,
	button: [
		// {
		// 	name: "onesender.api.device_set_default",
		// 	show(doc) {
		// 		return !doc.is_default;
		// 	},
		// 	get_label() {
		// 		return __("Set default");
		// 	},
		// 	get_description(doc) {
		// 		return `Test connection Onesender ${__(doc.name)}`;
		// 	},
		// 	action(doc) {
		// 		return frappe.call({
		// 			method: "onesender.api.device_set_default",
		// 			args: {
		// 				name: doc.name,
		// 			},
		// 			freeze: true,
		// 			callback(r) {
		// 				console.log(frappe);
						
		// 				if (r.message) {
		// 					frappe.msgprint(r.message);
		// 				}
		// 				cur_list.refresh()
		// 			},
		// 		});
		// 	},
		// },
		{
			name: "onesender.api.device_check",
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
				return frappe.call({
					method: "onesender.api.device_check",
					args: {
						name: doc.name,
					},
					freeze: true,
					callback(r) {
						if (r.message) {
							frappe.msgprint(r.message);
						}
						cur_list.refresh()
					},
				});
			},
		},
	],
};
