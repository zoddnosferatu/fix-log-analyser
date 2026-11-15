
# fix log analyser

a small python tool for reading simulated fix-style logs and
exporting message details and exceptions to csv.

## what it does

• parses tag-value messages separated by pipes or soh characters.
• extracts order ids, symbols, execution types, and order statuses.
• checks sequence numbers separately for each sender/target pair.
• flags missing sequences, low-sequence records, and malformed input.
• extracts rejected-order execution reports.

## run

requires python 3. no external packages are needed.
python parser.py sample_logs.txt
the script creates two files:
• reports/messages.csv
• reports/exceptions.csv

## sample data

the input contains simulated heartbeats, a new order,
an acknowledgement, partial and full fills, and a rejected order.
it also includes:
• a missing sequence number.
• a repeated rejection report.
• a non-numeric sequence number.
the original sample produces 9 parsed messages and 5 exception
records. the repeated rejection is counted twice because the
script reports individual records rather than unique orders.

## limitations

this is an offline learning project, not a fix engine.
the sample messages are simplified log excerpts, not complete
wire-valid fix messages. the parser does not validate bodylength
or checksum, process repeating groups, handle session recovery,
or reconstruct order state.
sequence checks assume one continuous session capture, with
sender and target identifying each direction. the first observed
message establishes the baseline.
a sequence gap means records are missing from the observed log.
it does not establish whether the cause was a logging issue,
an incomplete capture, or something else.

## possible improvements

• add automated tests.
• validate numeric order fields.
• deduplicate execution reports.
• support more complete session identification.
• add bodylength and checksum validation.
