import pytest

from cf_empty_email.app import (
    parse_for_dkim_records,
    parse_for_dmarc_records,
    parse_for_mx_records,
    parse_for_spf_records,
)

zone_id: str = ""
zone_name: str = "example.net"
host_name: str = "example.net"
spf_include: str = "example.com"

id_list: list[str] = [
    "C7C2737244FD3ADB5F8F77EE13E7A98B",
    "FDD311FE3942F567C9B1BFEB1972CF3E",
    "A937DC56A20C884E0F1C186210AE06F5",
    "B6171610233BB7C057F3494FA1D0D6CD",
    "6DAC3A6D6FADD446631853AE38DF34B5",
    "A02BF92A53E47B5F602CC82DD7C3D889",
    "D63D2B7C8F450B4DEDE1484766CE055D",
    "C2016ABEAEFD43FAEEBA7B0E4839D5A8",
    "4F64B22B0ECA418CD4179305930D977D",
    "F1B1D08E06D83A35853B7BE52A43848C",
    "46BCF1F04994FB97C0EF06E97446D7CD",
    "6D1F5A0A79E58791D223B679C802FDB8",
    "765BB81AFE308AEC88FD98EDF4DDA567",
    "27D467BA06497B8E3F83EB76C6CBD4AF",
    "196F648C20607FBD798C36018A054312",
    "98BA2596F7B34A54C1F2E6BE55A4FCD2",
]


# Placeholder non-email related DNS records
@pytest.fixture()
def test_other_dns_records() -> list[dict]:
    return [
        {
            "id": id_list[0],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "A",
            "content": "10.1.1.1",
            "proxiable": True,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2023-12-15T22:53:29.695701Z",
            "modified_on": "2024-10-21T16:25:33.288853Z",
        },
        {
            "id": id_list[1],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "A",
            "content": "10.1.1.2",
            "proxiable": True,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2023-12-15T22:53:29.695701Z",
            "modified_on": "2024-10-21T16:25:33.288853Z",
        },
        {
            "id": id_list[2],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "A",
            "content": "10.1.1.3",
            "proxiable": True,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2023-12-15T22:53:29.695701Z",
            "modified_on": "2024-10-21T16:25:33.288853Z",
        },
        {
            "id": id_list[3],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "AAAA",
            "content": "fd12:3456:789a:1::1",
            "proxiable": True,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2023-12-15T22:53:29.640148Z",
            "modified_on": "2024-10-21T16:25:51.889319Z",
        },
        {
            "id": id_list[4],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": f"sig1._domainkey.{zone_name}",
            "type": "CNAME",
            "content": f"sig1.dkim.{zone_name}",
            "proxiable": True,
            "proxied": False,
            "ttl": 3600,
            "settings": {...},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2025-01-05T04:04:43.844386Z",
            "modified_on": "2025-01-05T04:04:43.844386Z",
        },
        {
            "id": id_list[5],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": f"www.{zone_name}",
            "type": "CNAME",
            "content": f"alias.{zone_name}",
            "proxiable": True,
            "proxied": False,
            "ttl": 1,
            "settings": {...},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2023-12-15T22:53:29.741852Z",
            "modified_on": "2024-10-21T16:26:46.847953Z",
        },
    ]


# Placeholder MX DNS records
@pytest.fixture()
def test_mx_dns_records() -> list[dict]:
    return [
        {
            "id": id_list[6],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "MX",
            "content": f"mx02.mail.{zone_name}",
            "priority": 10,
            "proxiable": False,
            "proxied": False,
            "ttl": 3600,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2025-01-05T04:04:43.843635Z",
            "modified_on": "2025-01-05T04:04:43.843635Z",
        },
        {
            "id": id_list[7],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "MX",
            "content": f"mx01.mail.{zone_name}",
            "priority": 10,
            "proxiable": False,
            "proxied": False,
            "ttl": 3600,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2025-01-05T04:04:43.834101Z",
            "modified_on": "2025-01-05T04:04:43.834101Z",
        },
    ]


# Placeholder TXT DNS records
@pytest.fixture()
def test_spf_dns_records() -> list[dict]:
    return [
        {
            "id": id_list[8],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": host_name,
            "type": "TXT",
            "content": f'"v=spf1 include:{spf_include} ~all"',
            "proxiable": False,
            "proxied": False,
            "ttl": 3600,
            "settings": {},
            "meta": {...},
            "comment": None,
            "tags": [...],
            "created_on": "2025-01-05T04:04:43.847471Z",
            "modified_on": "2025-01-05T04:04:43.847471Z",
        },
    ]


@pytest.fixture()
def test_dmarc_dns_records() -> list[dict]:
    return [
        {
            "id": id_list[9],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": f"_dmarc.{zone_name}",
            "type": "TXT",
            "content": '"v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s"',
            "proxiable": False,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": "DMARC reject all record",
            "tags": [...],
            "created_on": "2025-01-06T19:45:22.271215Z",
            "modified_on": "2025-01-06T19:45:22.271215Z",
            "comment_modified_on": "2025-01-06T19:45:22.271215Z",
        },
    ]


@pytest.fixture()
def test_dkim_dns_records() -> list[dict]:
    return [
        {
            "id": id_list[10],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": f"*._domainkey.{zone_name}",
            "type": "TXT",
            "content": '"v=DKIM1; p="',
            "proxiable": False,
            "proxied": False,
            "ttl": 1,
            "settings": {},
            "meta": {...},
            "comment": "Reject all DKIM record",
            "tags": [...],
            "created_on": "2025-01-06T19:45:22.065941Z",
            "modified_on": "2025-01-06T19:45:22.065941Z",
            "comment_modified_on": "2025-01-06T19:45:22.065941Z",
        },
    ]


def test_parse_for_mx_records(test_other_dns_records: list[dict], test_mx_dns_records: list[dict]) -> None:
    mx_records = parse_for_mx_records(test_other_dns_records)
    assert len(mx_records) == 0

    test_records = test_other_dns_records + test_mx_dns_records
    mx_records = parse_for_mx_records(test_records)
    assert len(mx_records) == 2


def test_parse_for_spf_records(test_other_dns_records: list[dict], test_spf_dns_records: list[dict]) -> None:
    spf_records = parse_for_spf_records(test_other_dns_records)
    assert len(spf_records) == 0

    test_records = test_other_dns_records + test_spf_dns_records
    spf_records = parse_for_spf_records(test_records)
    assert len(spf_records) == 1


def test_parse_for_dmarc_records(test_other_dns_records: list[dict], test_dmarc_dns_records: list[dict]) -> None:
    dmarc_records = parse_for_dmarc_records(test_other_dns_records)
    assert len(dmarc_records) == 0

    test_records = test_other_dns_records + test_dmarc_dns_records
    dmarc_records = parse_for_dmarc_records(test_records)
    assert len(dmarc_records) == 1


def test_parse_for_dkim_records(test_other_dns_records: list[dict], test_dkim_dns_records: list[dict]) -> None:
    dkim_records = parse_for_dkim_records(test_other_dns_records)
    assert len(dkim_records) == 0

    test_records = test_other_dns_records + test_dkim_dns_records
    dkim_records = parse_for_dkim_records(test_records)
    assert len(dkim_records) == 1
