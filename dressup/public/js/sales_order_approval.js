/**
 * Sales Order – Discount Approval buttons
 *
 * Shown only when:
 *   - Current user has the "Discount Approver" role
 *   - Document is submitted (docstatus == 1)
 *   - custom_approval_status is "Pending" or "Under Review"
 *
 * Security note: button visibility is UI-only. Real enforcement lives in
 * the server-side whitelisted methods which re-check the role.
 */

frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		_render_approval_ui(frm);
	},
});

function _render_approval_ui(frm) {
	frm.dashboard.clear_comment();

	const status = frm.doc.custom_approval_status;
	const needs_action =
		frm.doc.docstatus === 1 &&
		(status === "Pending" || status === "Under Review");

	if (!needs_action) return;

	// Check role client-side (cosmetic — server enforces independently)
	if (!frappe.user.has_role("Discount Approver")) return;

	// ── Alert banner showing why approval is needed ──────────────────────
	const reason_html = (frm.doc.custom_approval_reason || "")
		.split("\n")
		.map((l) => `<li>${frappe.utils.escape_html(l)}</li>`)
		.join("");

	frm.dashboard.add_comment(
		`<b>${__("Discount Approval Required")}</b><ul style="margin:4px 0 0 16px">${reason_html}</ul>`,
		"orange",
		true
	);

	// ── Grouped buttons ───────────────────────────────────────────────────
	if (status === "Pending") {
		frm.add_custom_button(
			__("Review"),
			() => _do_review(frm),
			__("Discount Approval")
		);
	}

	frm.add_custom_button(
		__("Approve"),
		() => _do_approve(frm),
		__("Discount Approval")
	);

	frm.add_custom_button(
		__("Reject"),
		() => _do_reject(frm),
		__("Discount Approval")
	);

	// Highlight the Discount Approval group button
	frm.page.btn_primary.removeClass("btn-primary").addClass("btn-default");
	frm.page
		.get_inner_toolbar()
		.find(`[data-label="${encodeURIComponent(__("Discount Approval"))}"]`)
		.removeClass("btn-default")
		.addClass("btn-warning");
}

// ── Action handlers ───────────────────────────────────────────────────────────

function _do_review(frm) {
	frappe.confirm(
		__("Mark this Sales Order as <b>Under Review</b>?"),
		() => {
			frappe.call({
				method: "dressup.dressup.custom_scripts.sales_order.mark_under_review",
				args: { sales_order_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Updating..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Marked as Under Review"), indicator: "blue" });
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function _do_approve(frm) {
	const reason_html = (frm.doc.custom_approval_reason || "")
		.split("\n")
		.map((l) => `<li>${frappe.utils.escape_html(l)}</li>`)
		.join("");

	frappe.confirm(
		`${__("Approve extra discount for this Sales Order?")}<br>
		<ul style="margin:8px 0 0 16px;color:#d97706">${reason_html}</ul>`,
		() => {
			frappe.call({
				method: "dressup.dressup.custom_scripts.sales_order.approve_extra_discount",
				args: { sales_order_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Approving..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Discount Approved"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function _do_reject(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Reject Discount"),
		fields: [
			{
				label: __("Rejection Reason"),
				fieldname: "rejection_reason",
				fieldtype: "Small Text",
				reqd: 1,
				description: __("Mandatory — explain why the discount cannot be approved."),
			},
		],
		primary_action_label: __("Reject"),
		primary_action(values) {
			const reason = (values.rejection_reason || "").trim();

			// Client-side guard
			if (!reason) {
				frappe.msgprint(__("Rejection reason is mandatory."));
				return;
			}

			d.hide();

			frappe.call({
				method: "dressup.dressup.custom_scripts.sales_order.reject_extra_discount",
				args: {
					sales_order_name: frm.doc.name,
					reason: reason,
				},
				freeze: true,
				freeze_message: __("Rejecting..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Discount Rejected"), indicator: "red" });
						frm.reload_doc();
					}
				},
			});
		},
	});

	d.show();
}
