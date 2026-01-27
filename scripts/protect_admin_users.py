#!/usr/bin/env python3
"""
protect_admin_users.py

Safety control to prevent Terraform from managing/deleting super admin users.

Usage:
  python protect_admin_users.py --input imported/users/user.tf --output filtered/users.tf
  python protect_admin_users.py --check imported/users/user.tf
"""

import argparse
import json
import os
import re
import sys
import requests
from typing import List, Dict, Set


class OktaAdminProtector:
    """Protect super admin users from Terraform management"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_super_admins(self) -> Set[str]:
        """Get all users with super admin role"""
        print("🔍 Querying Okta for super admin users...")

        # Get the super admin role ID
        url = f"{self.base_url}/api/v1/iam/roles"
        response = self.session.get(url)
        response.raise_for_status()

        roles = response.json()
        super_admin_role = None

        for role in roles.get('roles', roles):
            if role.get('label') == 'Super Administrator' or role.get('type') == 'SUPER_ADMIN':
                super_admin_role = role.get('id')
                break

        if not super_admin_role:
            print("⚠️  Could not find Super Administrator role, trying alternative method...")
            return self._get_super_admins_alternative()

        # Get users assigned to super admin role
        url = f"{self.base_url}/api/v1/iam/roles/{super_admin_role}/users"
        response = self.session.get(url)
        response.raise_for_status()

        admin_users = response.json()
        admin_logins = set()

        for user in admin_users:
            login = user.get('profile', {}).get('login') or user.get('email')
            if login:
                admin_logins.add(login)
                print(f"  ⭐ Found super admin: {login}")

        return admin_logins

    def _get_super_admins_alternative(self) -> Set[str]:
        """Alternative method to find admins by checking user roles"""
        print("Using alternative admin detection method...")

        url = f"{self.base_url}/api/v1/users"
        params = {"limit": 200}
        response = self.session.get(url, params=params)
        response.raise_for_status()

        admin_logins = set()
        users = response.json()

        # Check each user's roles
        for user in users:
            user_id = user.get('id')
            login = user.get('profile', {}).get('login')

            # Check user's roles
            roles_url = f"{self.base_url}/api/v1/users/{user_id}/roles"
            roles_response = self.session.get(roles_url)

            if roles_response.status_code == 200:
                roles = roles_response.json()
                for role in roles:
                    if role.get('type') == 'SUPER_ADMIN' or 'SUPER' in role.get('type', ''):
                        admin_logins.add(login)
                        print(f"  ⭐ Found super admin: {login}")
                        break

        return admin_logins

    def parse_terraform_users(self, tf_file: str) -> List[Dict]:
        """Parse Terraform user resources from file"""
        with open(tf_file, 'r') as f:
            content = f.read()

        # Parse user resources by finding balanced braces
        users = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for resource "okta_user"
            resource_match = re.match(r'resource\s+"okta_user"\s+"([^"]+)"\s+\{', line)
            if resource_match:
                resource_name = resource_match.group(1)
                resource_lines = [line]
                brace_count = 1
                i += 1

                # Collect lines until braces are balanced
                while i < len(lines) and brace_count > 0:
                    current_line = lines[i]
                    resource_lines.append(current_line)

                    # Count braces (simple approach)
                    brace_count += current_line.count('{')
                    brace_count -= current_line.count('}')
                    i += 1

                full_block = '\n'.join(resource_lines)

                # Extract login (email)
                login_match = re.search(r'login\s*=\s*"([^"]+)"', full_block)
                email_match = re.search(r'email\s*=\s*"([^"]+)"', full_block)

                login = login_match.group(1) if login_match else None
                email = email_match.group(1) if email_match else None

                users.append({
                    'resource_name': resource_name,
                    'login': login or email,
                    'full_block': full_block
                })
            else:
                i += 1

        return users

    def filter_terraform_file(self, input_file: str, output_file: str, admin_logins: Set[str]) -> Dict:
        """Filter admin users from Terraform file"""
        users = self.parse_terraform_users(input_file)

        safe_users = []
        blocked_users = []

        for user in users:
            if user['login'] in admin_logins:
                blocked_users.append(user['login'])
                print(f"  🛡️  BLOCKED: {user['login']} (super admin - excluded from management)")
            else:
                safe_users.append(user)
                print(f"  ✅ SAFE: {user['login']} (will be managed by Terraform)")

        # Write filtered file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            f.write("# Terraform User Resources - Admin-Safe\n")
            f.write("# Generated by protect_admin_users.py\n")
            f.write(f"# Super admins excluded: {len(blocked_users)}\n")
            f.write(f"# Users managed: {len(safe_users)}\n\n")

            for user in safe_users:
                f.write(user['full_block'])
                f.write("\n\n")

        return {
            'total': len(users),
            'safe': len(safe_users),
            'blocked': len(blocked_users),
            'blocked_logins': blocked_users
        }

    def add_lifecycle_protection(self, input_file: str, output_file: str, admin_logins: Set[str]) -> Dict:
        """Add lifecycle prevent_destroy to admin users instead of removing them"""
        users = self.parse_terraform_users(input_file)

        protected_users = []
        normal_users = []

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            f.write("# Terraform User Resources - With Admin Protection\n")
            f.write("# Generated by protect_admin_users.py\n")
            f.write("# Super admins have lifecycle prevent_destroy enabled\n\n")

            for user in users:
                if user['login'] in admin_logins:
                    # Add lifecycle block
                    protected_users.append(user['login'])
                    print(f"  🔒 PROTECTED: {user['login']} (prevent_destroy enabled)")

                    # Insert lifecycle block before closing brace
                    modified_block = user['full_block'].rstrip()
                    if modified_block.endswith('}'):
                        modified_block = modified_block[:-1]  # Remove closing brace
                        modified_block += "\n\n  lifecycle {\n    prevent_destroy = true\n  }\n}"

                    f.write(modified_block)
                    f.write("\n\n")
                else:
                    normal_users.append(user['login'])
                    print(f"  ✅ NORMAL: {user['login']} (standard management)")
                    f.write(user['full_block'])
                    f.write("\n\n")

        return {
            'total': len(users),
            'protected': len(protected_users),
            'normal': len(normal_users),
            'protected_logins': protected_users
        }

    def check_only(self, input_file: str, admin_logins: Set[str]) -> Dict:
        """Check which users are admins without modifying files"""
        users = self.parse_terraform_users(input_file)

        results = {
            'total': len(users),
            'admins': [],
            'non_admins': [],
            'safe_to_manage': True
        }

        print(f"\n📊 Analysis of {input_file}:")
        print(f"  Total users: {len(users)}")

        for user in users:
            if user['login'] in admin_logins:
                results['admins'].append(user['login'])
                results['safe_to_manage'] = False
                print(f"  ⚠️  ADMIN USER: {user['login']} (DANGEROUS to manage)")
            else:
                results['non_admins'].append(user['login'])
                print(f"  ✅ Regular user: {user['login']}")

        if results['admins']:
            print(f"\n⚠️  WARNING: {len(results['admins'])} super admin(s) found in Terraform config!")
            print("  Recommendation: Use --mode filter or --mode protect")
        else:
            print("\n✅ SAFE: No super admins found in Terraform config")

        return results


def main():
    parser = argparse.ArgumentParser(description='Protect super admin users from Terraform management')
    parser.add_argument('--input', required=True, help='Input Terraform user file')
    parser.add_argument('--output', help='Output filtered/protected file')
    parser.add_argument('--mode', choices=['check', 'filter', 'protect'], default='check',
                      help='check: analyze only, filter: remove admins, protect: add prevent_destroy')

    args = parser.parse_args()

    # Get credentials from environment
    api_token = os.getenv('OKTA_API_TOKEN')
    org_name = os.getenv('OKTA_ORG_NAME')
    base_url = os.getenv('OKTA_BASE_URL', 'okta.com')

    if not api_token or not org_name:
        print("❌ Error: OKTA_API_TOKEN and OKTA_ORG_NAME environment variables required")
        sys.exit(1)

    protector = OktaAdminProtector(org_name, base_url, api_token)

    try:
        # Get super admins from Okta
        admin_logins = protector.get_super_admins()

        if not admin_logins:
            print("⚠️  Warning: No super admins found. This might indicate an API issue.")

        print(f"\n📋 Found {len(admin_logins)} super admin user(s)")

        # Process based on mode
        if args.mode == 'check':
            results = protector.check_only(args.input, admin_logins)

            # Write summary to JSON
            summary_file = args.input.replace('.tf', '_admin_check.json')
            with open(summary_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Summary written to: {summary_file}")

            sys.exit(0 if results['safe_to_manage'] else 1)

        elif args.mode == 'filter':
            if not args.output:
                print("❌ Error: --output required for filter mode")
                sys.exit(1)

            results = protector.filter_terraform_file(args.input, args.output, admin_logins)
            print(f"\n✅ Filtered file written to: {args.output}")
            print(f"  Total users: {results['total']}")
            print(f"  Safe users: {results['safe']}")
            print(f"  Blocked admins: {results['blocked']}")

            if results['blocked_logins']:
                print(f"\n🛡️  Protected admin users:")
                for login in results['blocked_logins']:
                    print(f"    - {login}")

        elif args.mode == 'protect':
            if not args.output:
                print("❌ Error: --output required for protect mode")
                sys.exit(1)

            results = protector.add_lifecycle_protection(args.input, args.output, admin_logins)
            print(f"\n✅ Protected file written to: {args.output}")
            print(f"  Total users: {results['total']}")
            print(f"  Protected admins: {results['protected']}")
            print(f"  Normal users: {results['normal']}")

            if results['protected_logins']:
                print(f"\n🔒 Users with prevent_destroy:")
                for login in results['protected_logins']:
                    print(f"    - {login}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
