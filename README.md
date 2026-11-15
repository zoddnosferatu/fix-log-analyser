an educational python tool for analysing simulated FIX.4.4-style
log excerpts and producing structured CSV reports.

## Features

- Parses tag-value records using pipe or SOH delimiters.
- Maps selected message types, execution types, and order statuses.
- Tracks observed sequence numbers separately by sender and target.
- Flags sequence gaps and low-sequence records.
- Extracts order-rejection reports.
- Exports message and exception CSV files.

## Run

python parser.py sample_logs.txt

## Outputs

- reports/messages.csv
- reports/exceptions.csv

## Assumptions and limitations

- All input is synthetic.
- Samples are simplified log excerpts, not wire-valid FIX messages.
- One continuous session capture is assumed.
- The first observed sequence establishes the baseline per direction.
- Session identity is simplified to sender and target.
- No BodyLength or CheckSum validation.
- No session establishment, retransmission, or sequence-reset handling.
- No repeating-group support.
- No complete FIX dictionary validation.
- No persistent order-state reconstruction.
- No deduplication of execution reports.
- No broker, exchange, or live trading connectivity.

A sequence gap means records are absent from the observed stream.
It does not establish why they are absent.

This is an offline learning project, not a production FIX engine.

## Development

Record the assistance used, the changes personally made,
and the tests actually performed. Do not claim independent
authorship or production use unless accurate.