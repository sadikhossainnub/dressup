/**
 * dressup/public/js/job_card_list.js
 *
 * Adds "Bulk Start Job" and "Bulk Complete Job" actions to the Job Card List View.
 *
 * Visibility rule (client-side filter before API call):
 *   - Bulk Start Job    → only "Open" cards
 *   - Bulk Complete Job → only "Work In Progress" cards
 *                         + optional sub-operation selection dialog
 *
 * Server methods: dressup.dressup.api.job_card.*
 */

frappe.listview_settings["Job Card"] = frappe.listview_settings["Job Card"] || {};

// Ensure status is fetched so get_checked_items() has it available
frappe.listview_settings["Job Card"].add_fields = (
	frappe.listview_settings["Job Card"].add_fields || []
).concat(["status"]);

// Preserve any existing onload hook
const _existing_job_card_onload = frappe.listview_settings["Job Card"].onload;

frappe.listview_settings["Job Card"].onload = function (listview) {
	if (_existing_job_card_onload) {
		_existing_job_card_onload.call(this, listview);
	}

	// ── Helpers ─────────────────────────────────────────────────────────────

	function build_summary(result_rows) {
		const rows = result_rows
			.map(
				(r) =>
					`<li><strong>${frappe.utils.escape_html(r.name)}</strong> — ${frappe.utils.escape_html(r.reason || r.error || "")}</li>`
			)
			.join("");
		return `<ul>${rows}</ul>`;
	}

	function show_result(title, count_label, count, skipped, failed) {
		let lines = [];
		if (count) {
			lines.push(
				`<p style="color:green;">✅ <strong>${count}</strong> ${count_label}</p>`
			);
		}
		if (skipped.length) {
			lines.push(
				`<p style="color:orange;">⏭ <strong>${skipped.length}</strong> ${__("skipped")}:</p>${build_summary(skipped)}`
			);
		}
		if (failed.length) {
			lines.push(
				`<p style="color:red;">❌ <strong>${failed.length}</strong> ${__("failed")}:</p>${build_summary(failed)}`
			);
		}
		if (!lines.length) {
			lines.push(`<p>${__("No Job Cards were processed.")}</p>`);
		}
		frappe.msgprint({
			title: __(title),
			message: lines.join(""),
			indicator: failed.length ? "red" : count ? "green" : "orange",
		});
	}

	function do_complete(names, sub_operation) {
		frappe.dom.freeze(__("Completing Job Cards…"));
		frappe.call({
			method: "dressup.dressup.api.job_card.bulk_complete_job_cards",
			args: { job_cards: names, sub_operation: sub_operation || null },
			callback: function (response) {
				frappe.dom.unfreeze();
				const result = response.message || {};
				show_result(
					"Bulk Complete Result",
					__("Job Card(s) completed successfully."),
					(result.completed || []).length,
					result.skipped || [],
					result.failed || []
				);
				listview.refresh();
			},
			error: function () {
				frappe.dom.unfreeze();
				frappe.msgprint({
					title: __("Error"),
					message: __(
						"An unexpected error occurred while completing Job Cards. Please check the Error Log."
					),
					indicator: "red",
				});
			},
		});
	}

	// ════════════════════════════════════════════════════════════════════════
	// Bulk Start Job  —  only for status = "Open"
	// ════════════════════════════════════════════════════════════════════════
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

		const eligible = selected.filter((row) => row.status === "Open");
		const ineligible = selected.filter((row) => row.status !== "Open");

		if (eligible.length === 0) {
			frappe.msgprint({
				title: __("Nothing to Start"),
				message: __(
					"None of the selected Job Cards have status <strong>Open</strong>. Only Open cards can be started."
				),
				indicator: "orange",
			});
			return;
		}

		const names = eligible.map((row) => row.name);
		let confirm_msg = __(
			"Are you sure you want to <strong>Start</strong> {0} Job Card(s) with status <em>Open</em>?",
			[names.length]
		);
		if (ineligible.length) {
			confirm_msg += `<br><span style="color:orange;">${__("{0} selected card(s) will be skipped (not Open).", [ineligible.length])}</span>`;
		}

		frappe.confirm(confirm_msg, function () {
			frappe.dom.freeze(__("Starting Job Cards…"));
			frappe.call({
				method: "dressup.dressup.api.job_card.bulk_start_job_cards",
				args: { job_cards: names },
				callback: function (response) {
					frappe.dom.unfreeze();
					const result = response.message || {};
					show_result(
						"Bulk Start Result",
						__("Job Card(s) started successfully."),
						(result.started || []).length,
						result.skipped || [],
						result.failed || []
					);
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
		});
	});

	// ════════════════════════════════════════════════════════════════════════
	// Bulk Complete Job  —  only for status = "Work In Progress"
	//                        + optional sub-operation selector
	// ════════════════════════════════════════════════════════════════════════
	listview.page.add_action_item(__("Bulk Complete Job"), function () {
		const selected = listview.get_checked_items();

		if (!selected || selected.length === 0) {
			frappe.msgprint({
				title: __("No Selection"),
				message: __("Please select at least one Job Card to complete."),
				indicator: "orange",
			});
			return;
		}

		const eligible = selected.filter(
			(row) => row.status === "Work In Progress"
		);
		const ineligible = selected.filter(
			(row) => row.status !== "Work In Progress"
		);

		if (eligible.length === 0) {
			frappe.msgprint({
				title: __("Nothing to Complete"),
				message: __(
					"None of the selected Job Cards have status <strong>Work In Progress</strong>."
				),
				indicator: "orange",
			});
			return;
		}

		const names = eligible.map((row) => row.name);

		// ── Step 1: Fetch sub-operations from server ─────────────────────────
		frappe.dom.freeze(__("Checking sub-operations…"));

		frappe.call({
			method:
				"dressup.dressup.api.job_card.get_sub_operations_for_job_cards",
			args: { job_cards: names },
			callback: function (r) {
				frappe.dom.unfreeze();

				const sub_ops = r.message || []; // [{value, label}, ...]

				// ── Step 2: Show dialog ──────────────────────────────────────
				const has_sub_ops = sub_ops.length > 0;

				const fields = [];

				// Info row
				let info_html = `<p>${__(
					"<strong>{0}</strong> Job Card(s) will be marked as completed.",
					[names.length]
				)}`;
				if (ineligible.length) {
					info_html += `<br><span style="color:orange;">${__("{0} card(s) skipped (not Work In Progress).", [ineligible.length])}</span>`;
				}
				info_html += `</p>`;

				fields.push({
					fieldtype: "HTML",
					options: info_html,
				});

				if (has_sub_ops) {
					// Sub-operation select
					const options_list = [
						{ value: "", label: __("— Complete entire Job Card —") },
						...sub_ops,
					];

					fields.push({
						fieldtype: "Select",
						fieldname: "sub_operation",
						label: __("Sub Operation"),
						options: options_list
							.map((o) => o.value)
							.join("\n"),
						description: __(
							"Select a sub-operation to mark only that step as complete, or leave blank to complete the entire Job Card."
						),
					});
				} else {
					fields.push({
						fieldtype: "HTML",
						options: `<p style="color:#888;">${__("No pending sub-operations found. The entire Job Card will be completed.")}</p>`,
					});
				}

				const dialog = new frappe.ui.Dialog({
					title: __("Bulk Complete Job"),
					fields: fields,
					primary_action_label: __("Complete"),
					primary_action: function (values) {
						dialog.hide();

						const sub_op = has_sub_ops
							? (values.sub_operation || "").trim()
							: "";

						do_complete(names, sub_op || null);
					},
				});

				dialog.show();
			},
			error: function () {
				frappe.dom.unfreeze();
				// If the sub-op fetch fails, fall back to direct complete
				frappe.msgprint({
					title: __("Warning"),
					message: __(
						"Could not fetch sub-operation list. Proceeding to complete entire Job Card(s)."
					),
					indicator: "orange",
				});
				do_complete(names, null);
			},
		});
	});
};
