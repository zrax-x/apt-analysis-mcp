# APT Analysis MCP Server

An MCP (Model Context Protocol) server designed to assist in APT (Advanced Persistent Threat) malware analysis. Currently provides tools for securely downloading samples via a jump server.

## Features

- **Sample Downloader**: Securely download malware samples from a remote server via a jump host using SSH/SCP.
- **Rule Hash Query**: Query sample hashes associated with YARA rules by rule name and namespace.
- **Integrated Workflow**: Download samples directly by YARA rule name.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/zrax-x/apt-analysis-mcp.git
    cd apt-analysis-mcp
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    # source .venv/bin/activate # Linux/Mac
    pip install -r requirements.txt
    ```

## Configuration

1.  **Copy the example configuration:**
    ```bash
    copy config.example.json config.json
    ```

2.  **Edit `config.json`:**
    Fill in your SSH details for the jumper and target servers, specify the local download directory, and configure the Rule Hash Mapping file path.

    ```json
    {
      "jumper": {
        "user": "your_jumper_user",
        "host": "jump_server_ip",
        "port": 22,
        "key": "~/.ssh/id_rsa_jumper"
      },
      "target": {
        "user": "your_target_user",
        "host": "target_server_ip",
        "port": 22,
        "workdir": "/path/to/target/workdir",
        "key": "~/.ssh/id_rsa_target"
      },
      "local_download_dir": "/path/to/local/samples",
      "rule_hash_mapping_file": "/path/to/Rule_Hash_Mapping.csv"
    }
    ```

    **Configuration Fields:**
    - `jumper`: Jump server (bastion host) SSH configuration
    - `target`: Target server SSH configuration where samples are stored
    - `local_download_dir`: Local directory to save downloaded samples
    - `rule_hash_mapping_file`: Path to the Rule_Hash_Mapping.csv file (absolute path recommended)

3.  **Generate Rule Hash Mapping:**
    The server requires a `Rule_Hash_Mapping.csv` file. Generate it by running:
    ```bash
    cd /path/to/yara_rules_parent_directory
    python3 build_rule_hash_mapping.py
    ```
    This will scan all YARA rules and create the mapping table. Then update the `rule_hash_mapping_file` path in `config.json` to point to this file.

## Usage with Claude Desktop

Add the server to your `claude_desktop_config.json` (typically in `%APPDATA%\Claude\` on Windows).

```json
{
  "mcpServers": {
    "apt-analysis": {
      "command": "path/to/your/venv/Scripts/python.exe",
      "args": [
        "path/to/apt-analysis-mcp/server.py"
      ]
    }
  }
}
```

## Available Tools

### 1. download_samples
Download malware samples by SHA256 hash.

**Parameters:**
- `hash_list` (list[str]): List of SHA256 hashes to download
- `output_dir` (str, optional): Local directory to save samples to (defaults to `local_download_dir` in config)

**Example:**
```
Download samples with hashes: ["3123bbd5564f4381820fb8da5810bd4d9718b5c80a7e8f055961007c6f30daff", "..."]
```

**Returns:**
```
"Successfully downloaded samples to /path/to/samples"
```

---

### 2. get_rule_sha256_list
Get SHA256 hash list for a YARA rule (ready for downloading samples).

This tool queries the Rule_Hash_Mapping.csv file (configured in `config.json`) to retrieve SHA256 hashes associated with a specific YARA rule. The returned hashes can be directly used with the `download_samples` tool.

**Parameters:**
- `rule` (str, required): YARA rule name (e.g., "APT_xxx")
- `namespace` (str, optional): YARA file path for exact matching (e.g., "./yara_rules/xxx/pe_rules/abc.yara")
  - If not provided, returns all rules matching the rule name
  - If provided, returns only the exact match

**Example Usage:**
```
Get SHA256 list for rule: APT_xxx
```

**Returns:**
```json
{
  "success": true,
  "sha256_hashes": [
    "3123bbd5564f4381820fb8da5810bd4d9718b5c80a7e8f055961007c6f30daff",
    "123408972b8ec9c2e64eeb46ce1db92ae3c40bc8de48d278ba4d436fc3c8b3a4",
    "ffaab4463be9d8131f363fd78e21d9de5d838a3ec4044526aea45a473d6ddd61",
    "..."
  ],
  "count": 9,
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "sha256_hashes": [],
  "count": 0,
  "error": "No SHA256 hashes found for rule: nonexistent_rule"
}
```

**Notes:**
- The tool reads from the `rule_hash_mapping_file` configured in `config.json`
- Returns only SHA256 hashes (MD5 hashes are not included as downloads require SHA256)
- Automatically deduplicates hashes if a rule appears in multiple files
- If the mapping file is not found or not configured, returns an error

## Workflow Examples

### Example 1: Query and Download Samples
```
Step 1: Get SHA256 list for rule: APT_IN_xxx
Step 2: Download samples with the returned SHA256 hashes
```

### Example 2: Download Specific Rule Samples
```
1. Get SHA256 list for rule: M_Hunting_yyy
2. Copy the SHA256 hashes from the response
3. Download samples with those hashes to /home/user/samples
```

## Development

- **Add new tools**: Create new modules in `tools/` and register them in `server.py`.
