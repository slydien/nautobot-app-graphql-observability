#!/usr/bin/env python3
"""Generate GraphQL traffic against a Nautobot instance for dashboard testing.

Creates test users with API tokens and sends a mix of GraphQL queries
(varying depth, complexity, valid/invalid) to exercise all Prometheus metrics.

Usage:
    python scripts/generate_traffic.py [--base-url http://localhost:8080] [--rounds 10] [--delay 2]
"""

import argparse
import os
import random
import sys
import time

import requests

DEFAULT_BASE_URL = "http://localhost:8080"
ADMIN_TOKEN = "0123456789abcdef0123456789abcdef01234567"

# Test users to create — each gets their own API token.
TEST_USERS = [
    {"username": "testuser_alice", "password": "testpass123!"},
    {"username": "testuser_bob", "password": "testpass123!"},
    {"username": "testuser_charlie", "password": "testpass123!"},
    {"username": "testuser_diana", "password": "testpass123!"},
    {"username": "testuser_eve", "password": "testpass123!"},
]

# --- Query library ---
# Each entry: (name, query, should_succeed)

QUERIES = [
    # Simple shallow queries (depth 1-2)
    (
        "ListLocations",
        '{ locations(name: "test") { id name } }',
        True,
    ),
    (
        "ListDevices",
        "{ devices { id name } }",
        True,
    ),
    (
        "ListPrefixes",
        "{ prefixes { id prefix } }",
        True,
    ),
    (
        "ListVLANs",
        "{ vlans { id vid name } }",
        True,
    ),
    (
        "ListIPAddresses",
        "{ ip_addresses { id address } }",
        True,
    ),
    (
        "ListInterfaces",
        "{ interfaces { id name } }",
        True,
    ),
    (
        "ListCircuits",
        "{ circuits { id cid } }",
        True,
    ),
    (
        "ListTenants",
        "{ tenants { id name } }",
        True,
    ),
    # Medium depth queries (depth 3-4)
    (
        "DevicesWithInterfaces",
        "{ devices { id name location { id name } interfaces { id name } } }",
        True,
    ),
    (
        "PrefixesWithVLAN",
        "{ prefixes { id prefix vlan { id vid name location { id name } } } }",
        True,
    ),
    (
        "LocationHierarchy",
        "{ locations { id name location_type { id name } parent { id name } } }",
        True,
    ),
    (
        "DeviceDetails",
        """{ devices {
            id name status { id name }
            role { id name }
            location { id name location_type { id name } }
            platform { id name }
        } }""",
        True,
    ),
    # Deep queries (depth 5+)
    (
        "DeepDeviceQuery",
        """{ devices {
            id name
            location {
                id name
                parent {
                    id name
                    parent {
                        id name
                    }
                }
            }
            interfaces {
                id name
                ip_addresses {
                    id address
                }
            }
        } }""",
        True,
    ),
    (
        "DeepPrefixQuery",
        """{ prefixes {
            id prefix
            namespace { id name }
            vlan {
                id vid name
                vlan_group { id name }
                location {
                    id name
                    location_type { id name }
                    parent { id name }
                }
            }
            location { id name }
        } }""",
        True,
    ),
    # High complexity queries (many fields)
    (
        "ComplexDeviceQuery",
        """{ devices {
            id name
            status { id name }
            role { id name }
            device_type { id model manufacturer { id name } }
            location { id name }
            platform { id name }
            serial
            primary_ip4 { id address }
            primary_ip6 { id address }
            comments
            interfaces { id name enabled mtu mac_address type description }
        } }""",
        True,
    ),
    (
        "ComplexLocationQuery",
        """{ locations {
            id name
            location_type { id name }
            parent { id name }
            status { id name }
            tenant { id name }
            description
            vlans { id vid name status { id name } }
            prefixes { id prefix status { id name } }
            devices { id name }
        } }""",
        True,
    ),
    # Queries that should produce errors
    (
        "InvalidField",
        "{ devices { id name nonexistent_field } }",
        False,
    ),
    (
        "SyntaxError",
        "{ devices { id name ",
        False,
    ),
    (
        "UnknownType",
        "{ fake_model_that_does_not_exist { id } }",
        False,
    ),
    (
        "BadFilter",
        '{ devices(invalid_filter: "nope") { id } }',
        False,
    ),
    # Named operations (mutations are not typically available in Nautobot's
    # read-only GraphQL, but the query will be processed and produce an error metric)
    (
        "IntrospectionQuery",
        "{ __schema { types { name kind } } }",
        True,
    ),
    (
        "TypeIntrospection",
        '{ __type(name: "DeviceType") { name fields { name type { name } } } }',
        True,
    ),
]


def api_session(base_url, token):
    """Create a requests session with auth headers."""
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    s.base_url = base_url
    return s


