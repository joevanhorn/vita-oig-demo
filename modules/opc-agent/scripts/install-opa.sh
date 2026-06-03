#!/bin/bash
# ==============================================================================
# OKTA PROVISIONING AGENT (OPA) INSTALLATION SCRIPT
# ==============================================================================
# Downloads and installs the Okta Provisioning Agent.
#
# Usage:
#   sudo ./install-opa.sh
#
# After installation, run:
#   sudo /opt/OktaProvisioningAgent/configure_agent.sh
# ==============================================================================

set -e

INSTALL_DIR="/opt/OktaProvisioningAgent"
DOWNLOAD_DIR="/installers/opc"
LOG_FILE="/var/log/opa-install.log"

# Okta Provisioning Agent download URL (tenant-specific)
DOWNLOAD_URL="https://taskvantage-admin.okta.com/artifacts/OPP/03.00.07/OktaProvisioningAgent-03.00.07-fd641e2.x86_64.rpm"
RPM_FILENAME="OktaProvisioningAgent-03.00.07.rpm"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"; exit 1; }

echo ""
log "=============================================="
log "Okta Provisioning Agent Installation"
log "=============================================="
echo ""

# Check root
[[ $EUID -ne 0 ]] && error "Run as root (sudo)"

# Check Java
log "Checking prerequisites..."
command -v java &>/dev/null || error "Java not installed. Run: sudo dnf install java-11-openjdk -y"
log "  Java: $(java -version 2>&1 | head -1)"

# Create download directory
mkdir -p "$DOWNLOAD_DIR"

# Check for existing RPM or download
RPM_FILE=$(ls "$DOWNLOAD_DIR"/OktaProvisioningAgent*.rpm 2>/dev/null | head -1)

if [[ -z "$RPM_FILE" ]]; then
    log "Downloading Okta Provisioning Agent..."
    log "  URL: $DOWNLOAD_URL"

    RPM_FILE="$DOWNLOAD_DIR/$RPM_FILENAME"

    if curl -fSL -o "$RPM_FILE" "$DOWNLOAD_URL" 2>&1; then
        log "  Downloaded: $RPM_FILE ($(du -h "$RPM_FILE" | cut -f1))"
    else
        error "Download failed. Check URL or network connectivity."
    fi
else
    log "Using existing RPM: $RPM_FILE"
fi

# Check existing installation
if [[ -d "$INSTALL_DIR" ]]; then
    warn "OPA already installed at $INSTALL_DIR"
    if systemctl is-active --quiet OktaProvisioningAgent 2>/dev/null; then
        log "  Service is running"
    fi
fi

# Install
log "Installing Okta Provisioning Agent..."
yum localinstall -y "$RPM_FILE" 2>&1 | tee -a "$LOG_FILE"

# Verify
[[ ! -f "$INSTALL_DIR/configure_agent.sh" ]] && error "Installation verification failed"

echo ""
log "=============================================="
log "Installation Complete!"
log "=============================================="
echo ""
echo -e "${GREEN}The agent is installed but NOT configured yet.${NC}"
echo ""
echo "To complete setup, run:"
echo ""
echo -e "  ${YELLOW}sudo /opt/OktaProvisioningAgent/configure_agent.sh${NC}"
echo ""
echo "This will open a browser for Okta authentication."
echo "Log in as an Okta admin to authorize the agent."
echo ""
echo "Useful commands:"
echo "  systemctl status OktaProvisioningAgent"
echo "  tail -f $INSTALL_DIR/logs/*.log"
echo ""
echo "JDBC connection info:"
echo "  cat /installers/connection-info.txt"
echo ""
