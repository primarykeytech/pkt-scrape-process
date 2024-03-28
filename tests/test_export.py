import unittest.mock as mock
import unittest
import pandas as pd
from fixtures import data_table, data_table_with_data
import export.csv_maker as csv_maker
import cfg


def test_scan_table(data_table, data_table_with_data):
    """
    Test the scan_table function.
    :param data_table: Fixture to create a mock table.
    :param data_table_with_data: Fixture to add data to the mock table.
    """

    # Scan the mock table and get the items.
    items = csv_maker.scan_table("mock_table")

    # Assert that there were two items found.
    assert len(items) == 2


def test_build_exported_csv(data_table, data_table_with_data, mocker):
    """
    Test the build_exported_csv function.
    :param data_table: Fixture to create a mock table.
    :param data_table_with_data: Fixture to add data to the mock table.
    """

    # Scan the mock table and get the items.
    items = csv_maker.scan_table("mock_table")

    # Mock the to_csv function from pandas and test that the to_csv function is called.
    with mock.patch("pandas.DataFrame.to_csv") as to_csv_mock:
        csv_maker.build_exported_csv(items)
        to_csv_mock.assert_called_with(cfg.EXPORT_FILE, index=False)
