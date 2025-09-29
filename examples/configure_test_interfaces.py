#!/usr/bin/env python3

import os
from netmiko import ConnectHandler
from dotenv import load_dotenv
import time

load_dotenv("../../.env")

device_config = {
    'device_type': os.getenv('DEVICE_TYPE', 'cisco_xr'),
    'host': os.getenv('DEVICE_HOSTNAME'),
    'username': os.getenv('DEVICE_USERNAME'),
    'password': os.getenv('DEVICE_PASSWORD'),
    'port': int(os.getenv('DEVICE_PORT', 22)),
    'timeout': 30,
    'session_timeout': 60,
}

def configure_test_interfaces():
    """Configure interfaces with mixed compliance for testing"""

    print(f"Connecting to {device_config['host']}...")
    connection = ConnectHandler(**device_config)

    # First, get list of interfaces
    print("\nGetting current interface list...")
    output = connection.send_command("show ip interface brief")
    print(output)

    # Configuration commands for different test scenarios
    config_commands = [
        # Compliant interfaces - proper format: <LOCATION>_<PEER>_<CIRCUIT-ID>
        "interface GigabitEthernet0/0/0/0",
        "description NYC_AWS_DIRECT_CKT123",
        "exit",

        "interface GigabitEthernet0/0/0/1",
        "description LAX_AZURE_EXPRESS_CKT456",
        "exit",

        "interface GigabitEthernet0/0/0/2",
        "description CHI_GOOGLE_CLOUD_CKT789",
        "exit",

        # Non-compliant interfaces - incorrect format
        "interface GigabitEthernet0/0/0/3",
        "description To Core Switch",  # Missing proper format
        "exit",

        "interface GigabitEthernet0/0/0/4",
        "description AWS Direct Connect",  # Missing location and circuit ID
        "exit",

        "interface GigabitEthernet0/0/0/5",
        "description NYC-AWS",  # Using dashes instead of underscores
        "exit",

        # Remove descriptions from some interfaces (non-compliant - no description)
        "interface GigabitEthernet0/0/0/6",
        "no description",
        "exit",

        "interface Loopback0",
        "no description",  # Loopback without description
        "exit",

        # Add more compliant ones
        "interface Loopback100",
        "description SFO_MGMT_LOOP_CKT001",
        "exit",

        "interface Loopback200",
        "description DAL_MONITOR_LOOP_CKT002",
        "exit",
    ]

    print("\nConfiguring test interfaces...")
    output = connection.send_config_set(config_commands)
    print(output)

    # Commit configuration on XR
    print("\nCommitting configuration...")
    output = connection.send_command("commit")
    print(output)

    # Show the configured interfaces
    print("\n" + "="*50)
    print("CONFIGURED INTERFACES:")
    print("="*50)
    output = connection.send_command("show running-config interface | include ^interface|description")
    print(output)

    print("\n" + "="*50)
    print("INTERFACE STATUS:")
    print("="*50)
    output = connection.send_command("show ip interface brief")
    print(output)

    connection.disconnect()
    print("\nConfiguration complete!")

    # Summary
    print("\n" + "="*50)
    print("TEST SCENARIO SUMMARY:")
    print("="*50)
    print("COMPLIANT INTERFACES (5):")
    print("  - GigabitEthernet0/0/0/0: NYC_AWS_DIRECT_CKT123")
    print("  - GigabitEthernet0/0/0/1: LAX_AZURE_EXPRESS_CKT456")
    print("  - GigabitEthernet0/0/0/2: CHI_GOOGLE_CLOUD_CKT789")
    print("  - Loopback100: SFO_MGMT_LOOP_CKT001")
    print("  - Loopback200: DAL_MONITOR_LOOP_CKT002")
    print("\nNON-COMPLIANT INTERFACES (5):")
    print("  - GigabitEthernet0/0/0/3: 'To Core Switch' (incorrect format)")
    print("  - GigabitEthernet0/0/0/4: 'AWS Direct Connect' (missing location/circuit)")
    print("  - GigabitEthernet0/0/0/5: 'NYC-AWS' (using dashes)")
    print("  - GigabitEthernet0/0/0/6: No description")
    print("  - Loopback0: No description")

if __name__ == "__main__":
    try:
        configure_test_interfaces()
    except Exception as e:
        print(f"Error: {e}")