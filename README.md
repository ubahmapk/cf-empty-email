# CF-NO-EMAIL

Python script to insert null email records into Cloudflare DNS zones.

The framework of this code was copied from my cf-check-dns script.

## Usage

 ```Usage: cf-empty-email [OPTIONS] [CF_ZONE]

 Add empty email DNS records for a given Cloudflare zone.

 Usage: cf_empty_email <zone_name>

 If no zone name is provided, a list of zones available to the user will be displayed.
 Credentials are accepted via the two environment variables:

 CF_API_KEY
 CF_API_EMAIL

╭─ Arguments ─────────────────────────────────────────────────────────────╮
│   cf_zone      [CF_ZONE]                                                │
╰─────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────╮
│ --print    -p               Only print the DNS records for the zone     │
│ --force    -f               Overwrite records if they already exist     │
│ --verbose  -v      INTEGER  Repeat for extra verbosity [default: 0]     │
│ --help     -h               Show this message and exit.                 │
╰─────────────────────────────────────────────────────────────────────────╯
```
