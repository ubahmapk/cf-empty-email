# Cloudflare Empty Email

Python script to insert null email records into Cloudflare DNS zones.

These DNS records are used to secure an otherwise parked domain (or any domain that does not send and receive email) from being used to send spoofed messages.

## Usage

 ```Usage: cf-empty-email [OPTIONS] [CF_ZONE]

 Add empty email DNS records for a given Cloudflare zone.
 Usage: cf_empty_email <zone_name>
 If no zone name is provided, a list of zones available to the user
 will be displayed.
 Credentials are accepted via the two environment variables:

 CF_API_KEY
 CF_API_EMAIL

╭─ Arguments ─────────────────────────────────────────────────────────╮
│   cf_zone      [CF_ZONE]  The domain name managed by Cloudflare     │
╰─────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────╮
│ --print    -p               Only print the DNS records for the zone │
│ --force    -f               Overwrite records if they already exist │
│ --verbose  -v      INTEGER  Repeat for extra verbosity [default: 0] │
│ --help     -h               Show this message and exit.             │
╰─────────────────────────────────────────────────────────────────────╯
```

## Email Records

The SPF, DKIM, and DMARC DNS records that are created in the domain are based on the instructions in the Cloudflare article, ["How to protect domains that do not send email"](https://www.cloudflare.com/learning/dns/dns-records/protect-domains-without-email/) (as of 2025-01-06). The explanation of the records are also copied from there.

The other entry created is a null MX record, based on [RFC 7505](https://www.rfc-editor.org/rfc/rfc7505).

### SPF

> SPF records can be formatted to protect domains against attempted phishing attacks by rejecting any emails sent from the domain. To do so, an SPF record must use the following format.
>
> ```
> v=spf1 -all
> ```
>
> Here is what the individual components of this record mean:
>
> - v=spf1 lets the server know that the record contains an SPF policy. All SPF records must begin with this component.
> - The indicator -all tells the server what to do with non-compliant emails or any senders that are not explicitly listed in the SPF record.
>
> With this type of SPF record, no IP addresses or domains are allowed, so -all states that all non-compliant emails will be rejected. For this type of record, all emails are considered non-compliant because there are no accepted IP addresses or domains.

### DKIM

> DKIM records protect domains by ensuring emails were actually authorized by the sender using a public key and a private key. DKIM records store the public key that the email server then uses to authenticate that the email signature was authorized by the sender. For domains that do not send emails, the DKIM record should be configured without an associated public key. Below is an example:
>
> | Name                     | Type | Content     |
> | ------------------------ | ---- | ----------- |
> | *._domainkey.example.com |  TXT | v=DKIM1; p= |
>
> - *._domainkey.example.com is the specialized name for the DKIM record (where “example.com” should be replaced with your domain). In this example, the asterisk (referred to as the wildcard) is being used as the selector, which is a specialized value that the email service provider generates and uses for the domain. The selector is part of the DKIM header and the email server uses it to perform the DKIM lookup in the DNS. The wildcard covers all possible values for the selector.
> - TXT indicates the DNS record type.
> - v=DKIM1 sets the version number and tells the server that this record references a DKIM policy.
> - The p value helps authenticate emails by tying a signature to its public key. In this DKIM record, the p value should be empty because there is no signature/public key to tie back to.

### DMARC

> DMARC policies can also help protect domains that do not send emails by rejecting all emails that fail SPF and DKIM. In this case, all emails sent from a domain not configured to send emails would fail SPF and DKIM checks. Below is an example of how to format a policy this way:
>
> | Name               | Type | Content                                    |
> | ------------------ | ---- | ------------------------------------------ |
> | _dmarc.example.com | TXT  | v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s |
>
>
> - The name field ensures that the record is set on the subdomain called _dmarc.example.com, which is required for DMARC policies.
> - TXT indicates the DNS record type.
> - v=DMARC1 tells the server that this DNS record contains a DMARC policy.
> - p=reject indicates that email servers should reject emails that fail DKIM and SPF checks.
> - adkim=s represents something called the alignment mode. In this case, the alignment mode is set to “s” for strict. Strict alignment mode means that the server of the email domain that contains the DMARC record must exactly match the domain in the From header of the email. If it does not, the DKIM check fails.
> - aspf=s serves the same purpose as adkim=s, but for SPF alignment.

### MX

The MX record below is called a "null MX record" and is a construct that is recognized by at least some (?) email systems.

| Type | Priority | Content |
| ---- | -------- | ------- |
| MX   | 0        | .       |

- MX is the DNS record type for email servers
- Priority 0 specifies this is entry has the highest priority for all email
- Content of "." is not actually a valid DNS hostname. But using a single dot in this way ensures it cannot be confused with any valid email server (as described in the RFC)

This script creates two MX records:

- One for the root domain (i.e. "@")
- One for any and all subdomains (i.e. "*.")
