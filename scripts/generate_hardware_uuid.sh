#!/usr/bin/env bash
set -euo pipefail

# Detect OS type
OS="$(uname -s)"

# -------------------------
# Collect hardware identifiers (Linux / macOS / Windows via MSYS/Git Bash)
# -------------------------

cpu_serial="unknown"
machine_id="unknown"
mac_addr="unknown"

case "$OS" in
    Linux)
        # CPU serial (common on ARM SBCs, not available on many x86 CPUs)
        cpu_serial=$(grep -m1 'Serial' /proc/cpuinfo 2>/dev/null | awk '{print $3}' || echo "unknown")

        # Machine ID
        machine_id=$(cat /etc/machine-id 2>/dev/null || echo "unknown")

        # MAC address (first non-loopback)
        mac_addr=$(ip link show | awk '/link\/ether/ {print $2; exit}' 2>/dev/null || echo "unknown")
        ;;
    
    Darwin)
        # macOS CPU serial (IOPlatformSerialNumber)
        cpu_serial=$(ioreg -l | grep IOPlatformSerialNumber | awk -F\" '{print $4}' || echo "unknown")

        # Machine ID (similar to Linux machine-id)
        machine_id=$(ioreg -rd1 -c IOPlatformExpertDevice | awk -F\" '/IOPlatformUUID/ {print $4}' || echo "unknown")

        # MAC address (primary interface)
        mac_addr=$(ifconfig en0 2>/dev/null | awk '/ether/ {print $2}' || echo "unknown")
        ;;

    MINGW*|MSYS*|CYGWIN*)
        # Windows via Git Bash / MSYS
        # CPU serial number
        cpu_serial=$(wmic cpu get ProcessorId 2>/dev/null | awk 'NR==2' || echo "unknown")

        # Machine UUID
        machine_id=$(wmic csproduct get UUID 2>/dev/null | awk 'NR==2' || echo "unknown")

        # MAC address
        mac_addr=$(wmic nic where "MACAddress is not null" get MACAddress 2>/dev/null | awk 'NR==2' || echo "unknown")
        ;;

    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac


# -------------------------
# Generate fingerprint
# -------------------------
uuid_input="${cpu_serial}|${machine_id}|${mac_addr}"
fingerprint=$(printf "%s" "$uuid_input" | sha256sum 2>/dev/null | cut -d' ' -f1)

# macOS doesn’t have sha256sum
if [[ -z "${fingerprint}" || "${fingerprint}" == "" ]]; then
    fingerprint=$(printf "%s" "$uuid_input" | shasum -a 256 | awk '{print $1}')
fi


# -------------------------
# System details
# -------------------------
platform="$OS"
architecture=$(uname -m)
os_release="unknown"

if [[ -f /etc/os-release ]]; then
    os_release=$(grep -m1 PRETTY_NAME /etc/os-release | cut -d= -f2- | tr -d '"')
elif [[ "$OS" == "Darwin" ]]; then
    os_release=$(sw_vers -productName)  
    os_release="$os_release $(sw_vers -productVersion)"
elif [[ "$OS" =~ MINGW|MSYS|CYGWIN ]]; then
    os_release=$(wmic os get Caption | awk 'NR==2')
fi


# -------------------------
# Output
# -------------------------
echo "-----------------------------------"
echo "System Information"
echo "-----------------------------------"
echo "OS:            $os_release"
echo "Platform:      $platform"
echo "Architecture:  $architecture"
echo "CPU Serial:    $cpu_serial"
echo "Machine ID:    $machine_id"
echo "MAC Address:   $mac_addr"
echo "-----------------------------------"
echo "Your hardware-uuid:"
echo "$fingerprint"
echo "-----------------------------------"
