[Home](../../index.md) > [Tutorials](../) > Networking & Connectivity

# 🌐 Tutorial 22: Networking and Connectivity

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center">

![Difficulty](https://img.shields.io/badge/Difficulty-Advanced-red?style=for-the-badge)
![Category](https://img.shields.io/badge/Category-Networking-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

---

## 🎯 Overview

This hands-on tutorial walks you through implementing enterprise networking for Microsoft Fabric, including Private Endpoints, ExpressRoute, VPN configurations, and multi-cloud connectivity. Essential for organizations with hybrid infrastructure or strict compliance requirements.

![Fabric Security Layers](https://learn.microsoft.com/en-us/fabric/security/media/security-overview/fabric-security-overview.svg)

*Source: [Microsoft Fabric Security Overview](https://learn.microsoft.com/en-us/fabric/security/security-overview)*

**Duration:** 3-4 hours
**Level:** Advanced
**Prerequisites:**
- Azure subscription with Owner or Network Contributor role
- Fabric workspace admin access
- Basic understanding of Azure networking
- Access to Azure CLI or PowerShell

---

## 📚 Learning Objectives

By the end of this tutorial, you will be able to:

- Configure Private Endpoints for Fabric
- Set up ExpressRoute for hybrid connectivity
- Implement Site-to-Site VPN
- Configure network security groups
- Enable multi-cloud shortcuts (S3, GCS)
- Meet gaming compliance network requirements

---

## 🔒 Part 1: Private Endpoints

### Step 1.1: Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         Microsoft Fabric            │
                    │  ┌─────────────────────────────────┐│
                    │  │      OneLake / Lakehouses       ││
                    │  └─────────────────────────────────┘│
                    │                  │                   │
                    │           Private Endpoint          │
                    └──────────────────┼──────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │           Private Link              │
                    │              Service                │
                    └──────────────────┼──────────────────┘
                                       │
    ┌──────────────────────────────────┼──────────────────────────────────┐
    │                        Customer VNet                                 │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
    │  │   Subnet    │    │   Subnet    │    │   Subnet (PE Subnet)    │ │
    │  │  (VMs/AKS)  │    │  (Gateway)  │    │    Private Endpoint     │ │
    │  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
    └─────────────────────────────────────────────────────────────────────┘
```

### Step 1.2: Create Virtual Network

```bash
# Variables
RESOURCE_GROUP="rg-fabric-networking"
LOCATION="eastus2"
VNET_NAME="vnet-fabric-hub"
VNET_ADDRESS="10.100.0.0/16"

# Create Resource Group
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Create Virtual Network
az network vnet create \
    --resource-group $RESOURCE_GROUP \
    --name $VNET_NAME \
    --address-prefix $VNET_ADDRESS \
    --location $LOCATION

# Create subnets
az network vnet subnet create \
    --resource-group $RESOURCE_GROUP \
    --vnet-name $VNET_NAME \
    --name "snet-private-endpoints" \
    --address-prefix "10.100.1.0/24" \
    --disable-private-endpoint-network-policies true

az network vnet subnet create \
    --resource-group $RESOURCE_GROUP \
    --vnet-name $VNET_NAME \
    --name "snet-gateway" \
    --address-prefix "10.100.2.0/27"

az network vnet subnet create \
    --resource-group $RESOURCE_GROUP \
    --vnet-name $VNET_NAME \
    --name "snet-compute" \
    --address-prefix "10.100.10.0/24"
```

### Step 1.3: Create Private DNS Zone

```bash
# Create Private DNS Zone for OneLake
az network private-dns zone create \
    --resource-group $RESOURCE_GROUP \
    --name "privatelink.dfs.fabric.microsoft.com"

# Link DNS zone to VNet
az network private-dns link vnet create \
    --resource-group $RESOURCE_GROUP \
    --zone-name "privatelink.dfs.fabric.microsoft.com" \
    --name "link-fabric-vnet" \
    --virtual-network $VNET_NAME \
    --registration-enabled false
```

### Step 1.4: Create Private Endpoint (Bicep)

```bicep
// private-endpoint.bicep

@description('Name of the Private Endpoint')
param privateEndpointName string = 'pe-fabric-onelake'

@description('VNet Resource ID')
param vnetId string

@description('Subnet name for Private Endpoint')
param subnetName string = 'snet-private-endpoints'

@description('Fabric Workspace ID')
param fabricWorkspaceId string

@description('Location')
param location string = resourceGroup().location

var privateDnsZoneName = 'privatelink.dfs.fabric.microsoft.com'
var subnetId = '${vnetId}/subnets/${subnetName}'

// Private Endpoint
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-06-01' = {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-connection'
        properties: {
          privateLinkServiceId: fabricWorkspaceId
          groupIds: [
            'onelake'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone Group
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-06-01' = {
  name: 'default'
  parent: privateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'onelake-dns'
        properties: {
          privateDnsZoneId: resourceId('Microsoft.Network/privateDnsZones', privateDnsZoneName)
        }
      }
    ]
  }
}

output privateEndpointId string = privateEndpoint.id
output privateIpAddress string = privateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
```

### Step 1.5: Verify Private Endpoint

```bash
# Check Private Endpoint status
az network private-endpoint show \
    --name "pe-fabric-onelake" \
    --resource-group $RESOURCE_GROUP \
    --query "provisioningState"

# Verify DNS resolution (from within VNet)
nslookup onelake.dfs.fabric.microsoft.com

# Expected: Should resolve to private IP (10.100.1.x)
```

---

## 🔌 Part 2: ExpressRoute Configuration

### Step 2.1: ExpressRoute Architecture

```
    ┌─────────────────┐         ┌─────────────────┐
    │  On-Premises    │         │    Microsoft    │
    │  Data Center    │         │     Cloud       │
    │                 │         │                 │
    │  ┌───────────┐  │         │  ┌───────────┐  │
    │  │  Router   │  │─────────│  │   MSEE    │  │
    │  │  (CE)     │  │   ER    │  │  Router   │  │
    │  └─────┬─────┘  │ Circuit │  └─────┬─────┘  │
    │        │        │         │        │        │
    │  ┌─────┴─────┐  │         │  ┌─────┴─────┐  │
    │  │  Network  │  │         │  │   Azure   │  │
    │  │  Devices  │  │         │  │   VNet    │  │
    │  └───────────┘  │         │  └───────────┘  │
    └─────────────────┘         └─────────────────┘
```

### Step 2.2: Create ExpressRoute Circuit

```bash
# Create ExpressRoute Circuit
az network express-route create \
    --resource-group $RESOURCE_GROUP \
    --name "er-fabric-circuit" \
    --provider "Equinix" \
    --peering-location "Chicago" \
    --bandwidth 1000 \
    --sku-family "MeteredData" \
    --sku-tier "Premium"

# Get Service Key (provide to connectivity provider)
az network express-route show \
    --resource-group $RESOURCE_GROUP \
    --name "er-fabric-circuit" \
    --query "serviceKey"
```

### Step 2.3: Create ExpressRoute Gateway

```bash
# Create public IP for gateway
az network public-ip create \
    --resource-group $RESOURCE_GROUP \
    --name "pip-er-gateway" \
    --sku "Standard" \
    --allocation-method "Static"

# Create ExpressRoute Gateway
az network vnet-gateway create \
    --resource-group $RESOURCE_GROUP \
    --name "ergw-fabric" \
    --vnet $VNET_NAME \
    --gateway-type "ExpressRoute" \
    --sku "Standard" \
    --public-ip-addresses "pip-er-gateway"

# Note: Gateway creation takes 30-45 minutes
```

### Step 2.4: Connect Circuit to Gateway

```bash
# Create connection (after circuit is provisioned)
az network vpn-connection create \
    --resource-group $RESOURCE_GROUP \
    --name "conn-er-fabric" \
    --vnet-gateway1 "ergw-fabric" \
    --express-route-circuit2 "/subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Network/expressRouteCircuits/er-fabric-circuit" \
    --connection-type "ExpressRoute"
```

### Step 2.5: Configure Private Peering

```bash
# Create private peering
az network express-route peering create \
    --resource-group $RESOURCE_GROUP \
    --circuit-name "er-fabric-circuit" \
    --peering-type "AzurePrivatePeering" \
    --peer-asn 65001 \
    --primary-peer-subnet "192.168.1.0/30" \
    --secondary-peer-subnet "192.168.2.0/30" \
    --vlan-id 100
```

---

## 🛡️ Part 3: VPN Gateway Configuration

### Step 3.1: Site-to-Site VPN Architecture

```
    ┌─────────────────┐                    ┌─────────────────┐
    │  On-Premises    │     IPsec/IKEv2    │     Azure       │
    │                 │        Tunnel       │                 │
    │  ┌───────────┐  │  ┌──────────────┐  │  ┌───────────┐  │
    │  │  VPN      │  │──│              │──│  │  VPN      │  │
    │  │  Device   │  │  │   Internet   │  │  │  Gateway  │  │
    │  └─────┬─────┘  │  └──────────────┘  │  └─────┬─────┘  │
    │        │        │                    │        │        │
    │  ┌─────┴─────┐  │                    │  ┌─────┴─────┐  │
    │  │  Local    │  │                    │  │   Azure   │  │
    │  │  Network  │  │                    │  │   VNet    │  │
    │  └───────────┘  │                    │  └───────────┘  │
    └─────────────────┘                    └─────────────────┘
```

### Step 3.2: Create VPN Gateway

```bash
# Create public IP
az network public-ip create \
    --resource-group $RESOURCE_GROUP \
    --name "pip-vpn-gateway" \
    --sku "Standard" \
    --allocation-method "Static"

# Create VPN Gateway (VpnGw2 for production)
az network vnet-gateway create \
    --resource-group $RESOURCE_GROUP \
    --name "vpngw-fabric" \
    --vnet $VNET_NAME \
    --gateway-type "Vpn" \
    --vpn-type "RouteBased" \
    --sku "VpnGw2" \
    --generation "Generation2" \
    --public-ip-addresses "pip-vpn-gateway"

# Note: Gateway creation takes 30-45 minutes
```

### Step 3.3: Create Local Network Gateway

```bash
# Define on-premises network
az network local-gateway create \
    --resource-group $RESOURCE_GROUP \
    --name "lng-onprem-datacenter" \
    --gateway-ip-address "203.0.113.50" \
    --local-address-prefixes "10.0.0.0/16" "172.16.0.0/16"
```

### Step 3.4: Create VPN Connection

```bash
# Create Site-to-Site connection
az network vpn-connection create \
    --resource-group $RESOURCE_GROUP \
    --name "conn-vpn-onprem" \
    --vnet-gateway1 "vpngw-fabric" \
    --local-gateway2 "lng-onprem-datacenter" \
    --shared-key "YourSecureSharedKey123!" \
    --connection-type "IPsec"

# Configure IKE policy (Phase 1)
az network vpn-connection ipsec-policy add \
    --resource-group $RESOURCE_GROUP \
    --connection-name "conn-vpn-onprem" \
    --dh-group "DHGroup14" \
    --ike-encryption "AES256" \
    --ike-integrity "SHA384" \
    --ipsec-encryption "AES256" \
    --ipsec-integrity "SHA256" \
    --pfs-group "PFS2048" \
    --sa-lifetime 28800 \
    --sa-max-size 102400000
```

### Step 3.5: On-Premises VPN Device Configuration

Example configuration for Cisco ASA:

```
! Cisco ASA Configuration for Azure VPN

crypto ikev2 policy 10
 encryption aes-256
 integrity sha384
 group 14
 prf sha384
 lifetime seconds 28800

crypto ikev2 enable outside

crypto ipsec ikev2 ipsec-proposal AZURE-PROPOSAL
 protocol esp encryption aes-256
 protocol esp integrity sha-256

crypto ipsec profile AZURE-PROFILE
 set ikev2 ipsec-proposal AZURE-PROPOSAL
 set security-association lifetime kilobytes 102400000
 set security-association lifetime seconds 3600

tunnel-group 20.185.xxx.xxx type ipsec-l2l
tunnel-group 20.185.xxx.xxx ipsec-attributes
 ikev2 remote-authentication pre-shared-key YourSecureSharedKey123!
 ikev2 local-authentication pre-shared-key YourSecureSharedKey123!

interface Tunnel1
 nameif azure-tunnel
 ip address 169.254.1.1 255.255.255.252
 tunnel source interface outside
 tunnel destination 20.185.xxx.xxx
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile AZURE-PROFILE

route azure-tunnel 10.100.0.0 255.255.0.0 169.254.1.2
```

---

## 🔐 Part 4: Network Security Groups

### Step 4.1: Create NSG for Fabric Access

```bash
# Create NSG
az network nsg create \
    --resource-group $RESOURCE_GROUP \
    --name "nsg-fabric-access"

# Allow outbound to Fabric (using Service Tags)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name "nsg-fabric-access" \
    --name "Allow-Fabric-Outbound" \
    --priority 100 \
    --direction Outbound \
    --access Allow \
    --protocol Tcp \
    --destination-address-prefixes "PowerBI" \
    --destination-port-ranges 443

# Allow outbound to Storage (for OneLake)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name "nsg-fabric-access" \
    --name "Allow-Storage-Outbound" \
    --priority 110 \
    --direction Outbound \
    --access Allow \
    --protocol Tcp \
    --destination-address-prefixes "Storage" \
    --destination-port-ranges 443

# Allow outbound to Microsoft Entra ID
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name "nsg-fabric-access" \
    --name "Allow-AzureAD-Outbound" \
    --priority 120 \
    --direction Outbound \
    --access Allow \
    --protocol Tcp \
    --destination-address-prefixes "AzureActiveDirectory" \
    --destination-port-ranges 443
```

### Step 4.2: Associate NSG with Subnet

```bash
az network vnet subnet update \
    --resource-group $RESOURCE_GROUP \
    --vnet-name $VNET_NAME \
    --name "snet-compute" \
    --network-security-group "nsg-fabric-access"
```

---

## ☁️ Part 5: Multi-Cloud Connectivity

### Step 5.1: AWS S3 Shortcut Configuration

```python
# In Fabric Notebook - Create S3 Shortcut

# Step 1: Create S3 connection (one-time setup in Fabric portal)
# Navigate: Workspace > Settings > Manage connections > New connection
# Connection type: Amazon S3
# Configure:
# - Access Key ID: <your-access-key>
# - Secret Access Key: <your-secret-key>
# - Region: us-east-1

# Step 2: Create shortcut via notebook
shortcut_config = {
    "path": "Files/external/aws-casino-data",
    "target": {
        "s3": {
            "connection_id": "<s3-connection-id>",
            "location": "s3://casino-data-lake/bronze/"
        }
    }
}

# Note: Shortcuts are created via UI or REST API
# This is for documentation purposes
```

### Step 5.2: Google Cloud Storage Shortcut

```python
# GCS Shortcut Configuration

# Step 1: Create GCS connection
# Navigate: Workspace > Settings > Manage connections > New connection
# Connection type: Google Cloud Storage
# Configure:
# - Service Account JSON key

# Step 2: Create shortcut
shortcut_config = {
    "path": "Files/external/gcs-analytics",
    "target": {
        "gcs": {
            "connection_id": "<gcs-connection-id>",
            "location": "gs://casino-analytics-bucket/exports/"
        }
    }
}
```

### Step 5.3: ADLS Gen2 Cross-Subscription

```python
# ADLS Gen2 shortcut (different subscription/tenant)

# Step 1: Configure cross-tenant access
# - Register app in target tenant
# - Grant Storage Blob Data Reader role

# Step 2: Create connection with service principal
# Navigate: Workspace > Settings > Manage connections > New connection
# Connection type: Azure Data Lake Storage Gen2
# Authentication: Service Principal
# Configure:
# - Tenant ID: <target-tenant-id>
# - Client ID: <app-client-id>
# - Client Secret: <app-client-secret>
# - Storage account: <storage-account-name>

# Step 3: Create shortcut
shortcut_config = {
    "path": "Files/external/partner-data",
    "target": {
        "adls": {
            "connection_id": "<adls-connection-id>",
            "location": "https://partnerstorage.dfs.core.windows.net/datalake/shared/"
        }
    }
}
```

---

## 🏛️ Part 6: Compliance Network Configuration

### Step 6.1: PCI-DSS Network Requirements

```bicep
// pci-dss-network.bicep
// PCI-DSS compliant network configuration

param location string = 'eastus2'
param environment string = 'prod'

// Dedicated VNet for cardholder data
resource pciVnet 'Microsoft.Network/virtualNetworks@2023-06-01' = {
  name: 'vnet-pci-${environment}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.200.0.0/16']
    }
    subnets: [
      {
        name: 'snet-cde'  // Cardholder Data Environment
        properties: {
          addressPrefix: '10.200.1.0/24'
          networkSecurityGroup: {
            id: cdeNsg.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-dmz'
        properties: {
          addressPrefix: '10.200.2.0/24'
          networkSecurityGroup: {
            id: dmzNsg.id
          }
        }
      }
    ]
  }
}

// CDE Network Security Group
resource cdeNsg 'Microsoft.Network/networkSecurityGroups@2023-06-01' = {
  name: 'nsg-cde-${environment}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'AllowAuthorizedInbound'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '10.200.2.0/24'  // DMZ only
          destinationAddressPrefix: '10.200.1.0/24'
          sourcePortRange: '*'
          destinationPortRange: '443'
        }
      }
    ]
  }
}

