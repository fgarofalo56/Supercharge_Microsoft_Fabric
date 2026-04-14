# 📊 Security Diagrams Summary

This document provides an overview of the Mermaid diagrams added to SECURITY.md.

## Diagrams Added

### 1. Security Requirements by Environment (State Diagram)

**Location:** Security Architecture section, after Security Control Matrix

**Purpose:** Shows the progressive increase in security controls from Development through Test, Staging, to Production environments.

**Key Features:**
- 🔵 Development: Basic controls, local auth, test data
- 🟡 Test: Enhanced controls, Microsoft Entra ID, masked PII
- 🟠 Staging: Production-like controls, MFA, full encryption
- 🔴 Production: Maximum controls, CMK, 24/7 monitoring

**Color Scheme:**
- Blue (#2196F3): Info/Development
- Orange (#FF9800): Warning/Staging
- Green (#4CAF50): Success/Test progression
- Red (#F44336): Critical/Production

---

### 2. Data Classification Decision Tree (Flowchart)

**Location:** Data Protection section, after Data Classification table

**Purpose:** Provides a clear decision tree to help users classify data into the appropriate security category.

**Classification Levels:**
- 🔴 **RESTRICTED/PII**: SSN, card numbers, bank accounts
  - Customer-managed keys, field-level encryption, no export
  
- 🟠 **CONFIDENTIAL**: Player PII, win/loss records
  - RBAC, row-level security, export restrictions
  
- 🟡 **INTERNAL**: Operational metrics, KPIs
  - Standard RBAC, employee access only
  
- 🟢 **PUBLIC**: Marketing materials, public reports
  - No restrictions, open access

**Decision Flow:**
1. Contains PII? → Yes/No
2. Contains Regulated PII? → Yes (Restricted) / No (Continue)
3. Business Sensitive? → Yes (Confidential) / No (Continue)
4. Can be Publicly Shared? → Yes (Public) / No (Internal)

**Color Scheme:**
- Red (#F44336): Restricted data
- Orange (#FF9800): Confidential data
- Yellow (#FFC107): Internal data
- Green (#4CAF50): Public data
- Blue (#2196F3): Decision nodes

---

### 3. Authentication & Authorization Flow (Sequence Diagram)

**Location:** Identity and Access Management section, after Microsoft Entra ID Integration table

**Purpose:** Illustrates the complete authentication and authorization flow for accessing Microsoft Fabric resources.

**Flow Phases:**

**Phase 1 - Authentication (Blue Background):**
1. User navigates to Fabric
2. Redirect to Microsoft Entra ID login
3. Conditional Access evaluation
4. MFA challenge (if required)
5. JWT token generation

**Phase 2 - Authorization (Green Background):**
6. Token validation
7. RBAC permission check
8. Row-level security filters applied
9. Access granted/denied

**Phase 3 - Data Access (Orange Background):**
10. Request encryption keys from Key Vault
11. Query data with filters
12. Decrypt and return results
13. Audit logging
14. Display to user

**Participants:**
- 👤 User
- 🌐 Browser
- 📊 Fabric Portal
- 🔐 Microsoft Entra ID
- 🛡️ Conditional Access
- 📱 MFA Service
- ⚡ Fabric API
- 🔑 Key Vault
- 💾 Data Lake

**Color Scheme:**
- Blue (#2196F3): Authentication phase background
- Green (#4CAF50): Authorization phase background
- Orange (#FF9800): Data access phase background
- Actors and signals use consistent theme colors

---

## Rendering the Diagrams

### In GitHub
The diagrams will render automatically when viewing SECURITY.md on GitHub.

### In VS Code
Install the **Mermaid Preview** extension:
```bash
code --install-extension bierner.markdown-mermaid
```

### Online Preview
Use the official Mermaid Live Editor:
https://mermaid.live/

### Export Options
- **PNG/SVG**: Use Mermaid Live Editor or VS Code extensions
- **PDF**: Render in browser and print to PDF
- **Presentations**: Copy code into reveal.js or Marp slides

---

## Customization Notes

All diagrams use the specified color palette:
- **Security/Error**: #F44336 (red)
- **Warning**: #FF9800 (orange)
- **Success**: #4CAF50 (green)
- **Info**: #2196F3 (blue)

The diagrams include:
- ✅ Meaningful icons and emojis for visual clarity
- ✅ Comprehensive labels and descriptions
- ✅ Accessibility-friendly color contrasts
- ✅ Professional styling consistent with the document
- ✅ Detailed notes and annotations

---

## Integration with Documentation

These diagrams complement the existing:
- Defense in Depth flowchart (Security Architecture)
- Private Endpoint Architecture diagram (Network Security)
- Security Incident Workflow diagram (Incident Response)

Together, they provide comprehensive visual documentation of:
1. **What** security controls are applied (existing Defense in Depth)
2. **When** controls are applied (new Environment State diagram)
3. **How** to classify data (new Decision Tree)
4. **How** authentication works (new Sequence diagram)

---

> 📖 **Created:** 2025-01-21
> 🎨 **Diagram Tool:** Mermaid.js
> 🎯 **Purpose:** Enhanced security documentation with visual aids
