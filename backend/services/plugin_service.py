"""
Plugin System Service - Third-party tool integration
"""

import os
import importlib
import json
from typing import Dict, List, Any, Optional
from core.config import settings


PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")


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


async def call_external_tool(tool_name: str, params: Dict) -> Dict:
    """Call an external research tool/API."""
    tool_map = {
        "crossref": _call_crossref,
        "pubmed": _call_pubmed,
        "google_scholar": _call_google_scholar,
    }

    if tool_name in tool_map:
        return await tool_map[tool_name](params)

    return {"error": f"Tool {tool_name} not supported"}


async def _call_crossref(params: Dict) -> Dict:
    """Query Crossref API for academic papers."""
    import httpx

    try:
        query = params.get("query", "")
        url = "https://api.crossref.org/works"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params={
                "query": query,
                "rows": params.get("limit", 10),
                "mailto": "research@ide.app",
            })

        if resp.status_code == 200:
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("title", [""])[0] if item.get("title") else "",
                    "authors": [
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in item.get("author", [])
                    ],
                    "year": str(item.get("published-print", {}).get("date-parts", [[""]])[0][0]) if item.get("published-print") else "",
                    "doi": item.get("DOI", ""),
                    "source": "crossref",
                })
            return {"results": results}
        return {"error": f"Crossref returned status {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


async def _call_pubmed(params: Dict) -> Dict:
    """Query PubMed via NCBI E-utilities for biomedical papers."""
    import httpx

    try:
        query = params.get("query", "")
        limit = params.get("limit", 10)
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

        async with httpx.AsyncClient(timeout=15.0) as client:
            search_resp = await client.get(f"{base}/esearch.fcgi", params={
                "db": "pubmed",
                "term": query,
                "retmax": limit,
                "retmode": "json",
            })
            search_data = search_resp.json()
            ids = search_data.get("esearchresult", {}).get("idlist", [])
            if not ids:
                return {"results": []}

            fetch_resp = await client.get(f"{base}/esummary.fcgi", params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            })
            fetch_data = fetch_resp.json()
            results = []
            for pid in ids:
                info = fetch_data.get("result", {}).get(pid, {})
                if not info or info.get("error"):
                    continue
                authors = [
                    a.get("name", "") for a in info.get("authors", [])
                ]
                results.append({
                    "title": info.get("title", ""),
                    "authors": authors,
                    "year": info.get("pubdate", "")[:4],
                    "pmid": pid,
                    "source": "pubmed",
                    "abstract_snippet": info.get("sortpubdate", ""),
                })
            return {"results": results}
    except Exception as e:
        return {"error": str(e)}


async def _call_google_scholar(params: Dict) -> Dict:
    """Query Google Scholar using SerpAPI (if key available) or Semantic Scholar as fallback."""
    import httpx

    serpapi_key = os.environ.get("SERPAPI_API_KEY", "")
    if serpapi_key:
        try:
            query = params.get("query", "")
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get("https://serpapi.com/search", params={
                    "q": query,
                    "api_key": serpapi_key,
                    "engine": "google_scholar",
                    "num": params.get("limit", 10),
                })
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("organic_results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "authors": [a.get("name", "") for a in item.get("inline_links", {}).get("authors", [])] if isinstance(item.get("inline_links", {}).get("authors"), list) else [],
                        "year": str(item.get("publication_info", {}).get("summary", "")[-4:]) if item.get("publication_info") else "",
                        "url": item.get("link", ""),
                        "source": "google_scholar",
                        "snippet": item.get("snippet", ""),
                    })
                return {"results": results}
        except Exception as e:
            pass

    try:
        query = params.get("query", "")
        limit = params.get("limit", 10)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://api.semanticscholar.org/graph/v1/paper/search", params={
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,url,abstract",
            })
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for p in data.get("data", []):
                results.append({
                    "title": p.get("title", ""),
                    "authors": [a.get("name", "") for a in p.get("authors", [])],
                    "year": str(p.get("year", "")),
                    "url": p.get("url", ""),
                    "source": "semantic_scholar",
                    "abstract_snippet": (p.get("abstract") or "")[:200],
                })
            return {"results": results}
        return {"error": f"Semantic Scholar returned status {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}
