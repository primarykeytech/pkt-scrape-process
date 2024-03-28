from fixtures import data_table, data_table_with_data
import export.csv_maker as csv_maker


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
