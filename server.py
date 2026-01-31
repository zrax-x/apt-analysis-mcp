from fastmcp import FastMCP
from tools.sample_downloader import download_samples as download_samples_api
import os
import json

# Create an MCP server
mcp = FastMCP("apt-analysis")

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

# Load config globally
config = load_config()

@mcp.tool()
def download_samples(hash_list: list[str], output_dir: str = None) -> str:
    """
    Download malware samples by hash.

    Args:
        hash_list: List of SHA256 hashes to download.
        output_dir: Local directory to save samples to. Defaults to config value.
    """
    # Use default from config if not provided
    if output_dir is None:
        output_dir = config.get("local_download_dir", "/tmp/samples")

    # Construct config dictionaries expected by the API
    jumper_config = config["jumper"]
    target_config = config["target"]

    # Use a print logger for MCP logging if needed, or just silence it
    def log_callback(msg):
        # In a real MCP server, we might want to log this to stderr or via MCP logs
        # For now, we'll keep it simple
        pass

    success, path, error = download_samples_api(
        hash_list=hash_list,
        local_output_dir=output_dir,
        jumper_config=jumper_config,
        target_config=target_config,
        output_dirname="mcp_download",
        flat_output=True,
        log_callback=log_callback
    )

    if success:
        return f"Successfully downloaded samples to {path}"
    else:
        return f"Failed to download samples: {error}"

if __name__ == "__main__":
    mcp.run()