// Enable DDoS protection
resource ddosProtection 'Microsoft.Network/ddosProtectionPlans@2023-06-01' = {
  name: 'ddos-${environment}'
  location: location
  properties: {}
}
```

### Step 6.2: Gaming Compliance Network (NIGC)

```yaml
# Gaming Commission Network Requirements
# Document for audit purposes

network_segmentation:
  zones:
    - name: "Gaming Floor"
      subnet: "10.210.1.0/24"
      access: "Restricted to slot systems"

    - name: "Cage Operations"
      subnet: "10.210.2.0/24"
      access: "Financial transactions"

    - name: "Surveillance"
      subnet: "10.210.3.0/24"
      access: "Isolated - no external access"

    - name: "Analytics"
      subnet: "10.210.10.0/24"
      access: "Fabric Private Endpoint access"

firewall_rules:
  - source: "Gaming Floor"
    destination: "Analytics"
    port: 443
    protocol: "HTTPS"
    purpose: "Slot telemetry to Fabric"

  - source: "Cage Operations"
    destination: "Analytics"
    port: 443
    protocol: "HTTPS"
    purpose: "Transaction data to Fabric"

audit_requirements:
  - All network traffic logged
  - 90-day retention minimum
  - Real-time alerting for anomalies
  - Quarterly penetration testing
