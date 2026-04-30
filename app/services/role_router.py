# app/services/role_router.py
# Single responsibility: given a role string, open the correct dashboard window.
# The login UI calls only this function — it never imports dashboards directly.
# This breaks the potential circular import chain completely.

from PyQt5.QtWidgets import QMessageBox


# Map each role to a lazy import path.
# Lazy imports (inside the function) mean dashboard modules are only loaded
# AFTER QApplication exists — prevents "QWidget before QApplication" errors.
_ROLE_DASHBOARD_MAP = {
    "farmer":   ("app.ui.farmer_dashboard",   "FarmerDashboard"),
    "customer": ("app.ui.customer_dashboard", "CustomerDashboard"),
    "agent":    ("app.ui.agent_dashboard",    "AgentDashboard"),
    "investor": ("app.ui.investor_dashboard", "InvestorDashboard"),
}


def open_dashboard_for_role(role: str, parent=None) -> object | None:
    """
    Instantiate and return the correct dashboard window for the given role.

    Args:
        role:   The role string from session (e.g. 'farmer').
        parent: The calling window — will be closed after dashboard opens.

    Returns:
        The opened dashboard window instance, or None on failure.
    """
    entry = _ROLE_DASHBOARD_MAP.get(role)

    if entry is None:
        QMessageBox.critical(
            parent, "Unknown Role",
            f"No dashboard is registered for role: '{role}'.\n"
            "Please contact your system administrator."
        )
        return None

    module_path, class_name = entry

    try:
        import importlib
        module = importlib.import_module(module_path)
        DashboardClass = getattr(module, class_name)
        dashboard = DashboardClass()
        dashboard.show()

        if parent:
            parent.close()

        return dashboard

    except ImportError as exc:
        QMessageBox.critical(
            parent, "Dashboard Not Found",
            f"Could not load dashboard for role '{role}'.\n\nDetail: {exc}"
        )
        return None
    except Exception as exc:
        QMessageBox.critical(
            parent, "Dashboard Error",
            f"An error occurred opening the dashboard.\n\nDetail: {exc}"
        )
        return None
