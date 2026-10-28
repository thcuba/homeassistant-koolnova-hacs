#!/usr/bin/env python3
"""
Script to investigate additional Koolnova API methods
"""

import json
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../custom_components/koolnova"))

from koolnova_api.client import KoolnovaAPIRestClient
from koolnova_api.exceptions import KoolnovaError

def test_api_methods():
    """Test additional API methods with credentials"""

    # Credentials from environment variables
    username = os.getenv('KOOLNOVA_USERNAME')
    password = os.getenv('KOOLNOVA_PASSWORD')
    email = os.getenv('KOOLNOVA_EMAIL', username)  # Default email is username if it's an email

    if not username or not password:
        print("❌ ERROR: Credentials not provided")
        print("\n💡 To use this script, set the environment variables:")
        print("   export KOOLNOVA_USERNAME='your_username_or_email'")
        print("   export KOOLNOVA_PASSWORD='your_password'")
        print("   export KOOLNOVA_EMAIL='your_email'  # optional if username is email")
        print("\n   Example:")
        print("   export KOOLNOVA_USERNAME='user@example.com'")
        print("   export KOOLNOVA_PASSWORD='mypassword'")
        print("   python test_api_methods.py")
        return

    print("🔐 Attempting authentication on Koolnova API...")
    print(f"User: {username}")
    print(f"Email: {email}")

    try:
        client = KoolnovaAPIRestClient(username, password, email)

        # Test known methods first
        print("\n✅ Testing already implemented methods:")

        # Test projects
        try:
            projects = client.get_project()
            print(f"📋 Projects: {len(projects)} found")
            if projects:
                print(f"   First project: {projects[0].get('Project_Name', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Projects error: {e}")

        # Test sensors
        try:
            sensors = client.get_sensors()
            print(f"🌡️ Sensors: {len(sensors)} found")
            if sensors:
                print(f"   First zone: {sensors[0].get('Room_Name', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Sensors error: {e}")

        print("\n🔍 Testing additional discovered methods:")

        # List of additional endpoints to test
        additional_endpoints = [
            'notifications',
            'devices',
            'users'
        ]

        for endpoint in additional_endpoints:
            try:
                print(f"\n📡 Testing /{endpoint}/")
                response = client._get_session().rest_request("GET", endpoint + "/")
                print(f"   ✅ Response: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📊 Data received: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   🔑 Main keys: {list(data.keys())}")
                        # Show pagination details
                        if 'total' in data:
                            print(f"   📄 Total items: {data['total']}")
                        if 'data' in data and isinstance(data['data'], list):
                            print(f"   📝 Items on page: {len(data['data'])}")
                            if data['data'] and isinstance(data['data'][0], dict):
                                print(f"   🔍 Keys of first item: {list(data['data'][0].keys())}")
                                # Show some sample data
                                first_item = data['data'][0]
                                print(f"   💡 Example - {endpoint}: {first_item}")
                    elif isinstance(data, list) and data:
                        print(f"   📝 First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'No dict'}")
                        print(f"   📊 Total items: {len(data)}")
            except Exception as e:
                print(f"   ❌ Error on /{endpoint}/: {e}")

        # Test methods related to existing modules
        print("\n🔧 Testing methods related to existing modules:")

        # Get module IDs first
        try:
            module_ids = client.search_all_ids()
            print(f"📟 IDs found: {module_ids}")

            if module_ids['koolnova']:
                koolnova_id = module_ids['koolnova'][0]
                print(f"🎯 Testing with Koolnova ID: {koolnova_id}")

                # Test endpoints related to modules
                module_endpoints = [
                    f'modules/{koolnova_id}/history',
                    f'modules/{koolnova_id}/logs',
                    f'modules/{koolnova_id}/measurements',
                    f'modules/{koolnova_id}/status',
                    f'modules/{koolnova_id}/diagnostics'
                ]

                for endpoint in module_endpoints:
                    try:
                        print(f"   📡 Testing /{endpoint}/")
                        response = client._get_session().rest_request("GET", endpoint)
                        print(f"      ✅ Response: {response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            print(f"      📊 Data type: {type(data)}")
                    except Exception as e:
                        print(f"      ❌ Error: {e}")

        except Exception as e:
            print(f"❌ Error obtaining module IDs: {e}")

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("\n💡 To use this script:")
        print("   export KOOLNOVA_USERNAME='your_username'")
        print("   export KOOLNOVA_PASSWORD='your_password'")
        print("   export KOOLNOVA_EMAIL='your_email'")
        print("   python test_api_methods.py")

if __name__ == "__main__":
    test_api_methods()
