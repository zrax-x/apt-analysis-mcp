from fastmcp import FastMCP
from tools.sample_downloader import download_samples as download_samples_api
from tools.rule_hash_query import RuleHashQuery
import os
import json

# Create an MCP server
mcp = FastMCP("apt-analysis")

# Initialize rule hash query
rule_query = None

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

# Load config globally
config = load_config()

# Initialize rule hash query
try:
    mapping_file = config.get("rule_hash_mapping_file", None)
    rule_query = RuleHashQuery(mapping_file)
    print(f"Loaded {len(rule_query.mapping)} rule mappings from {rule_query.mapping_file}", flush=True)
except Exception as e:
    print(f"Warning: Failed to load rule hash mapping: {e}", flush=True)
    rule_query = None

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


@mcp.tool()
def get_rule_sha256_list(rule: str, namespace: str = None) -> dict:
    """
    Get SHA256 hash list for a YARA rule.

    Args:
        rule: YARA rule name (e.g., "APT_xxx")
        namespace: Optional YARA file path for exact matching (e.g., "./yara_rules/xxx/pe_rules/abc.yara")
    
    Returns:
        Dictionary containing:
        - success: bool
        - sha256_hashes: list of SHA256 hash strings (ready for download)
        - count: number of SHA256 hashes
        - error: error message if failed
    
    Example response:
        {
            "success": true,
            "sha256_hashes": ["3123bbd5564f4381820fb8da5810bd4d9718b5c80a7e8f055961007c6f30daff", ...],
            "count": 9,
            "error": null
        }
    """
    if rule_query is None:
        return {
            "success": False,
            "sha256_hashes": [],
            "count": 0,
            "error": "Rule hash mapping not loaded. Please ensure Rule_Hash_Mapping.csv exists."
        }
    
    try:
        sha256_hashes = rule_query.get_sha256_list(rule, namespace)
        
        if not sha256_hashes:
            return {
                "success": False,
                "sha256_hashes": [],
                "count": 0,
                "error": f"No SHA256 hashes found for rule: {rule}"
            }
        
        return {
            "success": True,
            "sha256_hashes": sha256_hashes,
            "count": len(sha256_hashes),
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "sha256_hashes": [],
            "count": 0,
            "error": str(e)
        }

if __name__ == "__main__":
    mcp.run()
