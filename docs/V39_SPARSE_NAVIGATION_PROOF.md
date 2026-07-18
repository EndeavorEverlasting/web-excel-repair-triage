# V39 Sparse Prompt Library Navigation Proof

The Prompt Library navigation contract is enforced by executable tests and the V39 package generator.

- Allowed cadences: 10, 5, 2.
- Selection: largest cadence evenly dividing the prompt count.
- V39 prompt count: 56.
- Selected cadence: 2.
- Columns: A and P.
- Upper linked half: bottom footer.
- Lower linked half: top header.
- Header: bottom footer.
- Footer: top header.
- Non-cadence prompt rows: blank edge cells.
- Footer label: current prompt count.

The generated-workbook regression validates formulas, internal hyperlink metadata, direction, spacing, footer position, and footer text after an actual V38-to-V39 generation pass.
