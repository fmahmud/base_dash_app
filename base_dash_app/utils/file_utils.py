import csv
import io
from typing import List, Dict, Any


def convert_data_to_csv_file(data_to_write):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in data_to_write:
        writer.writerow(row)

    return output.getvalue()


def convert_dict_to_csv(data_to_write: List, keys: List[str], headers_override: Dict[str, Any] = None):
    output = io.StringIO()
    writer = csv.DictWriter(output, keys)

    if headers_override is not None:
        writer.writerow(headers_override)
    else:
        writer.writeheader()

    for row in data_to_write:
        writer.writerow(row)

    return output.getvalue()
