import boto3
import pandas as pd
import cfg


# Function to scan DynamoDB table and collect items
def scan_table(table_name):
    """
    Scan the table and collect all items.
    :param table_name: dynamodb table name
    :return: array of items
    """
    # Create a DynamoDB client and use the paginator to scan the table
    dynamodb = boto3.client("dynamodb")
    paginator = dynamodb.get_paginator('scan')

    # array to hold all items
    db_items = []

    # Loop through each page and collect items
    for page in paginator.paginate(TableName=table_name):
        db_items.extend(page['Items'])

    # return the items found.
    return db_items


def build_exported_csv(items):
    """
    Build the exported csv file.
    :param items: Items from dynamodb.
    :return: Boolean just to indicate success.
    """
    # Get attribute names (headers for CSV)
    attribute_names = list(items[0].keys())

    # Data that will be added to the dataframe
    data = []

    # Loop through each item and extract values
    for item in items:

        # Extract item values based on attribute names
        data_row = [item.get(attr) for attr in attribute_names]

        # List for the cleaned data
        cleaned_row = []

        # Loop through the values in the row. All the values
        # from dynamodb should have the 'S' key.
        for value in data_row:
            if 'S' in value:
                cleaned_row.append(value['S'].replace('\n', ''))

        # Append the cleaned row to the list
        data.append(cleaned_row)

    # Create pandas DataFrame and save to CSV
    df = pd.DataFrame(data, columns=attribute_names)

    # Save the dataframe to a csv file with the name set in the cfg file.
    df.to_csv(cfg.EXPORT_FILE, index=False)

    # return success
    return True


def main():
    """
    Run the scan of the dynamodb table and build the exported csv file.
    """
    # Scan the table and get items
    items = scan_table(cfg.DB_TABLE)

    # Check if any items retrieved
    if not items:
        print("No items found in the table")
        exit()

    # Build the exported csv file.
    if build_exported_csv(items):
        print(f"Exported data to: {cfg.EXPORT_FILE}")
    else:
        print(f"Export of data failed.")


if __name__ == '__main__':
    main()