```

---

## 📊 Part 7: Monitoring and Troubleshooting

### Step 7.1: Network Watcher Setup

```bash
# Enable Network Watcher
az network watcher configure \
    --resource-group $RESOURCE_GROUP \
    --locations $LOCATION \
    --enabled true

# Enable NSG flow logs
az network watcher flow-log create \
    --resource-group $RESOURCE_GROUP \
    --name "flowlog-fabric-nsg" \
    --nsg "nsg-fabric-access" \
    --storage-account "stfabricnetlogs" \
    --enabled true \
    --retention 90
```

### Step 7.2: Connection Troubleshooting

```bash
# Test connectivity to Fabric endpoint
az network watcher test-connectivity \
    --resource-group $RESOURCE_GROUP \
    --source-resource "vm-test-client" \
    --dest-address "onelake.dfs.fabric.microsoft.com" \
    --dest-port 443

# Check VPN connection status
az network vpn-connection show \
    --resource-group $RESOURCE_GROUP \
    --name "conn-vpn-onprem" \
    --query "connectionStatus"

# Check ExpressRoute circuit status
az network express-route show \
    --resource-group $RESOURCE_GROUP \
    --name "er-fabric-circuit" \
    --query "circuitProvisioningState"
```

---

## ✅ Summary Checklist

### Private Endpoints
- [ ] Created VNet and subnets
- [ ] Created Private DNS Zone
- [ ] Deployed Private Endpoint
- [ ] Verified DNS resolution

### ExpressRoute
- [ ] Created ExpressRoute circuit
- [ ] Created ExpressRoute Gateway
- [ ] Configured private peering
- [ ] Connected circuit to gateway

### VPN Gateway
- [ ] Created VPN Gateway
- [ ] Created Local Network Gateway
- [ ] Configured VPN connection
- [ ] Configured on-premises device

### Security
- [ ] Created Network Security Groups
- [ ] Applied NSG to subnets
- [ ] Enabled flow logs
- [ ] Configured monitoring

### Multi-Cloud
- [ ] Configured S3 shortcut
- [ ] Configured GCS shortcut
- [ ] Configured cross-subscription ADLS

---

## 📖 Additional Resources

- [Networking Documentation](../../NETWORKING.md)
- [Private Endpoints for Fabric](https://learn.microsoft.com/en-us/fabric/security/security-private-links-overview)
- [ExpressRoute Documentation](https://learn.microsoft.com/en-us/azure/expressroute/)

---

## 🧭 Navigation

| Previous | Up | Next |
|----------|-----|------|
| [⬅️ 21-GeoAnalytics & ArcGIS](../21-geoanalytics-arcgis/README.md) | [📖 Tutorials Index](../index.md) | [23-SHIR & Data Gateways](../23-shir-data-gateways/README.md) ➡️ |

---

> 💬 **Questions or issues?** Open an issue in the [GitHub repository](https://github.com/frgarofa/Suppercharge_Microsoft_Fabric/issues).

---

[⬆️ Back to Top](#-tutorial-22-networking-and-connectivity) | [📚 Tutorials](../) | [🏠 Home](../../index.md)
