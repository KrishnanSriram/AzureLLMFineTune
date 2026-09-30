# Step 7 - Validate

Tokenizer: approx (chars / 4) - pip install tiktoken for exact counts

| file | examples | tokens | max tokens/example | bad lines |
|---|---:|---:|---:|---:|
| training | 276 | 30,316 | 125 | 0 |
| validation | 58 | 6,377 | 127 | 0 |
| test | 58 | 6,380 | 122 | 0 |

## Estimated training cost (3 epochs, 90,948 billed tokens)
| training type | est. cost |
|---|---:|
| GlobalStandard | $0.14 |
| developerTier | $0.07 |

Prices are illustrative - confirm on the Azure OpenAI pricing page.

## Result
**PASS**
