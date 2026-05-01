frappe.pages['item-search'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Barcode Item Search',
		single_column: true
	});

	$(wrapper).find('.layout-main-section').addClass('item-search-container');

	wrapper.item_search = new ItemSearch(wrapper);
}

class ItemSearch {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.init();
	}

	init() {
		this.make_ui();
		this.bind_events();
	}

	make_ui() {
		this.wrapper.find('.layout-main-section').empty().append(`
			<div class="search-section text-center py-5">
				<h2 class="mb-4 search-title">Scan Barcode</h2>
				<div class="input-group search-input-group mx-auto">
					<input type="text" class="form-control form-control-lg barcode-input" placeholder="Scan Barcode, Serial, Batch or Item..." autofocus>
					<div class="input-group-append">
						<button class="btn btn-primary btn-lg btn-search" type="button">
							<i class="fa fa-search"></i>
						</button>
					</div>
				</div>
				<p class="mt-3 text-muted search-hint">Scan an item barcode, serial number, or batch to see stock details.</p>
			</div>
			<div class="result-section mt-5" style="display: none;">
				<!-- Item details will be rendered here -->
			</div>
			<div class="empty-state text-center mt-5" style="display: none;">
				<div class="text-muted py-5">
					<i class="fa fa-search fa-4x mb-3"></i>
					<h4>No Item Found</h4>
					<p>We couldn't find an item matching that barcode.</p>
				</div>
			</div>
		`);

		this.$barcode_input = this.wrapper.find('.barcode-input');
		this.$result_section = this.wrapper.find('.result-section');
		this.$empty_state = this.wrapper.find('.empty-state');

		this.add_custom_css();
	}

	bind_events() {
		let me = this;

		this.$barcode_input.on('keypress', function(e) {
			if (e.which === 13) {
				me.search();
			}
		});

		this.wrapper.find('.btn-search').on('click', function() {
			me.search();
		});

		// Auto-focus input on page click (good for physical scanners)
		$(document).on('click', () => {
			if (!$(event.target).is('input, textarea, select')) {
				this.$barcode_input.focus();
			}
		});
	}

	search() {
		let barcode = this.$barcode_input.val().trim();
		if (!barcode) return;

		frappe.dom.freeze(__('Searching...'));
		
		frappe.call({
			method: 'dressup.dressup.page.item_search.item_search.get_item_details',
			args: { barcode: barcode },
			callback: (r) => {
				frappe.dom.unfreeze();
				this.$barcode_input.val('').focus();
				
				if (r.message) {
					this.render_result(r.message);
				} else {
					this.show_empty_state();
				}
			}
		});
	}

	render_result(data) {
		this.$empty_state.hide();
		this.$result_section.empty().show();

		let stock_html = this.build_stock_html(data);
		let reservation_html = this.build_reservation_html(data);

		let html = `
			<div class="card item-card shadow-sm border-0">
				<div class="card-body">
					<div class="row">
						<div class="col-12 col-md-4 text-center item-image-col">
							${data.image ? `
								<img src="${data.image}" class="img-fluid rounded item-image mb-3" style="max-height: 250px;">
							` : `
								<div class="img-placeholder rounded mb-3">
									<i class="fa fa-cube fa-5x text-light"></i>
								</div>
							`}
						</div>
						<div class="col-12 col-md-8 item-details-col">
							<div class="d-flex justify-content-between align-items-start flex-wrap item-header">
								<div class="item-title-block">
									<h3 class="mb-1 item-name-heading">${data.item_name}</h3>
									<p class="text-muted mb-3 item-code-text">${data.item_code}</p>
								</div>
								<span class="badge badge-primary p-2 item-group-badge">${data.item_group}</span>
							</div>
							
							<div class="row mb-4 item-meta-row">
								<div class="col-6 col-sm-4">
									<small class="text-muted d-block">UOM</small>
									<strong>${data.uom}</strong>
								</div>
								${data.brand ? `
									<div class="col-6 col-sm-4">
										<small class="text-muted d-block">Brand</small>
										<strong>${data.brand}</strong>
									</div>
								` : ''}
							</div>

							<div class="description-section">
								<h6>Description</h6>
								<p class="text-muted">${data.description || 'No description available.'}</p>
							</div>
						</div>
					</div>
					
					<hr class="my-4">
					
					${stock_html}

					${reservation_html}
				</div>
			</div>
		`;

		this.$result_section.append(html);
		
		// Scroll to result
		$([document.documentElement, document.body]).animate({
			scrollTop: this.$result_section.offset().top - 100
		}, 500);
	}

	build_stock_html(data) {
		if (!data.stock || data.stock.length === 0) {
			return `
				<div class="alert alert-warning mt-4">
					No stock available in any warehouse.
				</div>
			`;
		}

		let stock_cards_html = data.stock.map(s => `
			<div class="stock-card">
				<div class="stock-card-warehouse">
					<span class="indicator-pill ${s.qty > 0 ? 'green' : 'red'}"></span>
					${s.warehouse}
				</div>
				<div class="stock-card-details">
					<div class="stock-card-detail">
						<small class="text-muted">Available</small>
						<strong>${s.qty} ${data.uom}</strong>
					</div>
					<div class="stock-card-detail">
						<small class="text-muted">Reserved</small>
						<strong>${s.reserved_qty || 0}</strong>
					</div>
					<div class="stock-card-detail">
						<small class="text-muted">Projected</small>
						<strong>${s.projected_qty || 0}</strong>
					</div>
				</div>
			</div>
		`).join('');

		return `
			<div class="stock-section mt-4">
				<h5 class="mb-3">Warehouse Stock</h5>
				<!-- Desktop table view -->
				<div class="stock-table-container d-none d-md-block">
					<table class="table table-hover">
						<thead>
							<tr>
								<th>Warehouse</th>
								<th class="text-right">Available Qty</th>
								<th class="text-right">Reserved</th>
								<th class="text-right">Projected</th>
							</tr>
						</thead>
						<tbody>
							${data.stock.map(s => `
								<tr>
									<td><span class="indicator-pill ${s.qty > 0 ? 'green' : 'red'}"></span> ${s.warehouse}</td>
									<td class="text-right font-weight-bold">${s.qty} ${data.uom}</td>
									<td class="text-right">${s.reserved_qty || 0}</td>
									<td class="text-right">${s.projected_qty || 0}</td>
								</tr>
							`).join('')}
						</tbody>
					</table>
				</div>
				<!-- Mobile card view -->
				<div class="stock-cards-container d-md-none">
					${stock_cards_html}
				</div>
			</div>
		`;
	}

	build_reservation_html(data) {
		if (!data.reservations || data.reservations.length === 0) {
			return '';
		}

		let total_reserved = data.reservations.reduce((sum, r) => sum + (r.remaining_qty || 0), 0);

		// Desktop table
		let table_rows = data.reservations.map(r => `
			<tr>
				<td>
					<a href="/app/${r.reference_type ? r.reference_type.toLowerCase().replace(/ /g, '-') : ''}/${r.reference_name}" class="reservation-link">
						${r.reference_name}
					</a>
				</td>
				<td>${r.customer || '-'}</td>
				<td>${r.reserved_by || '-'}</td>
				<td>${r.warehouse || '-'}</td>
				<td class="text-right">${r.reserved_qty} ${data.uom}</td>
				<td class="text-right">${r.delivered_qty}</td>
				<td class="text-right font-weight-bold">${r.remaining_qty} ${data.uom}</td>
				<td>
					<span class="reservation-status-badge status-${(r.status || '').toLowerCase().replace(/ /g, '-')}">
						${r.status}
					</span>
				</td>
				<td class="text-muted">${r.date || '-'}</td>
			</tr>
		`).join('');

		// Mobile cards
		let mobile_cards = data.reservations.map(r => `
			<div class="reservation-card">
				<div class="reservation-card-header">
					<a href="/app/${r.reference_type ? r.reference_type.toLowerCase().replace(/ /g, '-') : ''}/${r.reference_name}" class="reservation-link">
						${r.reference_name}
					</a>
					<span class="reservation-status-badge status-${(r.status || '').toLowerCase().replace(/ /g, '-')}">
						${r.status}
					</span>
				</div>
				${r.customer ? `<div class="reservation-card-customer"><i class="fa fa-user"></i> ${r.customer}</div>` : ''}
				${r.reserved_by ? `<div class="reservation-card-reservedby"><i class="fa fa-id-badge"></i> Reserved by: <strong>${r.reserved_by}</strong></div>` : ''}
				${r.warehouse ? `<div class="reservation-card-warehouse"><i class="fa fa-warehouse"></i> ${r.warehouse}</div>` : ''}
				<div class="reservation-card-qty-row">
					<div class="reservation-card-qty">
						<small class="text-muted">Ordered</small>
						<strong>${r.reserved_qty} ${data.uom}</strong>
					</div>
					<div class="reservation-card-qty">
						<small class="text-muted">Delivered</small>
						<strong>${r.delivered_qty}</strong>
					</div>
					<div class="reservation-card-qty remaining">
						<small class="text-muted">Pending</small>
						<strong>${r.remaining_qty} ${data.uom}</strong>
					</div>
				</div>
				${r.date ? `<div class="reservation-card-date text-muted"><i class="fa fa-calendar"></i> ${r.date}</div>` : ''}
			</div>
		`).join('');

		return `
			<hr class="my-4">
			<div class="reservation-section mt-4">
				<div class="reservation-header">
					<h5 class="mb-0">
						<i class="fa fa-lock text-warning"></i> Reserved Stock
					</h5>
					<span class="badge badge-warning reservation-total-badge">
						Total Pending: ${total_reserved} ${data.uom}
					</span>
				</div>

				<!-- Desktop table -->
				<div class="reservation-table-container d-none d-md-block mt-3">
					<table class="table table-hover">
						<thead>
							<tr>
								<th>Reference</th>
								<th>Customer</th>
								<th>Reserved By</th>
								<th>Warehouse</th>
								<th class="text-right">Ordered Qty</th>
								<th class="text-right">Delivered</th>
								<th class="text-right">Pending</th>
								<th>Status</th>
								<th>Date</th>
							</tr>
						</thead>
						<tbody>
							${table_rows}
						</tbody>
					</table>
				</div>

				<!-- Mobile cards -->
				<div class="reservation-cards-container d-md-none mt-3">
					${mobile_cards}
				</div>
			</div>
		`;
	}

	show_empty_state() {
		this.$result_section.hide();
		this.$empty_state.show();
	}

	add_custom_css() {
		const css = `
			.item-search-container {
				background-color: #f8f9fa;
				min-height: calc(100vh - 100px);
				padding: 0 15px;
			}

			/* ===== Search Section ===== */
			.search-input-group {
				max-width: 500px;
			}
			.search-input-group .form-control {
				border-radius: 10px 0 0 10px;
				border: 2px solid #e9ecef;
				box-shadow: none;
				transition: border-color 0.2s;
				font-size: 16px;
			}
			.search-input-group .form-control:focus {
				border-color: var(--primary-color);
			}
			.search-input-group .btn {
				border-radius: 0 10px 10px 0;
				padding-left: 25px;
				padding-right: 25px;
				min-width: 50px;
				min-height: 48px;
			}

			/* ===== Item Card ===== */
			.item-card {
				border-radius: 15px;
				overflow: hidden;
			}
			.img-placeholder {
				background: #e9ecef;
				height: 250px;
				display: flex;
				align-items: center;
				justify-content: center;
			}
			.item-image {
				box-shadow: 0 4px 12px rgba(0,0,0,0.1);
				border: 1px solid #eee;
			}
			.item-group-badge {
				white-space: nowrap;
			}

			/* ===== Indicator ===== */
			.indicator-pill {
				height: 10px;
				width: 10px;
				border-radius: 50%;
				display: inline-block;
				margin-right: 8px;
				flex-shrink: 0;
			}
			.indicator-pill.green { background: #28a745; }
			.indicator-pill.red { background: #dc3545; }

			/* ===== Stock Table (Desktop) ===== */
			.stock-table-container {
				background: white;
				padding: 20px;
				border-radius: 10px;
			}

			/* ===== Stock Cards (Mobile) ===== */
			.stock-cards-container {
				display: flex;
				flex-direction: column;
				gap: 10px;
			}
			.stock-card {
				background: white;
				border: 1px solid #e9ecef;
				border-radius: 10px;
				padding: 14px;
			}
			.stock-card-warehouse {
				font-weight: 600;
				font-size: 14px;
				margin-bottom: 10px;
				display: flex;
				align-items: center;
				word-break: break-word;
			}
			.stock-card-details {
				display: flex;
				justify-content: space-between;
				gap: 8px;
			}
			.stock-card-detail {
				display: flex;
				flex-direction: column;
				align-items: center;
				flex: 1;
				text-align: center;
			}
			.stock-card-detail small {
				font-size: 11px;
			}
			.stock-card-detail strong {
				font-size: 14px;
			}

			/* ===== Reservation Section ===== */
			.reservation-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				flex-wrap: wrap;
				gap: 10px;
			}
			.reservation-header h5 i {
				margin-right: 6px;
			}
			.reservation-total-badge {
				font-size: 13px;
				padding: 6px 12px;
			}
			.reservation-table-container {
				background: white;
				padding: 20px;
				border-radius: 10px;
			}
			.reservation-link {
				font-weight: 600;
				color: var(--primary-color, #5e64ff);
				text-decoration: none;
			}
			.reservation-link:hover {
				text-decoration: underline;
			}

			/* Status badges */
			.reservation-status-badge {
				display: inline-block;
				padding: 3px 10px;
				border-radius: 20px;
				font-size: 11px;
				font-weight: 600;
				white-space: nowrap;
			}
			.reservation-status-badge.status-reserved,
			.reservation-status-badge.status-partially-reserved {
				background: #fff3cd;
				color: #856404;
			}
			.reservation-status-badge.status-partially-delivered {
				background: #d4edda;
				color: #155724;
			}
			.reservation-status-badge.status-pending-delivery {
				background: #cce5ff;
				color: #004085;
			}

			/* ===== Reservation Cards (Mobile) ===== */
			.reservation-cards-container {
				display: flex;
				flex-direction: column;
				gap: 12px;
			}
			.reservation-card {
				background: white;
				border: 1px solid #e9ecef;
				border-radius: 10px;
				padding: 14px;
			}
			.reservation-card-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 8px;
				flex-wrap: wrap;
				gap: 6px;
			}
			.reservation-card-customer,
			.reservation-card-reservedby,
			.reservation-card-warehouse {
				font-size: 13px;
				color: #555;
				margin-bottom: 4px;
			}
			.reservation-card-customer i,
			.reservation-card-reservedby i,
			.reservation-card-warehouse i,
			.reservation-card-date i {
				width: 16px;
				margin-right: 6px;
				color: #999;
			}
			.reservation-card-qty-row {
				display: flex;
				justify-content: space-between;
				gap: 8px;
				margin-top: 10px;
				padding-top: 10px;
				border-top: 1px solid #f0f0f0;
			}
			.reservation-card-qty {
				display: flex;
				flex-direction: column;
				align-items: center;
				flex: 1;
				text-align: center;
			}
			.reservation-card-qty small {
				font-size: 11px;
			}
			.reservation-card-qty strong {
				font-size: 14px;
			}
			.reservation-card-qty.remaining strong {
				color: #e67e22;
			}
			.reservation-card-date {
				font-size: 12px;
				margin-top: 8px;
			}

			/* ===== Mobile Responsive ===== */
			@media (max-width: 767.98px) {
				.item-search-container {
					padding: 0 10px;
				}
				.search-section {
					padding-top: 24px !important;
					padding-bottom: 24px !important;
				}
				.search-title {
					font-size: 22px;
				}
				.search-hint {
					font-size: 13px;
				}
				.search-input-group {
					max-width: 100%;
				}
				.search-input-group .form-control {
					font-size: 16px;
					padding: 10px 14px;
					height: auto;
				}
				.search-input-group .btn {
					padding-left: 16px;
					padding-right: 16px;
				}

				/* Item card mobile tweaks */
				.item-card .card-body {
					padding: 16px;
				}
				.item-image-col {
					margin-bottom: 16px;
				}
				.img-placeholder {
					height: 180px;
				}
				.item-image {
					max-height: 200px !important;
				}
				.item-name-heading {
					font-size: 20px;
				}
				.item-code-text {
					font-size: 13px;
				}
				.item-header {
					gap: 8px;
				}
				.item-group-badge {
					font-size: 12px;
				}
				.item-meta-row {
					margin-bottom: 12px !important;
				}
				.result-section {
					margin-top: 20px !important;
				}

				/* Empty state mobile */
				.empty-state .fa-4x {
					font-size: 2.5em !important;
				}
			}

			/* ===== Very small screens (< 400px) ===== */
			@media (max-width: 400px) {
				.search-title {
					font-size: 18px;
				}
				.stock-card-details,
				.reservation-card-qty-row {
					flex-wrap: wrap;
				}
				.stock-card-detail,
				.reservation-card-qty {
					min-width: 70px;
				}
			}
		`;
		frappe.dom.set_style(css, 'item-search-css');
	}
}
