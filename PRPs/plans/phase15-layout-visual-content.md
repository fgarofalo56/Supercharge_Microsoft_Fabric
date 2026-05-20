# PRP: Phase 15 — Layout, Visual Impact & CSA-in-a-Box Content Reframing

> **Vision:** Transform the Supercharge Microsoft Fabric site from a flat documentation listing into a visually polished, navigable, enterprise-grade knowledge hub — applying the battle-tested patterns from the CSA-in-a-Box sister repository and porting its high-value content (industries, decision trees, compliance frameworks, research, runbooks) rewritten for Fabric.

## Summary

Phase 15 addresses three interconnected gaps: (1) navigation UX — the site uses `navigation.sections` + `navigation.expand` which forces every sidebar section open at all times, making the 300+ page site unnavigable; (2) visual impact — the site has zero images, no hero graphics, no Material grid cards, and minimal CSS beyond basic theme overrides; (3) content coverage — the CSA-in-a-Box repository contains 21 use cases, 6 industry pages, 13 decision trees, 14 compliance frameworks, 5 research papers, 14 runbooks, 5 role-based quickstarts, and 7 reference architectures that have direct Fabric equivalents but don't exist in this repo.

This PRP is structured for the **Parallel Worktree Orchestrator** skill — each work item touches non-overlapping files and can be executed by an independent headless Claude instance.

## User Story

**As an** enterprise architect, data engineer, or Fabric evaluator  
**I want** a polished documentation site with collapsible navigation, visual diagrams, decision trees, industry guidance, and compliance mappings  
**So that** I can navigate the 300+ pages efficiently, quickly find content relevant to my role and industry, and use visual aids to communicate architecture choices to stakeholders.

## Problem Statement

| Gap | Current State | Target State |
|-----|---------------|--------------|
| Navigation | `navigation.expand` forces all 300+ sidebar items open; no section indexes | Collapsible sidebar (remove `navigation.expand`), section index pages with `navigation.indexes` |
| Visual assets | Zero images in `docs/assets/` | Hero SVG, medallion-flow SVG, Mermaid decision trees, Material grid cards |
| Homepage | Custom `.hero`/`.grid` divs with hardcoded CSS | Material `grid cards` with icons, clickable architecture hero |
| Copilot chat | Basic rendering (no tables, no citations, no resize) | Port CSA-in-a-Box enhancements: table/citation/task-list rendering, resize handle, dark mode |
| Industries | None | 6 industry pages (Healthcare, Financial Services, Retail/CPG, Manufacturing, Energy, Telecom) |
| Decision trees | None | 5 interactive Mermaid decision trees |
| Compliance | None | 6 compliance framework mappings (FedRAMP, HIPAA, SOC 2, PCI-DSS, NIST 800-53, GDPR) |
| Role quickstarts | None | 5 role-based quickstart pages |
| Research | None | 3 research/white paper documents |
| Runbooks | None | 6 operational runbooks |
| Reference architectures | None | 4 reference architecture pages |

## Metadata

| Field | Value |
|-------|-------|
| Type | ENHANCEMENT + NEW_CAPABILITY |
| Complexity | HIGH |
| Systems Affected | mkdocs.yml, docs/stylesheets/, docs/javascripts/, docs/assets/, docs/index.md, docs/industries/ (new), docs/decisions/ (new), docs/compliance/ (new), docs/quickstarts/ (new), docs/research/ (new), docs/runbooks/ (new), docs/reference-architecture/ (new) |
| Dependencies | MkDocs Material 9.x, pymdownx.superfences (Mermaid), pymdownx.emoji |
| Estimated Workers | 10 parallel work items |
| Target Duration | 1-2 days (parallel execution) |
| Archon Project ID | `c0f96f03-5095-4704-a167-9a3f5a3e3ed1` |

---

## Mandatory Reading

Before implementing, every worker MUST understand:

1. **CSA-in-a-Box navigation config**: `navigation.tabs` + `navigation.indexes` WITHOUT `navigation.sections` or `navigation.expand` — this gives collapsible sidebar behavior
2. **Material grid cards**: Use `<div class="grid cards" markdown>` with Material icons (`:material-icon-name:{ .lg .middle }`) — NOT custom `.grid`/`.card` divs
3. **Section index pages**: When `navigation.indexes` is enabled, a folder's `index.md` becomes the landing page for that nav section
4. **Mermaid decision trees**: Use `flowchart TD` in fenced code blocks with `mermaid` language tag
5. **Hero SVG pattern**: Inline SVG wrapped in `<a>` tag with `.architecture-hero` CSS class
6. **Existing file structure**: Check `mkdocs.yml` nav structure — new sections must be added there

## Patterns to Mirror

- **CSA-in-a-Box homepage** (`docs/index.md`): Material grid cards, hero image, three-paradigm explanation
- **CSA-in-a-Box industry pages** (`docs/industries/financial-services.md`): Scope quote, scenario table, regulatory landscape, Mermaid data flow, getting-started steps
- **CSA-in-a-Box decision trees** (`docs/decisions/fabric-vs-databricks-vs-synapse.md`): Mermaid flowchart with per-recommendation detail, tradeoffs, anti-patterns
- **CSA-in-a-Box compliance** (`docs/compliance/`): NIST control families mapped to platform implementations
- **CSA-in-a-Box quickstarts** (`docs/quickstarts/`): Role-segmented onboarding with persona-specific paths

---

## Parallel Work Items

### Critical constraint

**File exclusivity**: Each work item lists its files explicitly. No file appears in more than one work item. The orchestrator validates this.

**mkdocs.yml is a shared file** — it must be in exactly ONE work item. Work Item 1 (Navigation Restructure) owns `mkdocs.yml` and adds ALL new nav entries for items 2-10 upfront with placeholder paths. Other workers create the actual files; the nav entries will resolve once all PRs merge.

---

### Work Item 1: `nav-restructure` — Navigation & mkdocs.yml Restructure

**Title:** Restructure navigation for collapsible sidebar and section indexes

**Description:**
Restructure the MkDocs Material navigation configuration to transform the site from a fully-expanded flat sidebar into a collapsible, tab-based navigation with section index pages.

