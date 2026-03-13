# Onity Enterprise Toolkit

![OS](https://img.shields.io/badge/OS-Windows_10%20%7C%2011-blue?style=flat-square)
![Language](https://img.shields.io/badge/Script-Batch%20%7C%20PowerShell%20%7C%20Python-success?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square)

**Migration Notice:** This repository supersedes and replaces the legacy `Onity-Onportal` project. All modern automation tools, compiled executables, and future Python applications will be maintained here. For older, standalone PowerShell scripts or historical reference, please visit the [Legacy Repository](https://github.com/deadboy18/Onity-Onportal).

---

## Overview

A comprehensive suite of automation scripts, network configuration utilities, and deployment resources designed for **Onity OnPortal** enterprise environments. 

These tools are engineered to assist IT administrators and vendor support teams in streamlining fresh installations, resolving service communication failures, and developing custom Property Management System (PMS) integrations.

## Repository Structure

```text
Onity-Enterprise-Toolkit/
├── README.md                           
├── Network-Setup/
│   └── Onity_FirewallRules.bat         
├── Service-Management/
│   ├── OnPortal-Service-Manager.bat         
│   └── OnPortal-Service-Manager.exe         
├── PMS-Integration-App/
│   ├── onity9.py                       
│   └── template_hotel_config.json      
└── Resources/
    └── Download_Links.md              

```

## Component Details & Usage

### 1. Network Setup

**File:** `Network-Setup/Onity_FirewallRules.bat`
An automated pre-installation script that configures the Windows environment for OnPortal deployment. Executing this file will automatically elevate privileges, disable IPv6 (to prevent localhost routing conflicts), flush the DNS cache, open TCP Port 6543, and enable ICMP (Ping) across Domain, Private, and Public network profiles.

### 2. Service Management

**Files:** `Service-Management/OnPortal-Service-Manager.bat` (or `.exe`)
An interactive, CLI-based graphical utility to force-restart critical Onity services without requiring manual intervention via `services.msc`. It provides options to safely restart the **OnPortal Node Service** (standard PMS communication) and the **OnPortal IoT Service** (utilized in properties integrated with external Energy Management Systems like InnComm).

*Note: The `.bat` version utilizes a polyglot wrapper to seamlessly trigger an administrative PowerShell session upon execution.*

**Quick Run (Web Execution)**
For IT administrators who prefer to run the utility directly from memory without downloading local files, open an elevated PowerShell terminal and execute the following command:

```powershell
irm "https://raw.githubusercontent.com/deadboy18/Onity-Enterprise-Toolkit/main/Service%20Management/OnPortal-Service-Manager.ps1" | iex
```

### 3. Software Installers & Documentation

Due to GitHub repository size limits, all official OnPortal executables (v1.6 through v3.0.7), DirectKey toolkits, Bluegiga drivers, and official installation manuals are hosted on external secure mirrors.

Please navigate to the **`Resources/Download_Links.md`** file in this repository to access the categorized Google Drive web directories and Mediafire offline archives.

## Roadmap: PMS Integration Application

Currently in active development within the `PMS-Integration-App/` directory is a standalone Python application. This tool utilizes a modern graphical user interface to interact directly with the Onity PMS protocol.

It is designed for advanced reading, encoding, and bulk management of hotel key cards. A sanitized `template_hotel_config.json` is provided to allow other IT teams to map their specific property network parameters and encoder hostnames prior to deployment.

## Acknowledgments

Special thanks to **Kernwuzhere1979** for their invaluable technical assistance in researching the Onity service architecture and identifying the IoT/EMS dependencies that made these orchestration tools possible.

## Disclaimer

This is an independent, community-driven repository and is not officially affiliated with, endorsed by, or supported by Onity. These utilities were developed to assist IT professionals during real-world deployments. Please use them at your own risk. It is strictly advised to back up your system configurations and database directories prior to making network or service modifications.
