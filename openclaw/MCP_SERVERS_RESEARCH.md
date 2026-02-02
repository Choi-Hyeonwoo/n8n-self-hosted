# MCP Servers Research for n8n + OpenClaw + Obsidian Stack

> Research date: 2026-02-02
> Stack: n8n Cloud (mangd.app.n8n.cloud) | OpenClaw VPS + Telegram Bot | Google Drive Obsidian Vault | GICS Entity Classification

---

## Table of Contents

1. [n8n Native MCP Support](#1-n8n-native-mcp-support)
2. [n8n MCP Companion Servers](#2-n8n-mcp-companion-servers)
3. [Obsidian MCP Servers](#3-obsidian-mcp-servers)
4. [Google Drive / Workspace MCP Servers](#4-google-drive--workspace-mcp-servers)
5. [Finance / Stock Data MCP Servers](#5-finance--stock-data-mcp-servers)
6. [Web Scraping / Research MCP Servers](#6-web-scraping--research-mcp-servers)
7. [Telegram MCP Servers](#7-telegram-mcp-servers)
8. [Knowledge Graph / Memory MCP Servers](#8-knowledge-graph--memory-mcp-servers)
9. [Transport Proxies (stdio <-> SSE bridge)](#9-transport-proxies)
10. [Recommended Stack](#10-recommended-stack-for-this-setup)

---

## 1. n8n Native MCP Support

n8n has **built-in MCP support** via two nodes (requires n8n v1.88.0+):

### MCP Server Trigger Node
- Exposes n8n workflows as MCP tools that external AI agents can discover and call
- URL format: `https://your-n8n.app.n8n.cloud/mcp/{path}`
- Transport: SSE and Streamable HTTP (no stdio)
- Auth: Bearer token or custom header auth
- Connect tool nodes to the trigger; external agents call them via MCP

### MCP Client Tool Node
- Connects to external MCP servers from within n8n workflows
- Configure with an SSE endpoint URL
- n8n AI agents can discover and call tools from any MCP server
- Set env var `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true` for community tools

### Instance-Level MCP Access
- Per-workflow toggle: Workflow menu > Settings > "Available in MCP"
- Exposes entire workflows as callable MCP tools

### How to use with your setup
1. Create workflows in mangd.app.n8n.cloud with MCP Server Trigger
2. Connect tools (Google Drive sync, Obsidian push, GICS lookup, etc.)
3. OpenClaw agent connects as MCP client via SSE to call n8n tools
4. Or: n8n uses MCP Client Tool to call external MCP servers (finance, web scraping)

**Docs:**
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/
- https://docs.n8n.io/advanced-ai/accessing-n8n-mcp-server/
- https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/

---

## 2. n8n MCP Companion Servers

### A) n8n-MCP (czlonkowski) -- TOP PICK
- **GitHub:** https://github.com/czlonkowski/n8n-mcp
- **Stars:** ~13,000
- **What:** Gives AI assistants deep knowledge of n8n's 1,084 nodes, their properties, operations, and documentation. Helps Claude/GPT build n8n workflows.
- **Why useful:** OpenClaw can use this to understand and generate n8n workflows programmatically. Pairs with the Telegram bot for "build me a workflow" commands.
- **Install:**
  ```bash
  npx n8n-mcp                           # local
  # or hosted: https://dashboard.n8n-mcp.com (free: 100 calls/day)
  # or Docker
  ```
- **Config (Claude Desktop):**
  ```json
  {
    "mcpServers": {
      "n8n-mcp": {
        "command": "npx",
        "args": ["-y", "n8n-mcp"]
      }
    }
  }
  ```

### B) n8n-mcp-server (illuminaresolutions)
- **GitHub:** https://github.com/illuminaresolutions/n8n-mcp-server
- **Stars:** ~119
- **What:** MCP server for managing n8n instances -- workflows, executions, credentials, tags, users.
- **Why useful:** Lets OpenClaw manage the n8n Cloud instance via MCP (list workflows, trigger executions, audit credentials).
- **Install:**
  ```bash
  npm install -g @illuminaresolutions/n8n-mcp-server
  ```
- **Config:**
  ```json
  {
    "mcpServers": {
      "n8n": {
        "command": "n8n-mcp-server",
        "env": {
          "N8N_BASE_URL": "https://mangd.app.n8n.cloud",
          "N8N_API_KEY": "your-api-key"
        }
      }
    }
  }
  ```

---

## 3. Obsidian MCP Servers

### A) obsidian-mcp-server (cyanheads) -- TOP PICK
- **GitHub:** https://github.com/cyanheads/obsidian-mcp-server
- **Stars:** ~349
- **What:** Full-featured Obsidian vault MCP server: read, write, search notes, manage tags, frontmatter, wiki-links. Bridges to Obsidian Local REST API plugin.
- **Why useful:** Direct MCP access to your Google Drive Obsidian vault. OpenClaw can read/write MOC notes, update YAML frontmatter, search across vault, manage GICS entity tags.
- **Install:**
  ```bash
  npx obsidian-mcp-server
  ```
- **Requires:** Obsidian Local REST API plugin running in Obsidian
- **Key tools:** `read_note`, `update_note`, `search_vault`, `manage_frontmatter`, `add_tag`, `remove_tag`, `list_directory`, `delete_note`

### B) obsidian-mcp-plugin (aaronsb) -- KNOWLEDGE GRAPH AWARE
- **GitHub:** https://github.com/aaronsb/obsidian-mcp-plugin
- **Stars:** ~219
- **What:** Obsidian plugin that runs an MCP server directly inside Obsidian. AI sees your vault as an interconnected knowledge graph, not isolated files.
- **Why useful:** Best for MOC pattern navigation. AI can traverse wiki-links, do multi-hop graph traversal, semantic search, and even run Dataview queries.
- **Install:** Via BRAT plugin: add `aaronsb/obsidian-mcp-plugin`
- **Key features:** Graph navigation, semantic search, Dataview DQL queries, multi-hop traversal, batch operations

### C) obsidian-mcp-tools (jacksteamdev)
- **GitHub:** https://github.com/jacksteamdev/obsidian-mcp-tools
- **Stars:** ~561
- **What:** Obsidian plugin + local MCP server with semantic search and Templater integration
- **Why useful:** Semantic (meaning-based) search across vault. Execute Obsidian templates via AI with dynamic parameters.
- **Install:** Obsidian Community Plugins > search "MCP Tools" > click "Install Server" in settings

### D) mcp-obsidian (bitbonsai) -- ZERO DEPENDENCY
- **GitHub:** https://github.com/bitbonsai/mcp-obsidian
- **Stars:** Available
- **What:** Lightweight, zero-dependency MCP server for safe Obsidian vault access. No Obsidian plugins required -- works directly with vault files.
- **Why useful:** Since your vault is on Google Drive, this can read the raw markdown files without needing Obsidian running. Good for VPS-side access.
- **Install:** Direct file-based access, no Obsidian instance needed

---

## 4. Google Drive / Workspace MCP Servers

### A) google-workspace-mcp (aaronsb) -- TOP PICK
- **GitHub:** https://github.com/aaronsb/google-workspace-mcp
- **Stars:** ~116
- **What:** Full Google Workspace MCP: Drive (upload/download/search/permissions), Gmail, Calendar, Contacts. OAuth 2.0 with automatic token refresh.
- **Why useful:** OpenClaw gets full Workspace access. Sync Obsidian vault files, send Gmail alerts, manage calendar events, search Drive for research docs.
- **Install:** Docker-based
  ```json
  {
    "mcpServers": {
      "google-workspace": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "-v", "/path/to/tokens:/app/tokens", "google-workspace-mcp"]
      }
    }
  }
  ```

### B) gdrive-mcp-server (felores)
- **GitHub:** https://github.com/felores/gdrive-mcp-server
- **Stars:** ~63
- **What:** Google Drive search, list, read with smart format conversion (Docs->Markdown, Sheets->CSV, Slides->text).
- **Why useful:** Read-only Drive access. Converts Google Docs to Markdown natively -- perfect for reading Obsidian notes synced to Drive.
- **Install:**
  ```bash
  git clone https://github.com/felores/gdrive-mcp-server.git
  cd gdrive-mcp-server && npm install && npm run build
  ```

### C) google-drive-mcp (piotr-agier)
- **GitHub:** https://github.com/piotr-agier/google-drive-mcp
- **Stars:** Available
- **What:** Full CRUD for Drive, Docs, Sheets, Slides. Path-based navigation (`/Work/Projects`), Shared Drives support.
- **Why useful:** Full read-write access to Drive vault. Create/update Obsidian notes from AI, manage folder structure.

### D) google-docs-mcp (a-bonus)
- **GitHub:** https://github.com/a-bonus/google-docs-mcp
- **Stars:** Available
- **What:** Full Google Docs, Sheets & Drive access with formatting control.
- **Why useful:** If you need to create formatted Google Docs reports from GICS research data.

---

## 5. Finance / Stock Data MCP Servers

### A) Financial Modeling Prep MCP Server (imbenrabi) -- TOP PICK for GICS
- **GitHub:** https://github.com/imbenrabi/Financial-Modeling-Prep-MCP-Server
- **Stars:** ~107
- **What:** 253+ financial tools across 24 categories. Real-time quotes, financial statements, technical indicators, ESG scores, insider trading, congressional trading, social sentiment.
- **Why useful:** Most comprehensive for GICS entity enrichment. FMP API includes sector/industry classification data. Covers fundamentals, technicals, and alternative data all in one MCP.
- **Install:**
  ```bash
  npm install -g financial-modeling-prep-mcp-server
  # or Docker:
  docker run -p 8080:8080 -e FMP_ACCESS_TOKEN=your_token ghcr.io/imbenrabi/financial-modeling-prep-mcp-server:latest
  ```
- **Requires:** FMP API key (free tier available at https://financialmodelingprep.com/)

### B) Yahoo Finance MCP (Alex2Yang97)
- **GitHub:** https://github.com/Alex2Yang97/yahoo-finance-mcp
- **Stars:** ~199
- **What:** Comprehensive Yahoo Finance data: historical prices, financials, options, analyst recs, news, insider transactions.
- **Why useful:** Free data source (no API key needed via yfinance). Good for quick stock lookups and enriching GICS entities with price/fundamentals.
- **Install:**
  ```bash
  git clone https://github.com/Alex2Yang97/yahoo-finance-mcp.git
  cd yahoo-finance-mcp && uv sync
  ```

### C) MaverickMCP (wshobson) -- TOP PICK for Technical Analysis
- **GitHub:** https://github.com/wshobson/maverick-mcp
- **Stars:** ~337
- **What:** 39+ financial analysis tools. Pre-seeded 520 S&P 500 stocks. VectorBT backtesting with 15+ strategies and ML algorithms. 20+ technical indicators.
- **Why useful:** Advanced technical analysis and backtesting. Pairs with GICS classification to analyze sector/industry performance patterns.
- **Install:**
  ```bash
  git clone https://github.com/wshobson/maverick-mcp.git
  cd maverick-mcp && uv sync && cp .env.example .env
  make dev
  ```

### D) Financial Datasets MCP Server
- **GitHub:** https://github.com/financial-datasets/mcp-server
- **Stars:** ~745
- **What:** Income statements, balance sheets, cash flow, stock prices, crypto data via Financial Datasets API.
- **Why useful:** Clean financial statement data for fundamental analysis of GICS-classified entities.
- **Requires:** Financial Datasets API key

### E) Alpha Vantage MCP (Official)
- **URL:** https://mcp.alphavantage.co/
- **What:** Official Alpha Vantage MCP. Real-time and historical stock data, forex, crypto, economic indicators.
- **Why useful:** Established, reliable data source. Sector performance endpoint useful for GICS analysis.
- **Requires:** Alpha Vantage API key (free tier: 25 requests/day)

---

## 6. Web Scraping / Research MCP Servers

### A) Bright Data MCP -- TOP PICK
- **GitHub:** https://github.com/brightdata/brightdata-mcp
- **Stars:** ~2,000
- **What:** All-in-one web access: search, scrape (as markdown), browser automation. 60+ specialized tools. Enterprise-grade anti-bot/unblocking.
- **Why useful:** Research any public company, SEC filings, news articles, analyst reports. Scrape financial data that is not in APIs. Free tier: 5,000 requests/month.
- **Install (hosted, no setup):**
  ```json
  {
    "mcpServers": {
      "brightdata": {
        "url": "https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN"
      }
    }
  }
  ```
- **Install (local):**
  ```bash
  npx @brightdata/mcp
  ```

### B) Firecrawl MCP Server (Official)
- **GitHub:** https://github.com/firecrawl/firecrawl-mcp-server
- **Stars:** ~5,400
- **What:** Web scraping, crawling, URL discovery, content extraction, deep research. Auto-retry with rate limiting.
- **Why useful:** Crawl entire company websites, extract structured data, deep research on GICS entities. Self-hosted option available.
- **Install:**
  ```bash
  npx -y firecrawl-mcp
  ```
- **Requires:** FIRECRAWL_API_KEY (or self-host)
- **Tools:** `scrape`, `batch_scrape`, `map`, `crawl`, `search`, `extract`

### C) Crawl4AI MCP Server (sadiuysal) -- SELF-HOSTED / FREE
- **GitHub:** https://github.com/sadiuysal/crawl4ai-mcp-server
- **Stars:** Available
- **What:** Lightweight, self-hosted, free alternative to Firecrawl. Tools: `scrape`, `crawl`, `crawl_site`, `crawl_sitemap`.
- **Why useful:** Deploy on VPS alongside OpenClaw. No API costs. Adaptive crawling.
- **Install:**
  ```bash
  git clone https://github.com/sadiuysal/crawl4ai-mcp-server.git
  cd crawl4ai-mcp-server && pip install -r requirements.txt
  ```

### D) Official Fetch Server (Anthropic)
- **GitHub:** https://github.com/modelcontextprotocol/servers (under src/fetch)
- **Stars:** 77,800 (parent repo)
- **What:** Basic web content fetching and conversion for LLM usage. Part of the official MCP reference servers.
- **Install:**
  ```bash
  npx -y @modelcontextprotocol/server-fetch
  ```

---

## 7. Telegram MCP Servers

### A) telegram-mcp (chigwell) -- TOP PICK
- **GitHub:** https://github.com/chigwell/telegram-mcp
- **Stars:** ~653
- **What:** Full Telegram MCP via Telethon (MTProto). Read chats, manage groups, send/edit/delete messages, media, contacts, polls, inline buttons, drafts, privacy settings.
- **Why useful:** OpenClaw's Telegram bot can be enhanced with MCP. Read chat history for context, manage groups, send rich messages with inline buttons, search messages.
- **Install:**
  ```bash
  git clone https://github.com/chigwell/telegram-mcp.git
  cd telegram-mcp && uv sync
  uv run session_string_generator.py  # generate Telegram session
  ```
- **Docker:** Supported via docker-compose

### B) telegram-mcp (guangxiangdebizi) -- BOT API FOCUSED
- **GitHub:** https://github.com/guangxiangdebizi/telegram-mcp
- **Stars:** Available
- **What:** Built on Telegram Bot API (not MTProto). Rich text, photo, document, video, forwarding, analytics.
- **Why useful:** If you prefer Bot API over user-account MTProto. Modular architecture.

### C) mcp-telegram-notifier (harnyk)
- **GitHub:** https://github.com/harnyk/mcp-telegram-notifier
- **Stars:** Available
- **What:** Simple: send messages, photos, documents, videos via Telegram bot. Notification-focused.
- **Why useful:** Lightweight option for sending alerts/notifications from AI workflows to Telegram.

### D) Telegram-Bot-MCP (SmartManoj)
- **GitHub:** https://github.com/SmartManoj/Telegram-Bot-MCP
- **Stars:** Available
- **What:** FastMCP-based Telegram bot. Polling, webhook, combined modes. Exposes Telegram as MCP tools/resources.
- **Why useful:** Exposes Telegram bot functionality as MCP tools that n8n can call.

---

## 8. Knowledge Graph / Memory MCP Servers

### A) Official Memory Server (Anthropic) -- ESSENTIAL
- **GitHub:** https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- **Stars:** Part of 77,800-star repo
- **What:** Knowledge graph persistent memory. Entities, relations, observations stored in JSONL. Claude remembers across chats.
- **Why useful:** Core memory for OpenClaw. Store GICS entities (companies, sectors, industries) as graph nodes with relations. Persist research findings across conversations.
- **Install:**
  ```bash
  npx -y @modelcontextprotocol/server-memory
  ```
- **Config:**
  ```json
  {
    "mcpServers": {
      "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {
          "MEMORY_FILE_PATH": "/path/to/memory.jsonl"
        }
      }
    }
  }
  ```

### B) Basic Memory (basicmachines-co) -- TOP PICK for Obsidian integration
- **GitHub:** https://github.com/basicmachines-co/basic-memory
- **Stars:** ~2,400
- **What:** Local-first knowledge management. Builds semantic graph from Markdown files. All knowledge stored in standard Markdown. Compatible with Obsidian.
- **Why useful:** Bridges AI memory and your Obsidian vault. Knowledge stored as Markdown with wiki-links and YAML frontmatter -- exactly your existing format. Semantic graph traversal across topics.
- **Install:**
  ```bash
  uv tool install basic-memory
  ```
- **Config:**
  ```json
  {
    "mcpServers": {
      "basic-memory": {
        "command": "uvx",
        "args": ["basic-memory", "mcp"]
      }
    }
  }
  ```
- **Key:** Stores in Markdown with `[[wiki-links]]` and YAML frontmatter -- native Obsidian format

### C) Neo4j MCP (neo4j-contrib) -- ENTERPRISE GRAPH
- **GitHub:** https://github.com/neo4j-contrib/mcp-neo4j
- **Stars:** ~885
- **What:** Natural language to Cypher queries, knowledge graph memory in Neo4j, data modeling, Aura cloud management.
- **Why useful:** If you want a proper graph database for GICS entity relationships. Store sector->industry->sub-industry->company hierarchies. Query complex relationships via natural language.
- **Install:** npm packages, multi-transport (stdio, SSE, HTTP)
- **Sub-servers:**
  - `mcp-neo4j-cypher` -- natural language -> Cypher queries
  - `mcp-neo4j-memory` -- knowledge graph memory across sessions
  - `mcp-neo4j-data-modeling` -- interactive graph model creation

### D) Graphiti MCP (rawr-ai)
- **GitHub:** https://github.com/rawr-ai/mcp-graphiti
- **Stars:** Available
- **What:** Entity/relationship extraction from text into Neo4j. Multi-project support. Docker-based.
- **Why useful:** Auto-extract entities and relationships from research notes and store in knowledge graph.

---

## 9. Transport Proxies

Since n8n Cloud uses SSE/HTTP and some clients (like Claude Desktop) only support stdio, you need bridges:

### A) mcp-proxy (sparfenyuk) -- RECOMMENDED
- **GitHub:** https://github.com/sparfenyuk/mcp-proxy
- **What:** Bidirectional bridge: stdio <-> SSE. Can proxy in both directions.
- **Install:**
  ```bash
  uv tool install mcp-proxy
  # or
  pipx install mcp-proxy
  ```

### B) mcp-remote
- **GitHub:** https://github.com/jms830/mcp-remote
- **What:** Connects stdio-only clients to remote HTTP+SSE MCP servers. OAuth support.
- **Security:** Pin version >= 0.1.16 (critical RCE fix in earlier versions)
- **Architecture:** `Claude Desktop <-> (stdio) <-> mcp-remote <-> (SSE/HTTP) <-> n8n MCP Server Trigger`

---

## 10. Recommended Stack for This Setup

### Tier 1: Essential (Install First)

| Server | Purpose | Why |
|--------|---------|-----|
| **n8n Native MCP** | Expose n8n workflows as tools | Built-in, zero install. Your automation backbone. |
| **n8n-MCP (czlonkowski)** | AI builds n8n workflows | 13K stars. OpenClaw can create/modify workflows via Telegram. |
| **obsidian-mcp-server (cyanheads)** | Vault read/write/search | Full CRUD on Obsidian notes, frontmatter, tags. Core for knowledge management. |
| **Official Memory Server** | Persistent entity memory | Store GICS entities, company research, user preferences across sessions. |
| **telegram-mcp (chigwell)** | Telegram integration | Full Telegram access for OpenClaw bot. |

### Tier 2: High Value (Add Next)

| Server | Purpose | Why |
|--------|---------|-----|
| **Basic Memory** | Markdown-based knowledge graph | 2.4K stars. Native Obsidian format (wiki-links, YAML). Bridges AI memory and vault. |
| **Financial Modeling Prep MCP** | GICS entity enrichment | 253+ financial tools. Sector/industry data for GICS classification. |
| **Yahoo Finance MCP** | Free stock data | No API key needed. Quick lookups, earnings, news. |
| **Bright Data MCP** | Web research | 2K stars. Scrape any public page. Free tier 5K/month. |
| **google-workspace-mcp** | Full Google Workspace | Drive + Gmail + Calendar. Sync vault, send alerts, manage schedule. |

### Tier 3: Power User (When Needed)

| Server | Purpose | Why |
|--------|---------|-----|
| **MaverickMCP** | Technical analysis + backtesting | 39+ tools, VectorBT, ML strategies. For investment research. |
| **Neo4j MCP** | Enterprise knowledge graph | If JSONL memory is insufficient. Proper graph DB for complex GICS hierarchies. |
| **obsidian-mcp-plugin (aaronsb)** | Graph-aware vault AI | Multi-hop traversal, Dataview queries. For deep MOC navigation. |
| **Firecrawl MCP** | Deep web crawling | 5.4K stars. Crawl entire sites, structured extraction. |
| **Crawl4AI MCP** | Self-hosted scraping | Free, deploy on VPS alongside OpenClaw. |
| **n8n-mcp-server (illuminaresolutions)** | n8n instance management | Manage workflows/executions programmatically. |
| **mcp-proxy** | Transport bridge | Connect stdio clients to SSE servers and vice versa. |

### Architecture Diagram

```
                    Telegram Users
                         |
                    [Telegram Bot]
                         |
                  [OpenClaw AI Agent] (VPS)
                    /    |    \
                   /     |     \
    [telegram-mcp]  [memory]  [obsidian-mcp-server]
                         |            |
                   [Basic Memory]     |
                     (Markdown)       |
                         |            |
                   [Google Drive] <---+
                   [Obsidian Vault]
                         |
              [google-workspace-mcp]
                         |
              [n8n Cloud MCP Server Trigger]
                    /    |    \
                   /     |     \
     [Finance MCP]  [Bright Data] [n8n-MCP]
     (FMP/Yahoo)    (Web Scraping) (Workflow Builder)
```

### VPS Installation Priority

For your OpenClaw VPS, install in this order:

```bash
# 1. Official Memory Server (persistent GICS entity memory)
npx -y @modelcontextprotocol/server-memory

# 2. Basic Memory (Obsidian-compatible knowledge graph)
uv tool install basic-memory

# 3. Obsidian MCP Server (vault CRUD)
npx obsidian-mcp-server

# 4. Yahoo Finance MCP (free stock data, no API key)
git clone https://github.com/Alex2Yang97/yahoo-finance-mcp.git

# 5. Telegram MCP (full Telegram access)
git clone https://github.com/chigwell/telegram-mcp.git

# 6. n8n-MCP (workflow knowledge)
npx n8n-mcp

# 7. Bright Data MCP (web scraping, hosted -- just add token)
# Configure: https://mcp.brightdata.com/mcp?token=YOUR_TOKEN

# 8. Financial Modeling Prep (comprehensive finance data)
npm install -g financial-modeling-prep-mcp-server
```

---

## Key References

- Official MCP Servers: https://github.com/modelcontextprotocol/servers (77.8K stars)
- Awesome MCP Servers: https://github.com/wong2/awesome-mcp-servers
- MCP Specification: https://modelcontextprotocol.io/
- n8n MCP Docs: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/
- n8n MCP Access: https://docs.n8n.io/advanced-ai/accessing-n8n-mcp-server/