def setup_users_via_orm():
    """Create test users and tokens directly via Django ORM.

    This avoids the REST API limitation where tokens are always assigned
    to the requesting (admin) user rather than the specified user.

    Returns:
        list[tuple[str, str]]: List of (username, token_key) pairs.
    """
    import django  # pylint: disable=import-outside-toplevel

    os.environ.setdefault("NAUTOBOT_CONFIG", "/opt/nautobot/nautobot_config.py")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nautobot.core.settings")

    from nautobot.core.cli import load_settings  # pylint: disable=import-outside-toplevel

    load_settings(os.environ["NAUTOBOT_CONFIG"])
    django.setup()

    from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel
    from nautobot.users.models import Token  # pylint: disable=import-outside-toplevel

    User = get_user_model()
    results = []

    for user_info in TEST_USERS:
        username = user_info["username"]
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_active": True},
        )
        if created:
            user.set_password(user_info["password"])
            user.save()
            print(f"  Created user: {username}")
        else:
            print(f"  User exists:  {username}")

        # Get or create a token owned by this user
        token = Token.objects.filter(user=user).first()
        if not token:
            token = Token.objects.create(user=user)
            print(f"  Token created: {username} -> {token.key[:12]}...")
        else:
            print(f"  Token exists:  {username} -> {token.key[:12]}...")

        results.append((username, token.key))

    return results


def send_graphql(session, base_url, query_name, query):
    """Send a GraphQL query and return (status_code, response_json, duration_ms)."""
    start = time.time()
    try:
        resp = session.post(
            f"{base_url}/api/graphql/",
            json={"query": query},
            timeout=30,
        )
        duration = (time.time() - start) * 1000
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:500]}
        return resp.status_code, body, duration
    except requests.exceptions.RequestException as exc:
        duration = (time.time() - start) * 1000
        return 0, {"error": str(exc)}, duration


def main():
    parser = argparse.ArgumentParser(description="Generate GraphQL traffic for dashboard testing")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Nautobot base URL")
    parser.add_argument("--rounds", type=int, default=10, help="Number of traffic rounds")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between rounds (seconds)")
    parser.add_argument("--admin-token", default=ADMIN_TOKEN, help="Admin API token")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    admin = api_session(base_url, args.admin_token)

    # --- Step 1: Check connectivity ---
    print("Checking Nautobot connectivity...")
    try:
        resp = admin.get(f"{base_url}/api/status/")
        if resp.status_code != 200:
            print(f"ERROR: Cannot reach Nautobot API (status {resp.status_code})")
            sys.exit(1)
        version = resp.json().get("nautobot-version", "unknown")
        print(f"  Connected to Nautobot {version}\n")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {base_url}")
        sys.exit(1)

    # --- Step 2: Create test users via Django ORM ---
    print("Setting up test users...")
    user_tokens = setup_users_via_orm()
    user_sessions = [{"username": username, "session": api_session(base_url, token)} for username, token in user_tokens]
    # Always include admin
    user_sessions.append({"username": "admin", "session": admin})
    print(f"\n  {len(user_sessions)} users ready for traffic generation\n")

    # --- Step 3: Generate traffic ---
    stats = {"total": 0, "success": 0, "errors": 0, "http_errors": 0}

    print(f"Generating traffic ({args.rounds} rounds, {args.delay}s delay)...\n")
    for round_num in range(1, args.rounds + 1):
        # Pick a random subset of queries for this round
        num_queries = random.randint(3, len(QUERIES))
        round_queries = random.sample(QUERIES, num_queries)

        print(f"--- Round {round_num}/{args.rounds} ({num_queries} queries) ---")

        for query_name, query, should_succeed in round_queries:
            # Pick a random user
            user = random.choice(user_sessions)
            username = user["username"]

            status_code, body, duration_ms = send_graphql(user["session"], base_url, query_name, query)
            stats["total"] += 1

            has_errors = "errors" in body if isinstance(body, dict) else False
            marker = ""

            if status_code == 0:
                marker = "CONN_ERR"
                stats["http_errors"] += 1
            elif status_code >= 400:
                marker = f"HTTP_{status_code}"
                stats["http_errors"] += 1
            elif has_errors:
                marker = "GQL_ERR"
                stats["errors"] += 1
            else:
                marker = "OK"
                stats["success"] += 1

            print(f"  [{marker:>8}] {query_name:<28} " f"user={username:<20} " f"{duration_ms:6.0f}ms")

        if round_num < args.rounds:
            time.sleep(args.delay)
        print()

    # --- Summary ---
    print("=" * 60)
    print("Traffic generation complete!")
    print(f"  Total requests:  {stats['total']}")
    print(f"  Successful:      {stats['success']}")
    print(f"  GraphQL errors:  {stats['errors']}")
    print(f"  HTTP errors:     {stats['http_errors']}")
    print()
    print("Check your dashboards:")
    print(f"  Prometheus: {base_url.replace('8080', '9090')}")
    print(f"  Grafana:    {base_url.replace('8080', '3000')}")
    print(f"  Metrics:    {base_url}/metrics/")


if __name__ == "__main__":
    main()
