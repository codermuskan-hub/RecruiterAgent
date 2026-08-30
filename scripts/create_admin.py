#!/usr/bin/env python3
"""
System Administration Script: Create System Administrator
Usage: python scripts/create_admin.py [username] [full_name] [email] [password]
"""

import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from database.database import create_system_admin, init_db


def main():
    init_db()
    if len(sys.argv) == 5:
        username = sys.argv[1]
        full_name = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
    else:
        print("=== 🛡️ System Administrator Provisioning ===")
        username = input("Enter Admin Username (default: system_admin): ").strip() or "system_admin"
        full_name = input("Enter Admin Full Name (default: System Administrator): ").strip() or "System Administrator"
        email = input("Enter Admin Email (default: admin@techcorp.in): ").strip() or "admin@techcorp.in"
        password = input("Enter Admin Password (default: admin123): ").strip() or "admin123"

    ok, msg = create_system_admin(username, full_name, email, password)
    if ok:
        print(f"\n✅ {msg}")
        print(f"Role: Admin (Operations & Governance)")
        print(f"Username: {username}")
    else:
        print(f"\n⚠️ {msg}")


if __name__ == "__main__":
    main()