Changes required:
1. In `mkdocs.yml` features: REMOVE `navigation.sections` and `navigation.expand`. ADD `navigation.indexes`. Keep `navigation.tabs`, `navigation.tabs.sticky`, `navigation.instant`, `navigation.tracking`, `navigation.top`, `navigation.footer`.
2. Add all new nav sections to `mkdocs.yml` nav tree — Industries, Decisions, Compliance, Quickstarts, Research, Runbooks, Reference Architecture. Group these under a top-level "Guides" tab.
3. Add `navigation.indexes` section index entries (e.g., `- index.md` as first item under each section).
4. Create section index files: `docs/features/index.md`, `docs/best-practices/index.md`, `docs/use-cases/index.md`, `docs/tutorials/index.md` using Material grid cards with icons and short descriptions linking to each child page.
5. Reorganize existing flat sections into logical groups under tabs.

Acceptance criteria:
- `navigation.expand` and `navigation.sections` are removed from mkdocs.yml
- `navigation.indexes` is added
- All new sections (industries, decisions, compliance, quickstarts, research, runbooks, reference-architecture) have nav entries
- Section index pages use Material `grid cards` pattern
- `mkdocs build` succeeds with no errors (warnings about missing files for future work items are acceptable)

**Files:**
```
mkdocs.yml
docs/features/index.md
docs/best-practices/index.md
docs/use-cases/index.md
docs/tutorials/index.md
docs/getting-started/index.md
```

**Validation commands:**
```bash
cd docs && python -c "import yaml; y=yaml.safe_load(open('../mkdocs.yml')); feats=y['theme']['features']; assert 'navigation.indexes' in feats; assert 'navigation.expand' not in feats; assert 'navigation.sections' not in feats; print('NAV CONFIG OK')"
```

**Max iterations:** 3

---

### Work Item 2: `visual-foundation` — CSS, Hero SVG & Homepage Redesign

**Title:** Visual foundation — hero SVG, docs.css, homepage Material grid cards

**Description:**
Create the visual foundation for the site: a hero architecture SVG, a `docs.css` stylesheet for hero/card/image styling, and redesign the homepage (`docs/index.md`) to use Material grid cards instead of custom `.hero`/`.grid`/`.card` divs.

