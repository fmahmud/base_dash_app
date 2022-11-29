import csv
import io


def convert_data_to_csv_file(data_to_write):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in data_to_write:
        writer.writerow(row)

    return output.getvalue()


def convert_dict_to_csv(data_to_write, keys):
    output = io.StringIO()
    writer = csv.DictWriter(output, keys)
    writer.writeheader()
    for row in data_to_write:
        writer.writerow(row)

    return output.getvalue()
