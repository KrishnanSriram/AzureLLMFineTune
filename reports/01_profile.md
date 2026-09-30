# Step 1 - Raw data profile

- Rows: **555**
- Columns: ticket_id, created_at, channel, customer_name, customer_email, subject, body, agent_tag, product, status
- Duplicate ticket_ids: 20
- Duplicate bodies (same text, any id): 50
- Empty bodies: 7
- Bodies containing HTML: 129
- Bodies containing an email address: 117
- Bodies containing a phone number: 142
- Blank product field: 185

## Missing values per column
| column | blank | % |
|---|---:|---:|
| ticket_id | 0 | 0% |
| created_at | 0 | 0% |
| channel | 0 | 0% |
| customer_name | 0 | 0% |
| customer_email | 0 | 0% |
| subject | 150 | 27% |
| body | 7 | 1% |
| agent_tag | 23 | 4% |
| product | 185 | 33% |
| status | 0 | 0% |

## Channel
| value | count |
|---|---:|
| email | 264 |
| web | 191 |
| chat | 100 |

## Status
| value | count |
|---|---:|
| solved | 342 |
| closed | 142 |
| open | 71 |

## Agent tags as typed (29 distinct)
| value | count |
|---|---:|
| General | 30 |
| misc | 29 |
| Warranty | 27 |
| RMA | 26 |
| where is my order | 25 |
| Order Status | 24 |
| Safety | 23 |
| (blank) | 23 |
| safety concern | 22 |
| Returns | 22 |
| WISMO | 22 |
| Defect | 21 |
| Return | 21 |
| exchange | 21 |
| shipping | 20 |
| Product question | 18 |
| refund | 18 |
| how to | 18 |
| urgent safety | 17 |
| wrnty | 17 |
| Tracking | 17 |
| defective part | 16 |
| question | 15 |
| SAFETY!! | 14 |
| Brake failure | 13 |
| warranty claim | 12 |
| safety issue | 12 |
| Billing | 9 |
| spam | 3 |

## Product field as typed
| value | count |
|---|---:|
| (blank) | 185 |
| cityglide e2 | 37 |
| TRAILBLAZER 29 | 30 |
| urbanfold mini | 30 |
| KIDRIDER 16 | 27 |
| trailblazer 29 | 27 |
| CITYGLIDE E2 | 25 |
| Trailblazer 29 | 24 |
| KidRider 16 | 24 |
| UrbanFold Mini | 23 |
| kidrider 16 | 23 |
| CityGlide E2 | 22 |
| URBANFOLD MINI | 22 |
| Summit Pro Carbon | 21 |
| SUMMIT PRO CARBON | 18 |
| summit pro carbon | 17 |

## Example raw email body
```
<p>Hi,</p><p>What tire pressure should I run on my Trailblazer 29er?</p><p>Sent from my iPhone</p><p>On Mon, Mar 3, 2026 at 9:14 AM Northwind Support <support@northwindbikes.example> wrote:<br>> Thanks for contacting Northwind Bikes.<br>> We received your request and will reply soon.</p>
```

## Example raw chat body
```
[10:00] Agent: Hi, thanks for contacting Northwind Bikes! How can I help?
[10:01] Customer: hi, I'm Ravi
[10:02] Customer: I found a crack in the frame of my Trail Blazer 29 near the seat post. Is it safe to ride?
[10:03] Agent: Sorry to hear that, let me check.
```
