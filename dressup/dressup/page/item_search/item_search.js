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
				<h2 class="mb-4">Scan Barcode</h2>
				<div class="input-group search-input-group mx-auto" style="max-width: 500px;">
					<input type="text" class="form-control form-control-lg barcode-input" placeholder="Scan or type barcode..." autofocus>
					<div class="input-group-append">
						<button class="btn btn-primary btn-lg btn-search" type="button">
							<i class="fa fa-search"></i>
						</button>
					</div>
				</div>
				<p class="mt-3 text-muted">Scan an item barcode to see stock availability and details.</p>
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

		let stock_html = '';
		if (data.stock && data.stock.length > 0) {
			stock_html = `
				<div class="stock-table-container mt-4">
					<h5 class="mb-3">Warehouse Stock</h5>
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
			`;
		} else {
			stock_html = `
				<div class="alert alert-warning mt-4">
					No stock available in any warehouse.
				</div>
			`;
		}

		let html = `
			<div class="card item-card shadow-sm border-0">
				<div class="card-body">
					<div class="row">
						<div class="col-md-4 text-center">
							${data.image ? `
								<img src="${data.image}" class="img-fluid rounded item-image mb-3" style="max-height: 250px;">
							` : `
								<div class="img-placeholder rounded mb-3">
									<i class="fa fa-cube fa-5x text-light"></i>
								</div>
							`}
						</div>
						<div class="col-md-8">
							<div class="d-flex justify-content-between align-items-start">
								<div>
									<h3 class="mb-1">${data.item_name}</h3>
									<p class="text-muted mb-3">${data.item_code}</p>
								</div>
								<span class="badge badge-primary p-2">${data.item_group}</span>
							</div>
							
							<div class="row mb-4">
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
				</div>
			</div>
		`;

		this.$result_section.append(html);
		
		// Scroll to result
		$([document.documentElement, document.body]).animate({
			scrollTop: this.$result_section.offset().top - 100
		}, 500);
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
			}
			.search-input-group .form-control {
				border-radius: 10px 0 0 10px;
				border: 2px solid #e9ecef;
				box-shadow: none;
				transition: border-color 0.2s;
			}
			.search-input-group .form-control:focus {
				border-color: var(--primary-color);
			}
			.search-input-group .btn {
				border-radius: 0 10px 10px 0;
				padding-left: 25px;
				padding-right: 25px;
			}
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
			.indicator-pill {
				height: 10px;
				width: 10px;
				border-radius: 50%;
				display: inline-block;
				margin-right: 8px;
			}
			.indicator-pill.green { background: #28a745; }
			.indicator-pill.red { background: #dc3545; }
			
			.stock-table-container {
				background: white;
				padding: 20px;
				border-radius: 10px;
			}
			
			.item-image {
				box-shadow: 0 4px 12px rgba(0,0,0,0.1);
				border: 1px solid #eee;
			}
		`;
		frappe.dom.set_style(css, 'item-search-css');
	}
}
