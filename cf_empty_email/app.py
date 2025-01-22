from sys import exit, stderr
from typing import Annotated

import httpx
import pandas as pd
import typer
from loguru import logger
from pydantic import EmailStr, Field, ValidationError
from pydantic_settings import BaseSettings
from rich import print as rprint

from cf_empty_email.__version__ import __version__

__author__ = "ubahmapk@proton.me"


class ZoneNotFoundError(Exception):
    pass


class DeleteRecordError(Exception):
    pass


class CreateRecordError(Exception):
    pass


class Settings(BaseSettings):
    cf_api_key: str = Field(pattern=r"^[a-zA-Z0-9_]*$")
    cf_api_email: EmailStr


def set_logging_level(verbosity: int) -> None:
    """Set the global logging level"""

    # Default level
    log_level = "INFO"

    if verbosity is not None:
        if verbosity == 1:
            log_level = "INFO"
        elif verbosity > 1:
            log_level = "DEBUG"
        else:
            log_level = "ERROR"

    logger.remove(0)
    # noinspection PyUnboundLocalVariable
    logger.add(stderr, level=log_level)

    return None


def retrieve_cf_credentials() -> tuple[str, str]:
    """Retrieve Cloudflare API credentials from environment variables"""

    cf_api_key: str = ""
    cf_api_email: str = ""

    try:
        settings = Settings()
        cf_api_key = settings.cf_api_key
        cf_api_email = settings.cf_api_email

    except ValidationError:
        message: str = "CloudFlare credentials are not set or are invalid.\n"
        message += "Please set the CF_API_KEY and CF_API_EMAIL environment variables."
        rprint(f"[bold red]{message}[/bold red]")
        raise typer.Abort() from None

    logger.debug("Cloudflare credentials found in environment")

    return cf_api_key, cf_api_email


def list_cf_zones(client: httpx.Client, cf_api_email: str) -> None:
    """List all zones available to the user."""

    try:
        result: dict = client.get("/zones").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID") from exc

    print(f"Available Zones for Cloudflare user {cf_api_email}:")
    for zone in result:
        print(f"\tZone: {zone['name']}")

    return None


def get_zone_id(client: httpx.Client, cf_zone: str) -> str:
    """Return the CF zone ID for a given Zone name."""

    zone_id: str = ""

    try:
        logger.debug(f"In get_zone_id: {cf_zone=}")
        result: dict = client.get("/zones").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID for {cf_zone}\nError details: {exc}") from exc

    try:
        zone_id = next(zone["id"] for zone in result if zone["name"] == cf_zone)
    except StopIteration:
        rprint(f"Zone [bold red]{cf_zone}[/bold red] not found")
        raise typer.Abort() from None

    logger.debug(f"Returning {zone_id=}")
    return zone_id


def retrieve_dns_records(client: httpx.Client, zone_id: str) -> dict:
    """Retrieve all DNS records for a given zone."""

    try:
        logger.debug(f"In retrieve_dns_records: {zone_id=}")
        result: dict = client.get(f"/zones/{zone_id}/dns_records").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID for {zone_id}") from exc

    return result


def print_dns_records(dns_records: dict) -> None:
    """Print all DNS records for a given zone."""

    if len(dns_records) == 0:
        print("No DNS records found")
        print()
        return None

    # Print the DNS records in a tabular format
    df: pd.DataFrame = pd.DataFrame.from_dict(dns_records)
    column_names: list[str] = ["modified_on", "name", "type", "content"]
    column_headers: list[str] = ["Last Updated", "Host", "Type", "Address"]
    print(df[column_names].to_string(index=False, header=column_headers, justify="right"))

    return None


def parse_for_mx_records(dns_records: dict) -> list[dict]:
    """Check if there is already any MX records for the zone."""

    mx_records: list[dict] = [record for record in dns_records if record["type"] == "MX"]

    return mx_records


def parse_for_spf_records(dns_records: dict) -> list[dict]:
    """Check if there is already an SPF records for the zone."""

    spf_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "spf" in record["content"]
    ]

    return spf_records


def parse_for_dkim_records(dns_records: dict) -> list[dict]:
    """Check if there is already any DKIM records for the zone."""

    dkim_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "DKIM" in record["content"]
    ]

    return dkim_records


def parse_for_dmarc_records(dns_records: dict) -> list[dict]:
    """Check if there is already a DMARC record for the zone."""

    dmarc_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "DMARC" in record["content"]
    ]

    return dmarc_records


def post_record(client: httpx.Client, zone_id: str, record_data: dict) -> None:
    """Post a DNS record for the zone."""

    try:
        client.post(f"/zones/{zone_id}/dns_records", json=record_data)
    except httpx.HTTPError as exc:
        raise CreateRecordError(f"Unable to create record for {zone_id}") from exc

    return None


def create_dkim_record(client: httpx.Client, zone_id: str) -> None:
    """Create a DKIM record for the zone."""

    # TXT record content must be wrapped in quotes
    record_data = {
        "comment": "Reject all DKIM record",
        "type": "TXT",
        "name": "*._domainkey",
        "content": '"v=DKIM1; p="',
    }

    post_record(client=client, zone_id=zone_id, record_data=record_data)

    return None


