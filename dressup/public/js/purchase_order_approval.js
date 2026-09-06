/**
 * Purchase Order – Dynamic Role-Based Approval Buttons & Button Guard
 *
 * Flow:
 * 1. If PO is submitted (docstatus == 1) and custom_po_approval_status is not "Approved" (Pending or Rejected):
 *    - Suppress/clear ALL standard buttons (Create, Update Items, Status, Cancel) for ALL users.
 * 2. If status is "Pending":
 *    - Check current user roles against configured roles from DressUp Settings -> PO Approval Roles.
 *    - If authorized, show "Approve" and "Reject" buttons under "PO Approval".
 * 3. On Reject:
 *    - Rejection sets status to "Rejected" and cancels the document (docstatus = 2).
 * 4. If status is "Approved":
 *    - Standard ERPNext buttons (Create -> Purchase Receipt/Invoice, etc.) appear as normal.
 */

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		_render_po_approval_ui(frm);
	},
	onload_post_render(frm) {
		_render_po_approval_ui(frm);
	},
});

function _render_po_approval_ui(frm) {
	frm.dashboard.clear_comment();

	const status = frm.doc.custom_po_approval_status;

	// Show status banner for everyone (submitted or cancelled docs with status)
	if (status && (frm.doc.docstatus === 1 || frm.doc.docstatus === 2)) {
		_render_status_banner(frm, status);
	}

	// Guard: Suppress ALL action buttons for ALL users if doc is submitted and NOT Approved
	if (frm.doc.docstatus === 1 && status !== "Approved") {
		_clear_all_toolbar_buttons(frm);
	} else {
		return;
	}

	// Fetch allowed PO approver roles dynamically from DressUp Settings
	frappe.call({
		method: "dressup.dressup.custom_scripts.purchase_order.get_po_approver_roles",
		callback(r) {
			const allowed_roles = r.message || ["PO Approver"];
			const can_approve = allowed_roles.some((role) => frappe.user.has_role(role));

			// Re-clear standard buttons in case ERPNext standard JS rendered them asynchronously
			_clear_all_toolbar_buttons(frm);

			if (!can_approve || frm.doc.docstatus !== 1 || status !== "Pending") {
				return;
			}

			// Add Approve button
			frm.add_custom_button(
				__("Approve"),
				() => _do_approve(frm),
				__("PO Approval")
			);

			// Add Reject button
			frm.add_custom_button(
				__("Reject"),
				() => _do_reject(frm),
				__("PO Approval")
			);

			// Style the PO Approval group button
			frm.page.btn_primary.removeClass("btn-primary").addClass("btn-default");
			frm.page
				.get_inner_toolbar()
				.find(`[data-label="${encodeURIComponent(__("PO Approval"))}"]`)
				.removeClass("btn-default")
				.addClass("btn-warning");
		},
	});

	// Multi-stage deferred cleanup to purge standard buttons added late by ERPNext/Frappe layout
	[50, 150, 400, 800].forEach((delay) => {
		setTimeout(() => {
			if (frm.doc.docstatus === 1 && frm.doc.custom_po_approval_status !== "Approved") {
				_filter_buttons_for_pending_po(frm);
			}
		}, delay);
	});
}

function _clear_all_toolbar_buttons(frm) {
	frm.custom_make_buttons = {};
	frm.clear_custom_buttons();
	frm.page.clear_inner_toolbar();
	frm.page.clear_user_actions();

	if (frm.page.btn_secondary) {
		frm.page.btn_secondary.addClass("hide").hide();
	}
}

