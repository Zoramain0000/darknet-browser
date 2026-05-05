# 🦉 Robin AI — Dark Web OSINT Platform

> **AI-Powered Dark Web Investigation Tool**
> Queries 16 dark web search engines in parallel through Tor, scrapes `.onion` sites, and analyzes results with **Mistral AI**.

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start (Local)](#-quick-start-local)
- [Docker Deployment](#-docker-deployment)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Pipeline Stages](#-pipeline-stages)
- [Dark Web Search Engines](#-dark-web-search-engines)
- [Project Structure](#-project-structure)
- [Security & Ethics](#-security--ethics)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🏗️ Architecture

┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌────────────────┐ │ User UI │───→│ Mistral AI │───→│ Tor Proxy │───→│ 16× Dark Web │ │ (Streamlit) │ │ Query Refine │ │ SOCKS5h │ │ Search Engines│ └─────────────┘ └──────────────┘ └─────────────┘ └────────────────┘ │ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ │ │ Report │←───│ Mistral AI │←───│ .onion │←────────────┘ │ Generator │ │ Analysis │ │ Scraper │ └─────────────┘ └──────────────┘ └─────────────┘

**Pipeline Flow:**

1. **User Query** → Enter search term in Streamlit UI
2. **LLM Refinement** → Mistral AI optimizes the query
3. **Tor Proxy** → Routes all traffic through Tor (SOCKS5h)
4. **Parallel Search** → Queries 16 engines simultaneously
5. **Onion Scraping** → Extracts content from discovered `.onion` sites
6. **LLM Analysis** → Mistral AI analyzes findings for threats
7. **Report Generation** → Markdown/HTML investigation report

---

## ✨ Features

### 🔍 **Intelligence Gathering**
- **16 Dark Web Search Engines** queried in parallel
  - Ahmia, Torch, OnionLand, Tor66, DarkSearch, Excavator, DeepSearch, FindTor, DarkWebLINK, Tordex, TorLinks, UnderDir, DarkWebEyes, OnionSearch, HiddenWiki, OnionDir
- **Deduplication** by URL, sorted by content relevance
- **Real .onion site scraping** through Tor proxy

### 🤖 **AI-Powered Analysis**
- **Mistral AI Integration** (real API — requires key)
- Query refinement for optimal dark web search results
- Threat identification & severity assessment
- Credential leak detection (emails, BTC, ETH addresses)
- Automated report generation with actionable recommendations

### 🎨 **Cyberpunk UI**
- Dark neon theme (`#0a0a0f` background, `#00f0ff` cyan accents)
- Real-time progress tracking with stage indicators
- Interactive pipeline visualization
- Responsive design (desktop + mobile)

### 🐳 **Production Ready**
- Docker Compose with Tor proxy container
- Health checks and automatic restart
- Prometheus metrics (optional)
- Non-root user execution

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | 3.9+ | 3.11 recommended |
| Streamlit | 1.55+ | Web UI framework |
| Tor | 0.4.8+ | SOCKS5 proxy for anonymity |
| Mistral AI Key | - | Get at [console.mistral.ai](https://console.mistral.ai) |
| Docker (optional) | 24+ | For containerized deployment |

### System Dependencies (Linux)

```bash
# Tor
sudo apt update && sudo apt install -y tor

# Python + virtualenv
sudo apt install -y python3 python3-pip python3-venv