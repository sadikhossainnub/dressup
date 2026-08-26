/**
 * Purchase Order – Dynamic Role-Based Approval Buttons & Button Guard
 *
 * Flow:
 * 1. If PO is submitted (docstatus == 1) and custom_po_approval_status is not "Approved" (Pending or Rejected):
 *    - Suppress/clear ALL standard buttons (Create, Update Items, etc.) for ALL users.
 * 2. If status is "Pending":
 *    - Check current user roles against configured roles from DressUp Settings -> PO Approval Roles.
 *    - If authorized, show "Approve" and "Reject" buttons under "PO Approval".
 * 3. If status is "Approved":
 *    - Standard ERPNext buttons (Create -> Purchase Receipt/Invoice, etc.) appear as normal.
 */

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		_render_po_approval_ui(frm);
	},
});

function _render_po_approval_ui(frm) {
	frm.dashboard.clear_comment();

	const status = frm.doc.custom_po_approval_status;

	// Show status banner for everyone (submitted docs only)
	if (frm.doc.docstatus === 1 && status) {
		_render_status_banner(frm, status);
	}

	// Guard: Suppress ALL action buttons for ALL users if doc is submitted and NOT Approved
	if (frm.doc.docstatus === 1 && status !== "Approved") {
		frm.clear_custom_buttons();
		frm.page.clear_inner_toolbar();
	}

	// Only check for approval buttons if doc is submitted and status is Pending
	if (frm.doc.docstatus !== 1 || status !== "Pending") {
		return;
	}

	// Fetch allowed PO approver roles dynamically from DressUp Settings
	frappe.call({
		method: "dressup.dressup.custom_scripts.purchase_order.get_po_approver_roles",
		callback(r) {
			const allowed_roles = r.message || ["PO Approver"];
			const can_approve = allowed_roles.some((role) => frappe.user.has_role(role));

			if (!can_approve) {
				return;
			}

			// Clear custom buttons again before adding approval options to prevent duplicates
			frm.clear_custom_buttons();
			frm.page.clear_inner_toolbar();

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
}

function _render_status_banner(frm, status) {
	const status_map = {
		"Pending": { color: "orange", icon: "⏳", label: __("Approval Pending") },
		"Approved": { color: "green", icon: "✅", label: __("Approved") },
		"Rejected": { color: "red", icon: "❌", label: __("Rejected") },
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
		primary_action_label: __("Reject"),
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
				freeze_message: __("Rejecting..."),
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Purchase Order Rejected"), indicator: "red" });
						frm.reload_doc();
					}
				},
			});
		},
	});

	d.show();
}
