# Onity OnPortal Pre-Install Tool

This batch script prepares a Windows system for **Onity OnPortal** installation by applying required network and firewall configurations automatically.

## What It Does

The script performs the following actions:

- Requests **Administrator privileges** if not already elevated
- **Disables IPv6** on all network adapters
- **Flushes the DNS cache**
- Creates **Windows Firewall rules** for TCP **Port 6543** (Inbound & Outbound)
- Enables **ICMP (Ping)** for network diagnostics
- Generates a **setup log on the Desktop** (`OnPortal_Setup_Log.txt`)

## Purpose

Ensures the system is properly configured for **Onity OnPortal communication** and avoids common network-related installation issues.

## Usage

1. Run `Onity_FirewallRules.bat`
2. Accept the **Administrator permission prompt**
3. Wait for the setup process to complete

After completion, the system will be ready for **Onity OnPortal installation**.

## Notes

- Some **EDR/Antivirus solutions** (e.g., CrowdStrike, SentinelOne) may still block port **6543**.
- If connectivity issues occur, check security software policies.
