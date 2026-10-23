# Search eval: `v1`

Date: 2026-10-23 · 40 queries · embeddings: text-embedding-3-small · RRF k=60

## Overall

| Method | Recall@5 | MRR |
|---|---|---|
| part_number | 42% | 0.41 |
| keyword | 78% | 0.69 |
| meaning | 88% | 0.78 |
| hybrid | 92% | 0.82 |

## Recall@5 by query type

| Query type | n | part_number | keyword | meaning | hybrid |
|---|---|---|---|---|---|
| exact code | 8 | 100% | 88% | 100% | 100% |
| messy code | 6 | 100% | 50% | 100% | 100% |
| code + words | 5 | 60% | 100% | 80% | 100% |
| description | 11 | 0% | 82% | 82% | 82% |
| synonyms | 10 | 0% | 70% | 80% | 90% |

## Hybrid: queries where the right part was not ranked first

- **s15** (code + words) `6205 sealed bearing`: correct at rank 4. Top 3: 6205 (bearing:6205:open), 6205 (bearing:6205:open), 6205 (bearing:6205:open)
- **s20** (description) `sealed deep groove bearing 25mm bore 52 OD`: correct at rank 4. Top 3: 6205 (bearing:6205:open), 6205 (bearing:6205:open), 6205 (bearing:6205:open)
- **s21** (description) `1.5 kW 4 pole motor foot mounted 400V`: correct at rank not in top 10. Top 3: FM-IE3-112M4-4-B3 (motor:4kw:4p:B3), NM3-112M-4P-4KW-B3 (motor:4kw:4p:B3), NM3-80M-4P-0.55KW-B3 (motor:0.55kw:4p:B3)
- **s22** (description) `hydraulic return filter element 10 micron 400mm long`: correct at rank 3. Top 3: HE250-10M (filter:hydraulic:10:250), HE160-10M (filter:hydraulic:10:160), HE400-10M (filter:hydraulic:10:400)
- **s24** (description) `spin-on oil filter 3/4-16 UNF thread 140mm high`: correct at rank 3. Top 3: FSO/UNF34/100 (filter:spin-on:UNF34:100), SO-UNF34-100 (filter:spin-on:UNF34:100), FSO/UNF34/140 (filter:spin-on:UNF34:140)
- **s27** (description) `11 kW 2 pole motor flange mount`: correct at rank 9. Top 3: NM3-80M-2P-0.75KW-B5 (motor:0.75kw:2p:B5), NM3-90L-2P-2.2KW-B5 (motor:2.2kw:2p:B5), NM3-132S-2P-7.5KW-B5 (motor:7.5kw:2p:B5)
- **s33** (synonyms) `ball bearing for 20mm shaft, 47mm housing, rubber sealed`: correct at rank 3. Top 3: 6005-2RSR (bearing:6005:sealed), 6000-2RS1 (bearing:6000:sealed), 6204-2RSR (bearing:6204:sealed)
- **s35** (synonyms) `fan belt A section 1067 mm`: correct at rank 3. Top 3: FX-A46 (belt:A46), A46 (belt:A46), A42 (belt:A42)
- **s36** (synonyms) `1450 rpm motor 2.2 kW feet mounted`: correct at rank not in top 10. Top 3: NM3-80M-2P-0.75KW-B3 (motor:0.75kw:2p:B3), NM3-71M-2P-0.37KW-B3 (motor:0.37kw:2p:B3), NM3-132S-2P-5.5KW-B3 (motor:5.5kw:2p:B3)
