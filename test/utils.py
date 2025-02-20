from subprocess import Popen, PIPE
import csv
import sys
from io import StringIO

CsvData = list[list[str]]


def xzar(args: list[str], data: CsvData) -> CsvData:
    input_data = StringIO()
    writer = csv.writer(input_data)

    for row in data:
        writer.writerow(row)

    process = Popen(
        [sys.executable, "-m", "xzar"] + args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )

    stdout, stderr = process.communicate(input_data.getvalue())

    if process.returncode != 0:
        raise AssertionError(stderr)

    output_data = StringIO()
    output_data.write(stdout)
    output_data.seek(0)

    return list(csv.reader(output_data))
