ENDPOINTS = {
    "sales": {"path": "sales", "mode": "range", "window_days": 15, "params": ("ini", "end"), "priority": 10},
    "salesbywaiter": {"path": "salesbywaiter", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date"), "priority": 20},
    "products": {"path": "products", "mode": "full", "extra": {"activeProducts": "false"}, "priority": 30},
    "tables": {"path": "tables", "mode": "full", "priority": 40},
    "shiftstatus": {"path": "shiftstatus", "mode": "full", "priority": 50},
    "fiscaldocuments": {"path": "fiscaldocuments", "mode": "range", "window_days": 15, "params": ("ini", "end"), "extra": {"document_type": "all"}, "priority": 60},
    "inventorystate": {"path": "inventorystate", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date"), "priority": 70},
    "accountingmovements": {"path": "accountingmovements", "mode": "range", "window_days": 15, "params": ("initial_date", "final_date"), "extra": {"include_sales": "true"}, "priority": 80},
    "orders_cancellation_report": {"path": "orders/cancellation-report", "mode": "range", "window_days": 15, "params": ("start_date", "end_date"), "date_format": "%Y-%m-%d", "priority": 90},
    "collection": {"path": "collection", "mode": "daily", "params": ("date",), "priority": 100},
}
