ENDPOINTS = {
    "products": {"path": "products", "mode": "full", "extra": {"activeProducts": "false"}},
    "tables": {"path": "tables", "mode": "full"},
    "shiftstatus": {"path": "shiftstatus", "mode": "full"},
    "sales": {"path": "sales", "mode": "range", "window_days": 15, "params": ("ini", "end")},
    "salesbywaiter": {"path": "salesbywaiter", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date")},
    "collection": {"path": "collection", "mode": "daily", "params": ("date",)},
    "fiscaldocuments": {"path": "fiscaldocuments", "mode": "range", "window_days": 15, "params": ("ini", "end"), "extra": {"document_type": "all"}},
    "inventorystate": {"path": "inventorystate", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date")},
    "accountingmovements": {"path": "accountingmovements", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date"), "extra": {"include_sales": "true"}},
    "orders_cancellation_report": {"path": "orders/cancellation-report", "mode": "range", "window_days": 15, "params": ("start_date", "end_date"), "date_format": "%Y-%m-%d"},
}