function _filter_buttons_for_pending_po(frm) {
	// Prevent Frappe from generating the "Create" button dropdown
	frm.custom_make_buttons = {};

	// Remove standard custom buttons added by ERPNext (Create, Status, Update Items, etc.)
	const inner_toolbar = frm.page.get_inner_toolbar();
	if (inner_toolbar) {
		inner_toolbar.find(".btn-group, .btn").each(function () {
			const $btn = $(this);
			const label = ($btn.attr("data-label") || $btn.text() || "").trim();

			if (label !== __("PO Approval") && !$btn.parents(`[data-label="${encodeURIComponent(__("PO Approval"))}"]`).length) {
				$btn.remove();
			}
		});
	}

	// Remove standard page action buttons (e.g. Cancel button / Update Items)
	if (frm.page.btn_secondary) {
		const sec_label = (frm.page.btn_secondary.text() || "").trim();
		if (sec_label === __("Cancel") || sec_label === __("Update Items") || sec_label === "") {
			frm.page.btn_secondary.addClass("hide").hide();
		}
	}

	// Extra cleanup: hide any secondary buttons in wrapper page-actions area
	if (frm.page.wrapper) {
		frm.page.wrapper.find(".page-actions .btn-secondary, .page-actions .btn-default").each(function () {
			const $btn = $(this);
			const txt = ($btn.text() || "").trim();
			if (txt === __("Cancel") || txt === __("Update Items")) {
				$btn.addClass("hide").hide();
			}
		});
	}
}

function _render_status_banner(frm, status) {
	const status_map = {
		"Pending": { color: "orange", icon: "⏳", label: __("Approval Pending") },
		"Approved": { color: "green", icon: "✅", label: __("Approved") },
		"Rejected": { color: "red", icon: "❌", label: __("Rejected & Cancelled") },
	};

	const s = status_map[status];
	if (!s) return;

	let msg = `<b>${s.icon} ${s.label}</b>`;

	if (status === "Approved" && frm.doc.custom_po_approved_by) {
		msg += ` — ${__("By")}: <b>${frappe.utils.escape_html(frm.doc.custom_po_approved_by)}</b>`;
	}

	if (status === "Rejected") {
		if (frm.doc.custom_po_approved_by) {
			msg += ` — ${__("By")}: <b>${frappe.utils.escape_html(frm.doc.custom_po_approved_by)}</b>`;
		}
		if (frm.doc.custom_po_rejection_reason) {
			msg += `<br><b>${__("Reason")}:</b> ${frappe.utils.escape_html(frm.doc.custom_po_rejection_reason)}`;
		}
	}

	frm.dashboard.add_comment(msg, s.color, true);
}

// ── Action handlers ────────────────────────────────────────────────────────

function _do_approve(frm) {
	frappe.confirm(
		__(
			"Are you sure you want to <b>Approve</b> this Purchase Order?<br><br>"
			+ "<b>Supplier:</b> {0}<br><b>Grand Total:</b> {1} {2}",
			[
				frappe.utils.escape_html(frm.doc.supplier),
				frm.doc.currency || "BDT",
				format_currency(frm.doc.grand_total, frm.doc.currency),
			]
		),
		() => {
			frappe.call({
				method: "dressup.dressup.custom_scripts.purchase_order.approve_purchase_order",
				args: { po_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Approving..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Purchase Order Approved"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function _do_reject(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Reject Purchase Order"),
		fields: [
			{
				label: __("Rejection Reason"),
				fieldname: "rejection_reason",
				fieldtype: "Small Text",
				reqd: 1,
				description: __("Mandatory — explain why this Purchase Order cannot be approved."),
			},
		],
		primary_action_label: __("Reject & Cancel PO"),
		primary_action(values) {
			const reason = (values.rejection_reason || "").trim();

			if (!reason) {
				frappe.msgprint(__("Rejection reason is mandatory."));
				return;
			}

			d.hide();

			frappe.call({
				method: "dressup.dressup.custom_scripts.purchase_order.reject_purchase_order",
				args: {
					po_name: frm.doc.name,
					reason: reason,
				},
				freeze: true,
				freeze_message: __("Rejecting and Cancelling PO..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Purchase Order Rejected & Cancelled"), indicator: "red" });
						frm.reload_doc();
					}
				},
			});
		},
	});

	d.show();
}
