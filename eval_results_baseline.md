# Baseline retrieval results

228 lesson units, 21 dev queries (threshold choice), 19 test queries (reported below).

| Method | Threshold | Hit@1 | Hit@3 | False refusals | Correct refusals | ms/query |
|---|---|---|---|---|---|---|
| lookup | 0.00 | 41% | 41% | 53% | 100% | 1.15 |
| keyword | 0.12 | 76% | 88% | 6% | 50% | 0.25 |
| router | 0.12 | 88% | 88% | 6% | 50% | 1.11 |

Hit@3 by query type (test split):

| Method | confusion | descriptive | explicit |
|---|---|---|---|
| lookup | 40% | 0% | 100% |
| keyword | 80% | 100% | 80% |
| router | 60% | 100% | 100% |

The queries and the index hints were written by the same author, so treat these numbers as optimistic until real learners' questions are added.
