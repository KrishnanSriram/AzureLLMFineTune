# Step 2 - Clean

- Rows in: **555**
- Rows out: **403**

## Dropped rows by reason
| reason | rows |
|---|---:|
| not finished (open) | 67 |
| same text submitted twice | 50 |
| duplicate ticket_id | 20 |
| test or spam | 8 |
| empty / too short | 7 |

## Before
```
<p>Hello Northwind team,</p><p>The brakes on my trailblazer29 stopped working while I was going downhill.</p><p>Thanks,<br>Elena</p>
```
## After
```
The brakes on my trailblazer29 stopped working while I was going downhill.
```
