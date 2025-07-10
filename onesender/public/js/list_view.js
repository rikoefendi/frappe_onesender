frappe.provide("frappe.views");

frappe.views.ListView = class extends frappe.views.ListView {
	constructor(opts) {
		super(opts);
	}
	refresh(refresh_header = false) {
		return super.refresh().then(() => {
			this.render_header(refresh_header);
			this.render_count();
			this.update_checkbox();
			this.update_url_with_filters();
			this.setup_realtime_updates();
			this.apply_styles_basedon_dropdown();
		});
	}
	apply_styles_basedon_dropdown() {
		$(".list-row .level-left, .list-row-head .level-left").css({
			flex: "2",
			"min-width": "72%",
		});
	}
	get_meta_html(doc) {
		let html = "";

		let settings_button = null;

		// check if the button property is an array or object
		if (Array.isArray(this.settings.button)) {
			// we have more than one button
			settings_button = "";
			for (const button of this.settings.button) {
				// make sure you have a unique name for each button,
				// otherwise it won't work
				// TODO make sure each name is unique, now it only checks if name exists
				if (!button.name) {
					frappe.throw("Button needs a unique 'name' when using multiple buttons.");
				}

				if (button && button.show(doc)) {
					settings_button += `
                        <span class="list-actions">
                            <button class="btn btn-action btn-default btn-xs"
                                data-name="${doc.name}" data-idx="${doc._idx}" data-action="${
						button.name
					}"
                                title="${button.get_description(doc)}">
                                ${button.get_label(doc)}
                            </button>
                        </span>
                    `;
				}
			}
		} else {
			// business as usual
			if (this.settings.button && this.settings.button.show(doc)) {
				settings_button = `
                    <span class="list-actions">
                        <button class="btn btn-action btn-default btn-xs"
                            data-name="${doc.name}" data-idx="${doc._idx}"
                            title="${this.settings.button.get_description(doc)}">
                            ${this.settings.button.get_label(doc)}
                        </button>
                    </span>
                `;
			}
		}

		const modified = comment_when(doc.modified, true);

		let assigned_to = ``;

		let assigned_users = doc._assign ? JSON.parse(doc._assign) : [];
		if (assigned_users.length) {
			assigned_to = `<div class="list-assignments d-flex align-items-center">
					${frappe.avatar_group(assigned_users, 3, { filterable: true })[0].outerHTML}
				</div>`;
		}

		let comment_count = null;
		if (this.settings && !this.settings.disable_comment_count) {
			comment_count = `<span class="comment-count d-flex align-items-center">
				${frappe.utils.icon("es-line-chat-alt")}
				${doc._comment_count > 99 ? "99+" : doc._comment_count || 0}
			</span>`;
		}

		html += `
			<div class="level-item list-row-activity hidden-xs">
				<div class="hidden-md hidden-xs">
					${settings_button || assigned_to}
				</div>
				<span class="modified">${modified}</span>
				${comment_count || ""}
				${comment_count ? '<span class="mx-2">·</span>' : ""}
				<span class="list-row-like hidden-xs" style="margin-bottom: 1px;">
					${this.get_like_html(doc)}
				</span>
			</div>
			<div class="level-item visible-xs text-right">
				${this.get_indicator_html(doc)}
			</div>
		`;

		return html;
	}

	setup_action_handler() {
		this.$result.on("click", ".btn-action", (e) => {
			const $button = $(e.currentTarget);
			const doc = this.data[$button.attr("data-idx")];

			// get the name of button
			const btnName = $button.attr("data-action");

			// again, check if array
			if (Array.isArray(this.settings.button)) {
				// find the button action
				const button = this.settings.button.find((b) => b.name == btnName);
				button.action(doc);
			} else {
				this.settings.button.action(doc);
			}
			e.stopPropagation();
			return false;
		});
	}
};
