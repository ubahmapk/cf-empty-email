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

    logger.debug("AWS credentials found in environment")

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


def check_for_mx_records(dns_records: dict) -> bool:
    """Check if there is already any MX records for the zone."""

    mx_records: list[dict] = [record for record in dns_records if record["type"] == "MX"]

    return bool(mx_records)


def check_for_spf_records(dns_records: dict) -> bool:
    """Check if there is already an SPF records for the zone."""

    spf_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "spf" in record["content"]
    ]

    return bool(spf_records)


def check_for_dkim_records(dns_records: dict) -> bool:
    """Check if there is already any DKIM records for the zone."""

    dkim_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "DKIM" in record["content"]
    ]

    return bool(dkim_records)


def check_for_dmarc_records(dns_records: dict) -> bool:
    """Check if there is already a DMARC record for the zone."""

    dmarc_records: list[dict] = [
        record for record in dns_records if record["type"] == "TXT" and "DMARC" in record["content"]
    ]

    return bool(dmarc_records)


def create_dkim_record(client: httpx.Client, zone_id: str) -> None:
    """Create a DKIM record for the zone."""

    record_data = {
        "comment": "Reject all DKIM record",
        "type": "TXT",
        "name": "*._domainkey",
        "content": "v=DKIM1; p=",
    }

    try:
        client.post(f"/zones/{zone_id}/dns_records", json=record_data)
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to create DKIM record for {zone_id}") from exc

    return None


def create_spf_record(client: httpx.Client, zone_id: str) -> None:
    """Create an SPF record for the zone."""

    record_data = {
        "comment": "Reject all senders SPF record",
        "type": "TXT",
        "name": "@",
        "content": "v=spf1 -all",
    }

    try:
        client.post(f"/zones/{zone_id}/dns_records", json=record_data)
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to create SPF record for {zone_id}") from exc

    return None


def create_dmarc_record(client: httpx.Client, zone_id: str) -> None:
    """Create a DMARC record for the zone."""

    record_data = {
        "comment": "DMARC reject all record",
        "type": "TXT",
        "name": "_dmarc",
        "content": "v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s",
    }

    try:
        client.post(f"/zones/{zone_id}/dns_records", json=record_data)
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to create MX record for {zone_id}") from exc

    return None


def create_mx_record(client: httpx.Client, zone_id: str) -> None:
    """Create an MX record for the zone."""

    record_data = {
        "comment": "Null mail server",
        "type": "MX",
        "name": "@",
        "content": ".",
        "priority": 0,
        "proxied": False,
        "ttl": 1,
    }

    try:
        client.post(f"/zones/{zone_id}/dns_records", json=record_data)
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to create MX record for {zone_id}") from exc

    return None


def process_single_zone(cf_zone: str, client: httpx.Client, print_only: bool, force: bool) -> None:
    """Given a zone name, print all DNS records for that zone."""

    cf_zone_id: str = ""
    dns_records: dict = {}

    with client as client:
        try:
            cf_zone_id = get_zone_id(client, cf_zone)
            logger.debug(f"{cf_zone_id=}")
        except ZoneNotFoundError:
            exit("Unable to retrieve Zone ID")

        dns_records = retrieve_dns_records(client, cf_zone_id)

    mx_exists: bool = check_for_mx_records(dns_records)
    spf_exists: bool = check_for_spf_records(dns_records)
    dkim_exists: bool = check_for_dkim_records(dns_records)
    dmarc_exists: bool = check_for_dmarc_records(dns_records)

    print(f"MX records exist: {mx_exists}")
    print(f"SPF records exist: {spf_exists}")
    print(f"DKIM records exist: {dkim_exists}")
    print(f"DMARC records exist: {dmarc_exists}")
    print()

    if print_only:
        print_dns_records(dns_records)
        return None

    if (mx_exists or spf_exists or dkim_exists or dmarc_exists) and not force:
        rprint("[bold red]Email DNS records already exist for this domain.[/bold red]")
        rprint("[bold]Pass the --force flag to add the records anyway[/bold]")
        print()
        print_dns_records(dns_records)
        return None

    return None


app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})


def version_callback(value: bool) -> None:
    if value:
        print(f"aws-costs version {__version__}")

        raise typer.Exit(0)

    return None


@app.command()
def main(
    cf_zone: Annotated[str, typer.Argument()] = "",
    print_only: Annotated[bool, typer.Option("--print", "-p", help="Only print the DNS records for the zone")] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite records if they already exist")] = False,
    verbosity: Annotated[int, typer.Option("--verbose", "-v", help="Repeat for extra verbosity")] = 0,
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

    process_single_zone(cf_zone, client, print_only, force)
