import argparse
import csv
from pathlib import Path

MESSAGE_TYPES = {
    "0": "Heartbeat",
    "3": "SessionReject",
    "4": "SequenceReset",
    "8": "ExecutionReport",
    "D": "NewOrderSingle",
}

ORDER_STATUSES = {
    "0": "New",
    "1": "PartiallyFilled",
    "2": "Filled",
    "4": "Canceled",
    "8": "Rejected",
}

EXEC_TYPES = {
    "0": "New",
    "4": "Canceled",
    "8": "Rejected",
    "F": "Trade",
}

MESSAGE_COLUMNS = [
    "line", "sender", "target", "sequence", "message_type",
    "client_order_id", "order_id", "symbol", "order_status",
    "execution_type", "order_qty", "cum_qty", "leaves_qty", "text",
]

EXCEPTION_COLUMNS = [
    "line", "category", "sender", "target", "sequence",
    "client_order_id", "details",
]


def parse_message(raw):
    text = raw.strip()
    if not text or text.startswith("#"):
        return None

    fields = {}
    for item in text.replace("\x01", "|").strip("|").split("|"):
        if not item or "=" not in item:
            raise ValueError(f"Malformed field: {item!r}")

        tag, value = item.split("=", 1)

        if not tag.isdigit() or not value:
            raise ValueError(f"Invalid tag/value: {item!r}")
        if tag in fields:
            raise ValueError(
                f"Repeated tag {tag}: repeating groups are unsupported"
            )

        fields[tag] = value

    for tag in ("8", "35", "34", "49", "56"):
        if tag not in fields:
            raise ValueError(f"Missing required project field: {tag}")

    if fields["8"] != "FIX.4.4":
        raise ValueError("This project supports FIX.4.4 samples only")

    try:
        sequence = int(fields["34"])
    except ValueError:
        raise ValueError("MsgSeqNum(34) must be an integer")

    if sequence < 1:
        raise ValueError("MsgSeqNum(34) must be positive")

    return fields


def analyse(lines):
    expected = {}
    messages = []
    exceptions = []

    def flag(line_number, category, fields, details):
        exceptions.append({
            "line": line_number,
            "category": category,
            "sender": fields.get("49", ""),
            "target": fields.get("56", ""),
            "sequence": fields.get("34", ""),
            "client_order_id": fields.get("11", ""),
            "details": details,
        })

    for line_number, raw in enumerate(lines, 1):
        try:
            fields = parse_message(raw)
        except ValueError as error:
            flag(line_number, "PARSE_ERROR", {}, str(error))
            continue

        if fields is None:
            continue

        sender = fields["49"]
        target = fields["56"]
        sequence = int(fields["34"])
        msg_type = fields["35"]
        stream = (sender, target)

        # The first observed message establishes a capture baseline.
        if stream in expected:
            next_number = expected[stream]

            if sequence > next_number:
                flag(
                    line_number,
                    "SEQUENCE_GAP",
                    fields,
                    f"Expected {next_number}; observed {sequence}. "
                    f"Missing in capture: {next_number}-{sequence - 1}.",
                )
            elif sequence < next_number:
                flag(
                    line_number,
                    "LOW_SEQUENCE",
                    fields,
                    f"Expected at least {next_number}; observed {sequence}. "
                    f"Possible duplicate, replay, or out-of-order record; "
                    f"PossDupFlag={fields.get('43', 'not supplied')}.",
                )

        expected[stream] = max(expected.get(stream, sequence), sequence + 1)

        if msg_type == "4":
            flag(
                line_number,
                "UNSUPPORTED_SEQUENCE_RESET",
                fields,
                "Sequence-reset processing is not implemented. "
                "Subsequent sequence alerts may be misleading.",
            )

        if msg_type == "8":
            if "150" not in fields or "39" not in fields:
                flag(
                    line_number,
                    "MISSING_EXECUTION_FIELDS",
                    fields,
                    "Execution report lacks ExecType(150) or OrdStatus(39).",
                )

            if fields.get("150") == "8":
                flag(
                    line_number,
                    "ORDER_REJECTION",
                    fields,
                    fields.get("58", "No rejection text supplied"),
                )

        messages.append({
            "line": line_number,
            "sender": sender,
            "target": target,
            "sequence": sequence,
            "message_type": MESSAGE_TYPES.get(msg_type, msg_type),
            "client_order_id": fields.get("11", ""),
            "order_id": fields.get("37", ""),
            "symbol": fields.get("55", ""),
            "order_status": ORDER_STATUSES.get(
                fields.get("39"), fields.get("39", "")
            ),
            "execution_type": EXEC_TYPES.get(
                fields.get("150"), fields.get("150", "")
            ),
            "order_qty": fields.get("38", ""),
            "cum_qty": fields.get("14", ""),
            "leaves_qty": fields.get("151", ""),
            "text": fields.get("58", ""),
        })

    return messages, exceptions


def write_csv(destination, rows, columns):
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Analyse simplified FIX.4.4 log samples."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()

    try:
        with args.input_file.open(encoding="utf-8") as file:
            messages, exceptions = analyse(file)
    except OSError as error:
        parser.exit(1, f"Cannot read input: {error}\n")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        args.output_dir / "messages.csv",
        messages,
        MESSAGE_COLUMNS,
    )
    write_csv(
        args.output_dir / "exceptions.csv",
        exceptions,
        EXCEPTION_COLUMNS,
    )

    print(f"Parsed messages: {len(messages)}")
    print(f"Exception records: {len(exceptions)}")

    for item in exceptions:
        print(
            f"Line {item['line']} | {item['category']} | "
            f"{item['details']}"
        )


if __name__ == "__main__":
    main()