# Step 3 - Redact personal data

- Rows: **403**
- Dropped columns: customer_name, customer_email

## Replacements
| token | count |
|---|---:|
| [ORDER_ID] | 118 |
| [PHONE] | 82 |
| [NAME] | 74 |
| [EMAIL] | 43 |

```
before: The battery on my Trailblazer 29er got really hot and started smoking in the garage. You can call me at (888) 491-3906.
after:  The battery on my Trailblazer 29er got really hot and started smoking in the garage. You can call me at [PHONE].
```

```
before: My name is Zoe Lee. Is it ok to ride the Trailblazer 29 in the rain? My email is zoe.lee60@example.com.
after:  My name is [NAME] [NAME]. Is it ok to ride the Trailblazer 29 in the rain? My email is [EMAIL].
```

```
before: How often should I get my bike serviced? You can call me at 714-213-5473.
after:  How often should I get my bike serviced? You can call me at [PHONE].
```
