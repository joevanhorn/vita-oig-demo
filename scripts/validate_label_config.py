#!/usr/bin/env python3
"""
Validate label_mappings.json configuration file.

Usage:
    python3 scripts/validate_label_config.py <path-to-label_mappings.json>
"""

import json
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/validate_label_config.py <config-file>")
        sys.exit(1)

    config_file = sys.argv[1]

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Check required keys
    required_keys = ['labels', 'assignments']
    missing = [k for k in required_keys if k not in config]
    if missing:
        print(f"❌ Missing required keys: {', '.join(missing)}")
        sys.exit(1)

    print('✅ Required structure present')
    print('')
    print('**Configuration Summary:**')
    print(f'- Labels defined: {len(config.get("labels", {}))}')
    print(f'- Assignment categories: {len(config.get("assignments", {}))}')

    # Count total assignments
    total = sum(len(orns) for cat in config.get('assignments', {}).values() for orns in cat.values())
    print(f'- Total resource assignments: {total}')
    print('')

    # List labels
    print('**Labels:**')
    for label in config.get('labels', {}).keys():
        print(f'- {label}')
    print('')

    # Check ORN format
    print('**ORN Validation:**')
    invalid = []
    for category, labels in config.get('assignments', {}).items():
        for label, orns in labels.items():
            for orn in orns:
                if not orn.startswith('orn:'):
                    invalid.append(f'{category}/{label}: {orn}')

    if invalid:
        print('❌ Invalid ORN formats found:')
        for inv in invalid[:10]:
            print(f'  - {inv}')
        sys.exit(1)
    else:
        print('✅ All ORNs have valid format')

if __name__ == '__main__':
    main()
