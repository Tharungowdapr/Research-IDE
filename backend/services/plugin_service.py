"""
Plugin System Service - Third-party tool integration
"""

import os
import importlib
import json
from typing import Dict, List, Any, Optional
from core.config import settings


PLUGIN_DIR = os.path.join(os.path.dirname(__file__), '../plugins')


class PluginRegistry:
    """Simple plugin registry for third-party research tools."""
    
    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        self._enabled: List[str] = []
    
    def register(self, name: str, plugin: Any):
        """Register a plugin."""
        self._plugins[name] = plugin
        if name not in self._enabled:
            self._enabled.append(name)
    
    def unregister(self, name: str):
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            if name in self._enabled:
                self._enabled.remove(name)
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a specific plugin."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins."""
        return [
            {
                "name": name,
                "enabled": name in self._enabled,
                "description": getattr(p, 'description', 'No description'),
                "version": getattr(p, 'version', '1.0.0'),
            }
            for name, p in self._plugins.items()
        ]
    
    def execute_plugin(self, name: str, *args, **kwargs) -> Any:
        """Execute a plugin if enabled."""
        if name not in self._enabled:
            raise ValueError(f"Plugin {name} is not enabled")
        
        plugin = self._plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin {name} not found")
        
        if hasattr(plugin, 'execute'):
            return plugin.execute(*args, **kwargs)
        raise AttributeError(f"Plugin {name} has no execute method")


# Global registry
registry = PluginRegistry()


def load_plugins():
    """Load plugins from the plugins directory."""
    if not os.path.exists(PLUGIN_DIR):
        os.makedirs(PLUGIN_DIR, exist_ok=True)
        return
    
    # Look for Python files in plugins directory
    for filename in os.listdir(PLUGIN_DIR):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                module_name = filename[:-3]
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}",
                    os.path.join(PLUGIN_DIR, filename)
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin class or instance
                    if hasattr(module, 'plugin'):
                        registry.register(module_name, module.plugin)
            except Exception as e:
                print(f"Failed to load plugin {filename}: {e}")


def create_sample_plugin():
    """Create a sample plugin for reference."""
    sample_path = os.path.join(PLUGIN_DIR, '_sample_plugin.py')
    if not os.path.exists(sample_path):
        with open(sample_path, 'w') as f:
            f.write('''
"""
Sample Plugin - Reference implementation
"""

class SamplePlugin:
    name = "sample"
    description = "A sample plugin for reference"
    version = "1.0.0"
    
    def execute(self, *args, **kwargs):
        """Main execution method for the plugin."""
        return {
            "status": "success",
            "message": "Sample plugin executed successfully",
            "args": args,
            "kwargs": kwargs,
        }

# Plugin instance
plugin = SamplePlugin()
''')
        print(f"Sample plugin created at {sample_path}")


def call_external_tool(tool_name: str, params: Dict) -> Dict:
    """Call an external research tool/API."""
    # Example integrations
    tool_map = {
        "crossref": _call_crossref,
        "pubmed": _call_pubmed,
        "google_scholar": _call_google_scholar,
    }
    
    if tool_name in tool_map:
        return tool_map[tool_name](params)
    
    return {"error": f"Tool {tool_name} not supported"}


async def _call_crossref(params: Dict) -> Dict:
    """Query Crossref API for academic papers."""
    import httpx
    
    try:
        query = params.get("query", "")
        url = "https://api.crossref.org/works"
        resp = await httpx.AsyncClient().get(url, params={
            "query": query,
            "rows": params.get("limit", 10),
            "mailto": "research@ide.app",
        })
        
        if resp.status_code == 200:
            data = resp.json()
            return {"results": data.get("message", {}).get("items", [])}
    except Exception as e:
        return {"error": str(e)}
    
    return {"error": "Crossref API request failed"}


def _call_pubmed(params: Dict) -> Dict:
    """Query PubMed for biomedical papers."""
    # Simplified - would use Biopython's Entrez in production
    return {"error": "PubMed integration not yet implemented"}


def _call_google_scholar(params: Dict) -> Dict:
    """Query Google Scholar (via proxy/scraper)."""
    return {"error": "Google Scholar integration not yet implemented"}
