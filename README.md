# APT Analysis MCP Server

An MCP (Model Context Protocol) server designed to assist in APT (Advanced Persistent Threat) malware analysis. Currently provides tools for securely downloading samples via a jump server.

## Features

- **Sample Downloader**: Securely download malware samples from a remote server via a jump host using SSH/SCP.

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
    Fill in your SSH details for the jumper and target servers, and specify the local download directory.

    ```json
    {
      "jumper": {
        "user": "your_jumper_user",
        // ...
      },
      "target": {
        "user": "your_target_user",
        // ...
      },
      "local_download_dir": "C:\\path\\to\\samples"
    }
    ```

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

## Development

- **Add new tools**: Create new modules in `tools/` and register them in `server.py`.
