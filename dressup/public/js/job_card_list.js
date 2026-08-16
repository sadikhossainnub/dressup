/**
 * dressup/public/js/job_card_list.js
 *
 * Adds a "Bulk Start Job" action to the Job Card List View.
 * Uses the server-side method: dressup.dressup.api.job_card.bulk_start_job_cards
 */

frappe.listview_settings["Job Card"] = frappe.listview_settings["Job Card"] || {};

// Preserve any existing onload hook
const _existing_job_card_onload = frappe.listview_settings["Job Card"].onload;

frappe.listview_settings["Job Card"].onload = function (listview) {
	// Call any previously registered onload first
	if (_existing_job_card_onload) {
		_existing_job_card_onload.call(this, listview);
	}

	listview.page.add_action_item(__("Bulk Start Job"), function () {
		const selected = listview.get_checked_items();

		if (!selected || selected.length === 0) {
			frappe.msgprint({
				title: __("No Selection"),
				message: __("Please select at least one Job Card to start."),
				indicator: "orange",
			});
			return;
		}

		const names = selected.map((row) => row.name);
		const count = names.length;

		frappe.confirm(
			__(
				"Are you sure you want to <strong>Start</strong> {0} selected Job Card(s)?",
				[count]
			),
			function () {
				// ── Confirmed ──────────────────────────────────────────────
				frappe.dom.freeze(__("Starting Job Cards…"));

				frappe.call({
					method:
						"dressup.dressup.api.job_card.bulk_start_job_cards",
					args: { job_cards: names },
					callback: function (response) {
						frappe.dom.unfreeze();

						const result = response.message || {};
						const started = (result.started || []).length;
						const skipped = result.skipped || [];
						const failed = result.failed || [];

						// ── Build a human-readable summary ─────────────────
						let lines = [];

						if (started) {
							lines.push(
								`<p style="color:green;">✅ <strong>${started}</strong> ${__("Job Card(s) started successfully.")}</p>`
							);
						}

						if (skipped.length) {
							const skip_rows = skipped
								.map(
									(s) =>
										`<li><strong>${frappe.utils.escape_html(s.name)}</strong> — ${frappe.utils.escape_html(s.reason)}</li>`
								)
								.join("");
							lines.push(
								`<p style="color:orange;">⏭ <strong>${skipped.length}</strong> ${__("skipped")}:</p><ul>${skip_rows}</ul>`
							);
						}

						if (failed.length) {
							const fail_rows = failed
								.map(
									(f) =>
										`<li><strong>${frappe.utils.escape_html(f.name)}</strong> — ${frappe.utils.escape_html(f.error)}</li>`
								)
								.join("");
							lines.push(
								`<p style="color:red;">❌ <strong>${failed.length}</strong> ${__("failed")}:</p><ul>${fail_rows}</ul>`
							);
						}

						if (!lines.length) {
							lines.push(`<p>${__("No Job Cards were processed.")}</p>`);
						}

						frappe.msgprint({
							title: __("Bulk Start Result"),
							message: lines.join(""),
							indicator: failed.length ? "red" : started ? "green" : "orange",
						});

						// Refresh the list to reflect updated statuses
						listview.refresh();
					},
					error: function () {
						frappe.dom.unfreeze();
						frappe.msgprint({
							title: __("Error"),
							message: __(
								"An unexpected error occurred while starting Job Cards. Please check the Error Log."
							),
							indicator: "red",
						});
					},
				});
			}
		);
	});
};