Changes required:
1. Create `docs/assets/images/` directory structure.
2. Create `docs/assets/images/architecture-hero.svg` — an inline SVG showing the Fabric architecture: OneLake at center, Bronze/Silver/Gold medallion flow, Real-Time Intelligence, Direct Lake → Power BI, Purview governance overlay. Use Fabric brand colors (#0078D4 blue, #50E6FF cyan, #FFB900 amber). Aim for 800x400 viewport.
3. Create `docs/stylesheets/docs.css` with:
   - `.architecture-hero` class (full-width, max-width 1100px, centered, rounded corners, shadow, dark mode variant)
   - Hover affordance for linked hero images
   - Card grid gap tightening (`.md-typeset .grid.cards { gap: 0.75rem; }`)
   - Screenshot/diagram container class `.diagram-container`
4. Rewrite `docs/index.md` to use:
   - Clickable hero SVG image with `.architecture-hero` class
   - Material `grid cards` with `:material-*:` icons for "Start here" section
   - Three-paradigm explanation (OneLake + Medallion + Direct Lake) similar to CSA-in-a-Box's three-paradigm section
   - "Choose your path" navigation cards
   - Remove existing custom `.hero`, `.grid`, `.card` div patterns — use Material built-in patterns
5. Update `docs/stylesheets/extra.css` — remove the custom `.grid`/`.card` CSS classes that are being replaced by Material built-ins. Keep Fabric branding vars, admonitions, badges, and dark mode support.

Acceptance criteria:
- `docs/assets/images/architecture-hero.svg` exists and renders in browser
- `docs/stylesheets/docs.css` exists with `.architecture-hero` class
- `docs/index.md` uses Material `grid cards` pattern (no custom `.grid`/`.card` divs)
- Homepage has clickable hero SVG
- Extra CSS in `docs/stylesheets/extra.css` removes replaced `.grid`/`.card` classes
- `mkdocs build` succeeds

**Files:**
```
docs/assets/images/architecture-hero.svg
docs/stylesheets/docs.css
docs/index.md
docs/stylesheets/extra.css
```

**Validation commands:**
```bash
test -f docs/assets/images/architecture-hero.svg && echo "SVG EXISTS" || echo "MISSING SVG"
test -f docs/stylesheets/docs.css && echo "CSS EXISTS" || echo "MISSING CSS"
grep -q "grid cards" docs/index.md && echo "GRID CARDS OK" || echo "MISSING GRID CARDS"
grep -q "architecture-hero" docs/index.md && echo "HERO REF OK" || echo "MISSING HERO REF"
```

**Max iterations:** 3

---

### Work Item 3: `copilot-chat-enhance` — Copilot Chat Widget Enhancements

**Title:** Port CSA-in-a-Box copilot chat enhancements (tables, citations, resize, dark mode)

**Description:**
Enhance the copilot chat widget by porting features from the CSA-in-a-Box implementation. The current Fabric copilot widget has basic markdown rendering. The CSA-in-a-Box version has rich rendering (tables, task lists, blockquotes, citation superscripts, citation footer cards), a resizable panel with drag handle, full-page mode, XSS-hardened markdown parsing, highlight.js lazy loading for code blocks with copy buttons, and comprehensive dark mode support.

Changes required:
1. Rewrite `docs/javascripts/copilot-chat.js` to port from CSA-in-a-Box:
   - XSS-hardened markdown renderer: handle code blocks (fenced + inline), tables, task lists, blockquotes, headings, links, bold/italic, citations `[^n]`
   - highlight.js lazy loading for code syntax highlighting
   - Copy button on code blocks
   - Citation footer card builder (shows source references)
   - Panel resize drag handle (min 320px, max 75% viewport)
   - Full-page mode toggle
   - ndjson streaming with progressive rendering
   - Keep existing `window.COPILOT_CONFIG` override pattern (don't switch to hardcoded CONFIG)
   - SHA-256 token generation via SubtleCrypto
2. Rewrite `docs/stylesheets/copilot-chat.css` to port from CSA-in-a-Box:
   - Floating FAB button (`.copilot-fab`)
   - Resizable panel with drag handle
   - Message bubbles (user vs assistant)
   - Rich typography: `.copilot-table-wrap` for tables, task lists, blockquotes
   - Citation superscripts and footer cards
   - Full-page mode
   - Streaming caret animation
   - Copy buttons on code blocks
   - Comprehensive dark mode (`[data-md-color-scheme="slate"]` AND `prefers-color-scheme: dark`)
   - Responsive design (mobile breakpoints)
3. Update `docs/chat.md` to document the enhanced features with a Mermaid architecture diagram showing: User → Chat Widget → Azure Function → Azure OpenAI, with search index grounding.

Acceptance criteria:
- Chat widget renders tables, code blocks with syntax highlighting, task lists, and citations
- Panel is resizable via drag handle
- Full-page mode toggle works
- Dark mode styling matches `[data-md-color-scheme="slate"]`
- `docs/chat.md` has Mermaid architecture diagram
- No XSS vulnerabilities in markdown rendering (HTML tags escaped)

**Files:**
```
docs/javascripts/copilot-chat.js
docs/stylesheets/copilot-chat.css
docs/chat.md
```

**Validation commands:**
```bash
grep -q "copilot-fab" docs/stylesheets/copilot-chat.css && echo "FAB CLASS OK" || echo "MISSING FAB"
grep -q "resize" docs/stylesheets/copilot-chat.css && echo "RESIZE OK" || echo "MISSING RESIZE"
grep -q "highlight" docs/javascripts/copilot-chat.js && echo "HIGHLIGHT OK" || echo "MISSING HIGHLIGHT"
grep -q "mermaid" docs/chat.md && echo "MERMAID OK" || echo "MISSING MERMAID"
grep -cq "copilot-table" docs/stylesheets/copilot-chat.css && echo "TABLE STYLES OK" || echo "MISSING TABLE STYLES"
```

**Max iterations:** 4

---

### Work Item 4: `role-quickstarts` — Role-Based Quickstart Pages

**Title:** Create 5 role-based quickstart pages for Fabric personas

**Description:**
Create role-based quickstart pages that give each persona a tailored onboarding path through the documentation. Modeled after CSA-in-a-Box's `docs/quickstarts/` pattern but rewritten entirely for Microsoft Fabric.

Roles to cover:
1. **Data Engineer** — Medallion architecture, PySpark notebooks, Data Factory pipelines, Lakehouse setup
2. **BI Developer** — Direct Lake, Power BI semantic models, DAX, Paginated Reports, Scorecards
3. **Data Scientist** — AutoML, Spark ML, Semantic Link, Vector Database, AI Functions
4. **Platform Admin** — Capacity planning, RBAC, network security, monitoring, BCDR, workspace management
5. **Security Admin** — OneLake Security, Purview governance, CMK, audit logs, compliance frameworks

Each page should include:
- Persona description and typical day
- "Your first 30 minutes" guided path (links to 3-5 existing tutorials/docs)
- "Your first week" expanded path
- Key features table (feature name → doc link → why it matters for this role)
- Common pitfalls for this persona
- Material grid cards linking to relevant sections

Create `docs/quickstarts/index.md` as the section landing page with all 5 roles as grid cards.

Acceptance criteria:
- 6 files created (index + 5 roles)
- Each quickstart links to at least 5 existing docs pages
- Material grid cards used on index page
- No broken internal links (all referenced pages exist in the repo)

**Files:**
```
docs/quickstarts/index.md
docs/quickstarts/data-engineer.md
docs/quickstarts/bi-developer.md
docs/quickstarts/data-scientist.md
docs/quickstarts/platform-admin.md
docs/quickstarts/security-admin.md
```

**Validation commands:**
```bash
find docs/quickstarts -name "*.md" | wc -l | grep -q "6" && echo "6 FILES OK" || echo "WRONG FILE COUNT"
grep -l "grid cards" docs/quickstarts/index.md && echo "GRID CARDS OK" || echo "MISSING GRID CARDS"
```

**Max iterations:** 3

---

### Work Item 5: `decision-trees` — Interactive Mermaid Decision Trees

**Title:** Create 5 interactive Mermaid decision trees for Fabric architecture choices

**Description:**
Create interactive decision tree pages using Mermaid `flowchart TD` diagrams, modeled after CSA-in-a-Box's `docs/decisions/` pattern. Each page has a TL;DR, Mermaid decision tree, per-recommendation detail sections with tradeoffs and anti-patterns, and links to relevant docs.

Decision trees to create:
1. **Lakehouse vs Warehouse vs SQL Database** — When to use each Fabric storage engine
2. **ETL vs ELT vs Streaming** — Data movement strategy selection
3. **Direct Lake vs Import vs DirectQuery** — Power BI connectivity mode selection
4. **Fabric vs Databricks vs Synapse** — Platform selection (adapted from CSA-in-a-Box but rewritten for Fabric-first perspective)
5. **Workspace Topology** — Single vs multi-workspace vs multi-capacity architecture

Create `docs/decisions/index.md` as section landing page.

Each decision tree page must include:
- TL;DR (3-sentence summary)
- "When this question comes up" section
- Mermaid `flowchart TD` diagram with clear branching logic
- Per-recommendation sections: When, Why, Tradeoffs (cost, latency, compliance, skill match), Anti-patterns
- Related links to existing docs

Acceptance criteria:
- 6 files created (index + 5 decision trees)
- Each has a valid Mermaid `flowchart TD` diagram
- Each recommendation section has Tradeoffs and Anti-patterns
- Links reference existing feature/best-practice docs

**Files:**
```
docs/decisions/index.md
docs/decisions/lakehouse-warehouse-sqldb.md
docs/decisions/etl-elt-streaming.md
docs/decisions/direct-lake-import-directquery.md
docs/decisions/fabric-databricks-synapse.md
docs/decisions/workspace-topology.md
```

**Validation commands:**
```bash
find docs/decisions -name "*.md" | wc -l | grep -q "6" && echo "6 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/decisions/lakehouse-warehouse-sqldb.md docs/decisions/etl-elt-streaming.md docs/decisions/direct-lake-import-directquery.md docs/decisions/fabric-databricks-synapse.md docs/decisions/workspace-topology.md; do grep -q "flowchart TD" "$f" && echo "$f MERMAID OK" || echo "$f MISSING MERMAID"; done
```

**Max iterations:** 3

---

### Work Item 6: `industry-pages` — Commercial Industry Verticals for Fabric

**Title:** Create 6 industry pages rewritten for Microsoft Fabric

**Description:**
Create industry-specific guidance pages adapted from CSA-in-a-Box's `docs/industries/` format but completely rewritten for Microsoft Fabric capabilities. Each page follows the CSA-in-a-Box industry page template: scope quote, scenario table, regulatory landscape, Mermaid data flow diagram, reference architecture variations, getting-started steps.

Industries to cover (each rewritten for Fabric, NOT Azure PaaS):
1. **Healthcare** — Patient analytics, clinical trials, FHIR data, HIPAA compliance, Direct Lake for clinical dashboards
2. **Financial Services** — Fraud detection, risk analytics, regulatory reporting, PCI-DSS, real-time transaction monitoring via RTI
3. **Retail & CPG** — Demand forecasting, supply chain visibility, customer 360, point-of-sale streaming
4. **Manufacturing** — IoT telemetry, predictive maintenance, quality analytics, Digital Twin Builder integration
5. **Energy & Utilities** — Smart grid analytics, outage prediction, renewable forecasting, NERC CIP compliance
6. **Telecommunications** — Network performance, churn prediction, CDR analytics, 5G capacity planning

Create `docs/industries/index.md` as section landing page with grid cards.

Each page must include:
- Industry scope quote
- 4-6 scenario table rows (Scenario | Fabric Pattern | Latency Target | Key Features)
- Regulatory landscape table (Framework | Applicability | Fabric Controls)
- Mermaid data flow diagram (source → Bronze → Silver → Gold → BI)
- "Why Fabric for [Industry]" section
- "Getting started" steps with links to existing tutorials/features
- Cross-references to existing best-practices and features docs

Acceptance criteria:
- 7 files created (index + 6 industries)
- Each industry page has Mermaid diagram, scenario table, regulatory table
- Grid cards on index page
- Links reference existing docs (features, best-practices, tutorials)

**Files:**
```
docs/industries/index.md
docs/industries/healthcare.md
docs/industries/financial-services.md
docs/industries/retail-cpg.md
docs/industries/manufacturing.md
docs/industries/energy-utilities.md
docs/industries/telecommunications.md
```

**Validation commands:**
```bash
find docs/industries -name "*.md" | wc -l | grep -q "7" && echo "7 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/industries/healthcare.md docs/industries/financial-services.md docs/industries/retail-cpg.md docs/industries/manufacturing.md docs/industries/energy-utilities.md docs/industries/telecommunications.md; do grep -q "mermaid" "$f" && echo "$f MERMAID OK" || echo "$f MISSING MERMAID"; done
grep -q "grid cards" docs/industries/index.md && echo "INDEX GRID OK" || echo "MISSING GRID"
```

**Max iterations:** 3

---

### Work Item 7: `compliance-frameworks` — Compliance Framework Mappings

**Title:** Create 6 compliance framework mapping documents for Fabric

**Description:**
Create compliance framework mapping pages showing how Microsoft Fabric controls satisfy regulatory requirements. Adapted from CSA-in-a-Box's `docs/compliance/` pattern but mapped to Fabric-native controls (OneLake Security, Purview, CMK, audit logs, workspace identity, network security) instead of Azure PaaS services.

Frameworks to cover:
1. **NIST 800-53** — Control families (AC, AU, CM, IA, SC, SI) mapped to Fabric implementations
2. **FedRAMP** — Fabric's path to FedRAMP authorization, current status, gap analysis
3. **HIPAA** — PHI handling in Fabric, BAA requirements, encryption, audit trails
4. **SOC 2 Type II** — Trust service criteria mapped to Fabric controls
5. **PCI-DSS** — Cardholder data environment in Fabric, network segmentation, encryption
6. **GDPR** — Data subject rights, data residency, right to deletion in OneLake

Create `docs/compliance/index.md` as section landing page with grid cards.

Each page must include:
- Framework overview and applicability to Fabric
- Control mapping table (Control ID | Control Name | Fabric Implementation | Evidence)
- Shared responsibility model (Microsoft vs Customer)
- Gap analysis / limitations
- Implementation checklist
- Links to relevant best-practices docs (CMK, audit logs, RBAC, network security)

Acceptance criteria:
- 7 files created (index + 6 frameworks)
- Each has control mapping table with at least 10 controls
- Shared responsibility section in each
- Links to existing best-practices docs

**Files:**
```
docs/compliance/index.md
docs/compliance/nist-800-53.md
docs/compliance/fedramp.md
docs/compliance/hipaa.md
docs/compliance/soc2.md
docs/compliance/pci-dss.md
docs/compliance/gdpr.md
```

**Validation commands:**
```bash
find docs/compliance -name "*.md" | wc -l | grep -q "7" && echo "7 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/compliance/nist-800-53.md docs/compliance/fedramp.md docs/compliance/hipaa.md docs/compliance/soc2.md docs/compliance/pci-dss.md docs/compliance/gdpr.md; do grep -q "Shared Responsibility\|shared responsibility" "$f" && echo "$f SHARED RESP OK" || echo "$f MISSING SHARED RESP"; done
grep -q "grid cards" docs/compliance/index.md && echo "INDEX GRID OK" || echo "MISSING GRID"
```

**Max iterations:** 3

---

### Work Item 8: `research-whitepapers` — Research & White Papers

**Title:** Create 3 research/white paper documents for Fabric

**Description:**
Create research-grade documents adapted from CSA-in-a-Box's `docs/research/` pattern but focused on Microsoft Fabric. These are longer-form documents (3,000-5,000 words each) that provide analytical depth beyond feature documentation.

Documents to create:
1. **Enterprise Data Platform Comparison 2026** — Fabric vs Databricks vs Snowflake vs Synapse feature matrix, TCO comparison, maturity assessment, migration considerations. Include comparison tables, Mermaid architecture diagrams, and decision guidance.
2. **AI Readiness Assessment for Fabric** — Framework for evaluating an organization's readiness to adopt Fabric AI capabilities (Copilot, AutoML, Semantic Link, Data Agents, AI Functions). Includes maturity model, assessment questionnaire, and implementation roadmap.
3. **Data Mesh Maturity Model on Fabric** — How to implement Data Mesh principles using Fabric constructs (workspaces as domains, OneLake as federated storage, Purview as governance, data products via lakehouses). Includes maturity levels, assessment criteria, and migration path from centralized to mesh.

Create `docs/research/index.md` as section landing page.

Acceptance criteria:
- 4 files created (index + 3 papers)
- Each paper is 3,000+ words
- Each includes at least one Mermaid diagram
- Each includes comparison or assessment tables
- Links to existing feature and best-practice docs

**Files:**
```
docs/research/index.md
docs/research/enterprise-data-platform-comparison.md
docs/research/ai-readiness-assessment.md
docs/research/data-mesh-maturity-model.md
```

**Validation commands:**
```bash
find docs/research -name "*.md" | wc -l | grep -q "4" && echo "4 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/research/enterprise-data-platform-comparison.md docs/research/ai-readiness-assessment.md docs/research/data-mesh-maturity-model.md; do wc -w < "$f" | awk '{if ($1 >= 2000) print "'"$f"' WORD COUNT OK"; else print "'"$f"' TOO SHORT: " $1 " words"}'; done
```

**Max iterations:** 4

---

### Work Item 9: `operational-runbooks` — Fabric Operational Runbooks

**Title:** Create 6 operational runbooks for Fabric administration

**Description:**
Create operational runbooks for day-to-day Fabric administration. These are procedural documents with step-by-step instructions, decision trees, and escalation paths. Adapted from CSA-in-a-Box's `docs/runbooks/` pattern but for Fabric-native operations.

Runbooks to create:
1. **Capacity Throttling Response** — Detecting throttling, root cause analysis, smoothing/rejection behavior, capacity scaling, CU optimization
2. **Failed Refresh Triage** — Semantic model refresh failures, pipeline failures, notebook failures, Dataflow Gen2 failures — diagnosis and recovery steps
3. **Data Quality Incident** — Detecting quality degradation, impact assessment, quarantine procedures, stakeholder communication, remediation
4. **Security Incident Response** — Unauthorized access detection, audit log investigation, credential rotation, Purview alert triage
5. **Disaster Recovery Execution** — Regional failover procedure, OneLake replication verification, capacity redeployment, data validation
6. **Cost Spike Investigation** — CU consumption anomaly detection, workload identification, burst vs sustained analysis, optimization actions

Create `docs/runbooks/index.md` as section landing page.

Each runbook must include:
- Trigger conditions (when to use this runbook)
- Severity classification
- Step-by-step procedure with numbered steps
- Mermaid flowchart for decision points
- Escalation path
- Post-incident review checklist
- Links to relevant monitoring/observability docs

Acceptance criteria:
- 7 files created (index + 6 runbooks)
- Each has numbered step-by-step procedure
- Each has Mermaid flowchart
- Each has escalation path
- Grid cards on index page

**Files:**
```
docs/runbooks/index.md
docs/runbooks/capacity-throttling.md
docs/runbooks/failed-refresh-triage.md
docs/runbooks/data-quality-incident.md
docs/runbooks/security-incident-response.md
docs/runbooks/disaster-recovery-execution.md
docs/runbooks/cost-spike-investigation.md
```

**Validation commands:**
```bash
find docs/runbooks -name "*.md" | wc -l | grep -q "7" && echo "7 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/runbooks/capacity-throttling.md docs/runbooks/failed-refresh-triage.md docs/runbooks/data-quality-incident.md docs/runbooks/security-incident-response.md docs/runbooks/disaster-recovery-execution.md docs/runbooks/cost-spike-investigation.md; do grep -q "mermaid" "$f" && echo "$f MERMAID OK" || echo "$f MISSING MERMAID"; done
grep -q "grid cards" docs/runbooks/index.md && echo "INDEX GRID OK" || echo "MISSING GRID"
```

**Max iterations:** 3

---

### Work Item 10: `reference-architecture` — Reference Architecture Pages

**Title:** Create 4 reference architecture pages with Mermaid diagrams

**Description:**
Create reference architecture pages showing production-grade Fabric deployments for different scales and patterns. Each page includes a Mermaid architecture diagram, component descriptions, sizing guidance, and implementation notes.

Architectures to create:
1. **Small/Medium Enterprise** — Single capacity, 2-3 workspaces (dev/test/prod), OneLake medallion, Direct Lake Power BI. For teams of 5-20 data practitioners.
2. **Large Enterprise Multi-Domain** — Multiple capacities, domain workspaces (Data Mesh), Purview governance hub, CI/CD via fabric-cicd, network isolation. For teams of 50+.
3. **Hybrid Cloud (Fabric + Azure PaaS)** — Fabric for analytics/BI + Azure services for what Fabric doesn't cover (AKS for custom apps, Azure SQL for OLTP, Event Hubs for high-volume streaming). Integration patterns via Mirroring, Shortcuts, and Dataflow Gen2.
4. **Real-Time Analytics** — Eventstream → Eventhouse (KQL) → Real-Time Dashboard + Data Activator alerts. For IoT, gaming, financial tick data, and operational monitoring.

Create `docs/reference-architecture/index.md` as section landing page.

Each page must include:
- Architecture overview (1 paragraph)
- Mermaid architecture diagram (component boxes with connections)
- Component table (Component | Fabric Item | Purpose | Sizing Notes)
- Capacity sizing guidance (SKU recommendation based on data volume/user count)
- Network architecture notes
- Cost estimation framework
- "Deploy this architecture" section linking to existing tutorials and IaC
- Tradeoffs and limitations

Acceptance criteria:
- 5 files created (index + 4 architectures)
- Each has Mermaid architecture diagram
- Each has component table and sizing guidance
- Grid cards on index page
- Links to existing tutorials, features, and infra docs

**Files:**
```
docs/reference-architecture/index.md
docs/reference-architecture/small-medium-enterprise.md
docs/reference-architecture/large-enterprise-multi-domain.md
docs/reference-architecture/hybrid-cloud.md
docs/reference-architecture/real-time-analytics.md
```

**Validation commands:**
```bash
find docs/reference-architecture -name "*.md" | wc -l | grep -q "5" && echo "5 FILES OK" || echo "WRONG FILE COUNT"
for f in docs/reference-architecture/small-medium-enterprise.md docs/reference-architecture/large-enterprise-multi-domain.md docs/reference-architecture/hybrid-cloud.md docs/reference-architecture/real-time-analytics.md; do grep -q "mermaid" "$f" && echo "$f MERMAID OK" || echo "$f MISSING MERMAID"; done
grep -q "grid cards" docs/reference-architecture/index.md && echo "INDEX GRID OK" || echo "MISSING GRID"
```

**Max iterations:** 3

---

## Orchestrator Manifest

```json
{
  "repo_root": "E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric",
  "base_branch": "main",
  "work_items": [
    {
      "id": "nav-restructure",
      "title": "Navigation & mkdocs.yml Restructure",
      "description": "Restructure MkDocs Material navigation: remove navigation.expand and navigation.sections, add navigation.indexes. Create section index pages for features/, best-practices/, use-cases/, tutorials/, getting-started/ using Material grid cards. Add all new nav sections (industries, decisions, compliance, quickstarts, research, runbooks, reference-architecture) to mkdocs.yml under a top-level Guides tab. This work item OWNS mkdocs.yml exclusively.",
      "files": [
        "mkdocs.yml",
        "docs/features/index.md",
        "docs/best-practices/index.md",
        "docs/use-cases/index.md",
        "docs/tutorials/index.md",
        "docs/getting-started/index.md"
      ],
      "validation_commands": [
        "cd E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric && python -c \"import yaml; y=yaml.safe_load(open('mkdocs.yml')); feats=y['theme']['features']; assert 'navigation.indexes' in feats; assert 'navigation.expand' not in feats; assert 'navigation.sections' not in feats; print('NAV CONFIG OK')\""
      ],
      "max_iterations": 3
    },
    {
      "id": "visual-foundation",
      "title": "Visual Foundation — Hero SVG, docs.css, Homepage Redesign",
      "description": "Create visual foundation: (1) docs/assets/images/architecture-hero.svg — inline SVG showing Fabric architecture with OneLake, medallion flow, RTI, Direct Lake, Power BI, Purview. Use Fabric brand colors (#0078D4, #50E6FF, #FFB900). (2) docs/stylesheets/docs.css with .architecture-hero class (full-width, max-width 1100px, rounded corners, shadow, dark mode). (3) Rewrite docs/index.md to use Material grid cards with :material-*: icons instead of custom .hero/.grid/.card divs. Add clickable hero SVG. (4) Update docs/stylesheets/extra.css to remove replaced .grid/.card CSS. Keep branding vars, admonitions, badges.",
      "files": [
        "docs/assets/images/architecture-hero.svg",
        "docs/stylesheets/docs.css",
        "docs/index.md",
        "docs/stylesheets/extra.css"
      ],
      "validation_commands": [
        "test -f E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/assets/images/architecture-hero.svg && echo 'SVG EXISTS' || echo 'MISSING SVG'",
        "test -f E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/stylesheets/docs.css && echo 'CSS EXISTS' || echo 'MISSING CSS'",
        "grep -q 'grid cards' E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/index.md && echo 'GRID CARDS OK' || echo 'MISSING GRID CARDS'"
      ],
      "max_iterations": 3
    },
    {
      "id": "copilot-chat-enhance",
      "title": "Copilot Chat Widget Enhancements",
      "description": "Enhance copilot chat widget by porting CSA-in-a-Box features. Rewrite docs/javascripts/copilot-chat.js with: XSS-hardened markdown renderer (tables, task lists, blockquotes, citations, code blocks with fencing), highlight.js lazy loading, copy buttons on code blocks, citation footer cards, panel resize drag handle (min 320px, max 75vw), full-page mode toggle, ndjson streaming with progressive rendering. Keep window.COPILOT_CONFIG override pattern. Rewrite docs/stylesheets/copilot-chat.css with: .copilot-fab floating button, resizable panel, message bubbles, .copilot-table-wrap for tables, citation styles, dark mode for [data-md-color-scheme=slate], responsive breakpoints, streaming caret animation. Update docs/chat.md with Mermaid architecture diagram.",
      "files": [
        "docs/javascripts/copilot-chat.js",
        "docs/stylesheets/copilot-chat.css",
        "docs/chat.md"
      ],
      "validation_commands": [
        "grep -q 'copilot-fab' E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/stylesheets/copilot-chat.css && echo 'FAB OK' || echo 'MISSING FAB'",
        "grep -q 'resize' E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/stylesheets/copilot-chat.css && echo 'RESIZE OK' || echo 'MISSING RESIZE'",
        "grep -q 'highlight' E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/javascripts/copilot-chat.js && echo 'HIGHLIGHT OK' || echo 'MISSING HIGHLIGHT'"
      ],
      "max_iterations": 4
    },
    {
      "id": "role-quickstarts",
      "title": "Role-Based Quickstart Pages",
      "description": "Create 5 role-based quickstart pages + index in docs/quickstarts/. Roles: data-engineer (medallion, PySpark, pipelines, Lakehouse), bi-developer (Direct Lake, Power BI, DAX, Paginated Reports), data-scientist (AutoML, Spark ML, Semantic Link, Vector DB, AI Functions), platform-admin (capacity, RBAC, network, monitoring, BCDR, workspaces), security-admin (OneLake Security, Purview, CMK, audit logs, compliance). Each page: persona description, 30-min guided path, first-week path, key features table, common pitfalls, Material grid cards. Index page uses grid cards for all 5 roles.",
      "files": [
        "docs/quickstarts/index.md",
        "docs/quickstarts/data-engineer.md",
        "docs/quickstarts/bi-developer.md",
        "docs/quickstarts/data-scientist.md",
        "docs/quickstarts/platform-admin.md",
        "docs/quickstarts/security-admin.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/quickstarts -name '*.md' | wc -l | grep -q '6' && echo '6 FILES OK' || echo 'WRONG FILE COUNT'",
        "grep -q 'grid cards' E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/quickstarts/index.md && echo 'GRID CARDS OK' || echo 'MISSING GRID CARDS'"
      ],
      "max_iterations": 3
    },
    {
      "id": "decision-trees",
      "title": "Interactive Mermaid Decision Trees",
      "description": "Create 5 decision tree pages + index in docs/decisions/. Trees: lakehouse-warehouse-sqldb (Fabric storage engine selection), etl-elt-streaming (data movement strategy), direct-lake-import-directquery (Power BI connectivity mode), fabric-databricks-synapse (platform selection, Fabric-first perspective), workspace-topology (single vs multi-workspace vs multi-capacity). Each page: TL;DR, 'When this comes up' section, Mermaid flowchart TD diagram, per-recommendation sections with When/Why/Tradeoffs (cost, latency, compliance, skill match)/Anti-patterns, Related links. Index page with grid cards.",
      "files": [
        "docs/decisions/index.md",
        "docs/decisions/lakehouse-warehouse-sqldb.md",
        "docs/decisions/etl-elt-streaming.md",
        "docs/decisions/direct-lake-import-directquery.md",
        "docs/decisions/fabric-databricks-synapse.md",
        "docs/decisions/workspace-topology.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/decisions -name '*.md' | wc -l | grep -q '6' && echo '6 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/decisions/lakehouse-warehouse-sqldb.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/decisions/fabric-databricks-synapse.md; do grep -q 'flowchart TD' \"$f\" && echo \"$f MERMAID OK\" || echo \"$f MISSING MERMAID\"; done"
      ],
      "max_iterations": 3
    },
    {
      "id": "industry-pages",
      "title": "Commercial Industry Verticals for Fabric",
      "description": "Create 6 industry pages + index in docs/industries/. Industries: healthcare (HIPAA, FHIR, Direct Lake clinical dashboards), financial-services (fraud detection, PCI-DSS, RTI transaction monitoring), retail-cpg (demand forecasting, customer 360, POS streaming), manufacturing (IoT, predictive maintenance, Digital Twin Builder), energy-utilities (smart grid, outage prediction, NERC CIP), telecommunications (network performance, churn, CDR analytics). Each page: scope quote, scenario table (Scenario|Fabric Pattern|Latency|Key Features), regulatory landscape table, Mermaid data flow diagram (source→Bronze→Silver→Gold→BI), 'Why Fabric' section, getting-started steps. Index with grid cards.",
      "files": [
        "docs/industries/index.md",
        "docs/industries/healthcare.md",
        "docs/industries/financial-services.md",
        "docs/industries/retail-cpg.md",
        "docs/industries/manufacturing.md",
        "docs/industries/energy-utilities.md",
        "docs/industries/telecommunications.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/industries -name '*.md' | wc -l | grep -q '7' && echo '7 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/industries/healthcare.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/industries/financial-services.md; do grep -q 'mermaid' \"$f\" && echo \"$f MERMAID OK\" || echo \"$f MISSING MERMAID\"; done"
      ],
      "max_iterations": 3
    },
    {
      "id": "compliance-frameworks",
      "title": "Compliance Framework Mappings for Fabric",
      "description": "Create 6 compliance framework pages + index in docs/compliance/. Frameworks: nist-800-53 (AC, AU, CM, IA, SC, SI control families mapped to Fabric), fedramp (Fabric FedRAMP path, current status, gap analysis), hipaa (PHI handling, BAA, encryption, audit), soc2 (trust service criteria mapping), pci-dss (cardholder data, network segmentation, encryption), gdpr (data subject rights, residency, right to deletion). Each page: framework overview, control mapping table (Control ID|Control Name|Fabric Implementation|Evidence), shared responsibility model, gap analysis, implementation checklist, links to best-practices. Index with grid cards.",
      "files": [
        "docs/compliance/index.md",
        "docs/compliance/nist-800-53.md",
        "docs/compliance/fedramp.md",
        "docs/compliance/hipaa.md",
        "docs/compliance/soc2.md",
        "docs/compliance/pci-dss.md",
        "docs/compliance/gdpr.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/compliance -name '*.md' | wc -l | grep -q '7' && echo '7 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/compliance/nist-800-53.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/compliance/hipaa.md; do grep -qi 'shared responsibility' \"$f\" && echo \"$f SHARED RESP OK\" || echo \"$f MISSING SHARED RESP\"; done"
      ],
      "max_iterations": 3
    },
    {
      "id": "research-whitepapers",
      "title": "Research & White Papers for Fabric",
      "description": "Create 3 research/white paper docs + index in docs/research/. Papers: enterprise-data-platform-comparison (Fabric vs Databricks vs Snowflake vs Synapse feature matrix, TCO comparison, maturity assessment, 3000+ words), ai-readiness-assessment (framework for evaluating AI readiness for Fabric Copilot/AutoML/Semantic Link/Data Agents, maturity model, assessment questionnaire, 3000+ words), data-mesh-maturity-model (Data Mesh on Fabric: workspaces as domains, OneLake federated storage, Purview governance, maturity levels, 3000+ words). Each includes Mermaid diagrams and comparison tables. Index with grid cards.",
      "files": [
        "docs/research/index.md",
        "docs/research/enterprise-data-platform-comparison.md",
        "docs/research/ai-readiness-assessment.md",
        "docs/research/data-mesh-maturity-model.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/research -name '*.md' | wc -l | grep -q '4' && echo '4 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/research/enterprise-data-platform-comparison.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/research/ai-readiness-assessment.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/research/data-mesh-maturity-model.md; do wc -w < \"$f\" | awk '{if ($1 >= 2000) print \"'\"$f\"' WORD COUNT OK\"; else print \"'\"$f\"' TOO SHORT: \" $1 \" words\"}'; done"
      ],
      "max_iterations": 4
    },
    {
      "id": "operational-runbooks",
      "title": "Fabric Operational Runbooks",
      "description": "Create 6 operational runbooks + index in docs/runbooks/. Runbooks: capacity-throttling (detecting throttling, smoothing/rejection, CU optimization), failed-refresh-triage (semantic model/pipeline/notebook/Dataflow Gen2 failures), data-quality-incident (quality degradation detection, quarantine, remediation), security-incident-response (unauthorized access, audit log investigation, credential rotation), disaster-recovery-execution (regional failover, OneLake replication, capacity redeployment), cost-spike-investigation (CU anomaly detection, workload identification, optimization). Each: trigger conditions, severity, numbered steps, Mermaid flowchart, escalation path, post-incident checklist. Index with grid cards.",
      "files": [
        "docs/runbooks/index.md",
        "docs/runbooks/capacity-throttling.md",
        "docs/runbooks/failed-refresh-triage.md",
        "docs/runbooks/data-quality-incident.md",
        "docs/runbooks/security-incident-response.md",
        "docs/runbooks/disaster-recovery-execution.md",
        "docs/runbooks/cost-spike-investigation.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/runbooks -name '*.md' | wc -l | grep -q '7' && echo '7 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/runbooks/capacity-throttling.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/runbooks/security-incident-response.md; do grep -q 'mermaid' \"$f\" && echo \"$f MERMAID OK\" || echo \"$f MISSING MERMAID\"; done"
      ],
      "max_iterations": 3
    },
    {
      "id": "reference-architecture",
      "title": "Reference Architecture Pages",
      "description": "Create 4 reference architecture pages + index in docs/reference-architecture/. Architectures: small-medium-enterprise (single capacity, 2-3 workspaces, OneLake medallion, Direct Lake, 5-20 users), large-enterprise-multi-domain (multi-capacity Data Mesh, Purview hub, fabric-cicd CI/CD, network isolation, 50+ users), hybrid-cloud (Fabric + Azure PaaS: AKS, Azure SQL, Event Hubs with Mirroring/Shortcuts/Dataflow Gen2 integration), real-time-analytics (Eventstream→Eventhouse KQL→RT Dashboard + Data Activator). Each: overview paragraph, Mermaid architecture diagram, component table (Component|Fabric Item|Purpose|Sizing), capacity sizing guidance, network notes, cost estimation, 'Deploy this' section with tutorial/IaC links, tradeoffs. Index with grid cards.",
      "files": [
        "docs/reference-architecture/index.md",
        "docs/reference-architecture/small-medium-enterprise.md",
        "docs/reference-architecture/large-enterprise-multi-domain.md",
        "docs/reference-architecture/hybrid-cloud.md",
        "docs/reference-architecture/real-time-analytics.md"
      ],
      "validation_commands": [
        "find E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/reference-architecture -name '*.md' | wc -l | grep -q '5' && echo '5 FILES OK' || echo 'WRONG FILE COUNT'",
        "for f in E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/reference-architecture/small-medium-enterprise.md E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric/docs/reference-architecture/hybrid-cloud.md; do grep -q 'mermaid' \"$f\" && echo \"$f MERMAID OK\" || echo \"$f MISSING MERMAID\"; done"
      ],
      "max_iterations": 3
    }
  ],
  "config": {
    "max_workers": 5,
    "worker_timeout_seconds": 2400,
    "permission_mode": "auto",
    "cleanup_on_success": false,
    "create_prs": true,
    "pr_base_branch": "main"
  }
}
```

---

## Execution Order

All 10 work items are independent — they can run in parallel with `max_workers: 5`, meaning 2 batches of 5 workers each.

**Batch 1 (5 parallel):**
1. `nav-restructure` — Owns mkdocs.yml, creates section indexes
2. `visual-foundation` — Hero SVG, docs.css, homepage redesign
3. `copilot-chat-enhance` — Chat widget enhancement
4. `role-quickstarts` — 5 role-based quickstart pages
5. `decision-trees` — 5 interactive decision trees

**Batch 2 (5 parallel):**
6. `industry-pages` — 6 industry verticals
7. `compliance-frameworks` — 6 compliance mappings
8. `research-whitepapers` — 3 research papers
9. `operational-runbooks` — 6 operational runbooks
10. `reference-architecture` — 4 reference architectures

## Post-Merge Integration

After all 10 PRs merge, a single integration pass is needed to:
1. Verify `mkdocs build` succeeds with all new files
2. Spot-check internal cross-links between new sections
3. Run `mkdocs serve` and visually verify navigation, hero image, and copilot chat
4. Update `CHANGELOG.md` with Phase 15 summary

This integration pass is NOT a parallel work item — it runs after all PRs merge.

---

## File Inventory

| Work Item | New Files | Modified Files | Total |
|-----------|-----------|----------------|-------|
| nav-restructure | 5 | 1 (mkdocs.yml) | 6 |
| visual-foundation | 2 | 2 (index.md, extra.css) | 4 |
| copilot-chat-enhance | 0 | 3 (chat.js, chat.css, chat.md) | 3 |
| role-quickstarts | 6 | 0 | 6 |
| decision-trees | 6 | 0 | 6 |
| industry-pages | 7 | 0 | 7 |
| compliance-frameworks | 7 | 0 | 7 |
| research-whitepapers | 4 | 0 | 4 |
| operational-runbooks | 7 | 0 | 7 |
| reference-architecture | 5 | 0 | 5 |
| **Total** | **49** | **6** | **55** |

No file appears in more than one work item.

---

## Cost Estimation

| Work Item | Complexity | Est. Duration | Est. Cost |
|-----------|-----------|---------------|-----------|
| nav-restructure | Medium | 10-15 min | $1.00-$2.00 |
| visual-foundation | Medium | 10-15 min | $1.00-$2.00 |
| copilot-chat-enhance | Complex | 15-25 min | $2.00-$4.00 |
| role-quickstarts | Medium | 10-15 min | $1.00-$2.00 |
| decision-trees | Medium | 10-15 min | $1.00-$2.00 |
| industry-pages | Medium-Complex | 12-20 min | $1.50-$3.00 |
| compliance-frameworks | Medium-Complex | 12-20 min | $1.50-$3.00 |
| research-whitepapers | Complex | 15-25 min | $2.00-$4.00 |
| operational-runbooks | Medium | 10-15 min | $1.00-$2.00 |
| reference-architecture | Medium | 10-15 min | $1.00-$2.00 |
| **Total** | | **~60-90 min** | **~$13-$26** |

With `max_workers: 5`, wall-clock time is approximately 25-50 minutes (two batches).

---

## Acceptance Criteria

- [ ] All 55 files created or modified
- [ ] `mkdocs build` succeeds with no errors
- [ ] Navigation sidebar is collapsible (not forced-expanded)
- [ ] Homepage has clickable hero SVG and Material grid cards
- [ ] Copilot chat renders tables, code blocks with highlighting, and citations
- [ ] All section index pages use Material grid cards
- [ ] All decision trees have valid Mermaid `flowchart TD` diagrams
- [ ] All industry pages have scenario tables and Mermaid data flow diagrams
- [ ] All compliance pages have control mapping tables and shared responsibility sections
- [ ] All research papers are 3,000+ words
- [ ] All runbooks have numbered procedures and Mermaid flowcharts
- [ ] All reference architectures have Mermaid diagrams and component tables
- [ ] No file overlaps between work items
- [ ] All 10 PRs created and mergeable