def create_spf_record(client: httpx.Client, zone_id: str) -> None:
    """Create an SPF record for the zone."""

    # TXT record content must be wrapped in quotes
    record_data = {
        "comment": "Reject all senders SPF record",
        "type": "TXT",
        "name": "@",
        "content": '"v=spf1 -all"',
    }

    post_record(client=client, zone_id=zone_id, record_data=record_data)

    return None


def create_dmarc_record(client: httpx.Client, zone_id: str) -> None:
    """Create a DMARC record for the zone."""

    # TXT record content must be wrapped in quotes
    record_data = {
        "comment": "DMARC reject all record",
        "type": "TXT",
        "name": "_dmarc",
        "content": '"v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s"',
    }

    post_record(client=client, zone_id=zone_id, record_data=record_data)

    return None


def create_mx_record(client: httpx.Client, zone_id: str) -> None:
    """Create an null MX record for the root domain and any subdomains."""

    record_data = [
        {
            "comment": "Null mail server for root domain",
            "type": "MX",
            "name": "@",
            "content": ".",
            "priority": 0,
            "proxied": False,
            "ttl": 1,
        },
        {
            "comment": "Null mail server for all subdomains",
            "type": "MX",
            "name": "*",
            "content": ".",
            "priority": 0,
            "proxied": False,
            "ttl": 1,
        },
    ]

    for record in record_data:
        post_record(client=client, zone_id=zone_id, record_data=record)

    return None


def delete_records(records: list[dict], client: httpx.Client, zone_id: str) -> None:
    """Delete all records in the list"""

    for record in records:
        print(f"Record Name: {record['name']}")
        print(f"Record Type: {record['type']}")
        print(f"Record Content: {record['content']}")
        message: str = "Delete this record?"
        if typer.confirm(message, default=False, show_default=True):
            try:
                client.delete(f"/zones/{zone_id}/dns_records/{record['id']}")
            except httpx.HTTPError as exc:
                raise DeleteRecordError(f"Unable to delete record {record['id']} for {zone_id}") from exc

    return None


app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})


def version_callback(value: bool) -> None:
    if value:
        print(f"cf-empty-email version {__version__}")

        raise typer.Exit(0)

    return None


@app.command()
def main(
    cf_zone: Annotated[str, typer.Argument(help="The domain name managed by Cloudflare")] = "",
    print_only: Annotated[bool, typer.Option("--print", "-p", help="Only print the DNS records for the zone")] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite records if they already exist")] = False,
    verbosity: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Repeat for extra verbosity")] = 0,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            show_default=False,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """
    \b
    Add empty email DNS records for a given Cloudflare zone.

    Usage: cf_empty_email <zone_name>

    If no zone name is provided, a list of zones available to the user will be displayed.

    \b
    Credentials are accepted via the two environment variables:

    \b
    CF_API_KEY
    CF_API_EMAIL
    """

    set_logging_level(verbosity)

    cf_api_key, cf_api_email = retrieve_cf_credentials()

    client_headers = {
        "X-Auth-Key": cf_api_key,
        "X-Auth-Email": cf_api_email,
        "Content-Type": "application/json",
    }

    client = httpx.Client(base_url="https://api.cloudflare.com/client/v4", headers=client_headers)

    if not cf_zone:
        list_cf_zones(client, cf_api_email)
        exit()

    cf_zone_id: str = ""
    dns_records: dict = {}

    with client as client:
        try:
            cf_zone_id = get_zone_id(client, cf_zone)
            logger.debug(f"{cf_zone_id=}")
        except ZoneNotFoundError:
            exit("Unable to retrieve Zone ID")

        dns_records = retrieve_dns_records(client, cf_zone_id)

    mx_records: list[dict] = parse_for_mx_records(dns_records)
    spf_records: list[dict] = parse_for_spf_records(dns_records)
    dkim_records: list[dict] = parse_for_dkim_records(dns_records)
    dmarc_records: list[dict] = parse_for_dmarc_records(dns_records)

    print(f"MX records exist: {bool(mx_records)}")
    print(f"SPF records exist: {bool(spf_records)}")
    print(f"DKIM records exist: {bool(dkim_records)}")
    print(f"DMARC records exist: {bool(dmarc_records)}")
    print()

    if print_only:
        print_dns_records(dns_records)
        return None

    # Re-open the client
    client = httpx.Client(base_url="https://api.cloudflare.com/client/v4", headers=client_headers)

    with client as client:
        if mx_records or spf_records or dkim_records or dmarc_records:
            if not force:
                message = "Email DNS records already exist for this domain."
                rprint(f"[bold red]{message}[/bold red]")
                message = "Pass the --force flag to add the records anyway."
                rprint(f"[bold]{message}[/bold]")
                print()
                print_dns_records(dns_records)
                raise typer.Abort()

            if mx_records:
                delete_records(mx_records, client, cf_zone_id)
            if spf_records:
                delete_records(spf_records, client, cf_zone_id)
            if dkim_records:
                delete_records(dkim_records, client, cf_zone_id)
            if dmarc_records:
                delete_records(dmarc_records, client, cf_zone_id)

        create_mx_record(client, cf_zone_id)
        create_spf_record(client, cf_zone_id)
        create_dkim_record(client, cf_zone_id)
        create_dmarc_record(client, cf_zone_id)

        updated_dns_records = retrieve_dns_records(client, cf_zone_id)

    print_dns_records(updated_dns_records)
