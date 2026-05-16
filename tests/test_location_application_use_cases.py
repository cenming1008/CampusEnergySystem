import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application import locations


class TestLocationApplicationUseCases(unittest.TestCase):
    def test_list_locations_use_case_filters_by_user_scope(self):
        session = object()
        current_user = SimpleNamespace(role="viewer", location_scope="1")
        service_rows = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        scoped_rows = [service_rows[0]]

        with patch.object(locations.LocationService, "get_all_locations", return_value=service_rows) as mock_service:
            with patch.object(locations, "filter_locations_by_scope", return_value=scoped_rows) as mock_filter:
                result = locations.list_locations_use_case(
                    session=session,
                    current_user=current_user,
                    location_type="area",
                    parent_id=3,
                    is_active=True,
                )

        self.assertIs(result, scoped_rows)
        mock_service.assert_called_once_with(
            session=session,
            location_type="area",
            parent_id=3,
            is_active=True,
        )
        mock_filter.assert_called_once_with(service_rows, current_user)

    def test_tree_use_case_checks_root_access_and_filters_tree_scope(self):
        session = object()
        current_user = SimpleNamespace(role="viewer", location_scope="1")
        service_tree = [{"id": 1, "children": [{"id": 2}]}]
        scoped_tree = [{"id": 1, "children": []}]

        with patch.object(locations, "ensure_location_access") as mock_access:
            with patch.object(locations.LocationService, "get_location_tree", return_value=service_tree) as mock_service:
                with patch.object(
                    locations,
                    "filter_location_tree_by_scope",
                    return_value=scoped_tree,
                ) as mock_filter:
                    result = locations.get_location_tree_use_case(
                        session=session,
                        current_user=current_user,
                        root_id=1,
                        max_depth=2,
                    )

        self.assertIs(result, scoped_tree)
        mock_access.assert_called_once_with(session, current_user, 1)
        mock_service.assert_called_once_with(session=session, root_location_id=1, max_depth=2)
        mock_filter.assert_called_once_with(service_tree, current_user)

    def test_create_location_use_case_audits_created_location(self):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        created = SimpleNamespace(id=8)

        with patch.object(locations.LocationService, "create_location", return_value=created) as mock_service:
            with patch.object(locations, "audit_log") as mock_audit:
                result = locations.create_location_use_case(
                    session=session,
                    current_user=current_user,
                    name="北区",
                    location_type="area",
                    parent_id=1,
                    code="NORTH",
                    description="desc",
                    area_sqm=1200.0,
                    manager="alice",
                    contact="123",
                )

        self.assertIs(result, created)
        mock_service.assert_called_once_with(
            session=session,
            name="北区",
            location_type="area",
            parent_id=1,
            code="NORTH",
            description="desc",
            area_sqm=1200.0,
            manager="alice",
            contact="123",
        )
        mock_audit.assert_called_once_with(
            "location.create",
            "admin",
            "location:8",
            role="admin",
        )

    def test_statistics_use_case_checks_access_then_calls_service(self):
        session = object()
        current_user = SimpleNamespace(role="viewer", location_scope="5")
        stats = {"device_count": {"total": 3}}

        with patch.object(locations, "ensure_location_access") as mock_access:
            with patch.object(locations.LocationService, "get_location_statistics", return_value=stats) as mock_service:
                result = locations.get_location_statistics_use_case(
                    session=session,
                    current_user=current_user,
                    location_id=5,
                    recursive=False,
                )

        self.assertIs(result, stats)
        mock_access.assert_called_once_with(session, current_user, 5)
        mock_service.assert_called_once_with(session=session, location_id=5, recursive=False)


if __name__ == "__main__":
    unittest.main()
