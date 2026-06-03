"""
ResearchIDE CLI - Interactive command-line interface for research workflow
Similar to opencode but tailored for research tasks
"""

import asyncio
import httpx
import json
import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
import typer

app = typer.Typer(name="research-ide", help="ResearchIDE CLI - AI-powered research assistant")
console = Console()

API_BASE = "http://localhost:8000/api"


class ResearchCLI:
    def __init__(self):
        self.token: Optional[str] = None
        self.current_project: Optional[str] = None
        self.client = httpx.Client(timeout=300.0)
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, email: str, password: str) -> bool:
        """Login to ResearchIDE."""
        try:
            resp = self.client.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "password": password}
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                console.print("[green]✓ Logged in successfully![/green]")
                return True
            else:
                console.print(f"[red]Login failed: {resp.json().get('detail', 'Unknown error')}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
            return False
    
    def list_projects(self):
        """List all projects."""
        try:
            resp = self.client.get(f"{API_BASE}/projects/", headers=self._headers())
            if resp.status_code == 200:
                projects = resp.json()
                if not projects:
                    console.print("[yellow]No projects found. Create one with 'create-project'[/yellow]")
                    return
                
                table = Table(title="Your Research Projects")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Stage", style="yellow")
                table.add_column("Status", style="blue")
                
                for p in projects:
                    table.add_row(
                        p["id"][:8] + "...",
                        p["title"][:40],
                        p.get("current_stage", "N/A"),
                        p.get("status", "N/A")
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Failed to fetch projects: {resp.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def create_project(self, title: str, description: str):
        """Create a new research project."""
        try:
            resp = self.client.post(
                f"{API_BASE}/projects/",
                headers=self._headers(),
                json={"title": title, "input_text": description}
            )
            if resp.status_code == 200:
                data = resp.json()
                self.current_project = data["id"]
                console.print(f"[green]✓ Project created: {title}[/green]")
                console.print(f"Project ID: {data['id']}")
                return data["id"]
            else:
                console.print(f"[red]Failed to create project: {resp.json().get('detail')}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
    
    def get_papers(self, project_id: Optional[str] = None):
        """Retrieve papers for a project."""
        pid = project_id or self.current_project
        if not pid:
            console.print("[red]No project selected. Use --project-id or create one.[/red]")
            return
        
        try:
            # First get intent
            console.print("[yellow]Extracting research intent...[/yellow]")
            resp = self.client.post(
                f"{API_BASE}/pipeline/intent",
                headers=self._headers(),
                json={"project_id": pid}
            )
            
            console.print("[yellow]Retrieving papers...[/yellow]")
            resp = self.client.post(
                f"{API_BASE}/pipeline/retrieve",
                headers=self._headers(),
                json={"project_id": pid, "max_papers": 20}
            )
            
            if resp.status_code == 200:
                papers = resp.json().get("papers", [])
                if not papers:
                    console.print("[yellow]No papers found.[/yellow]")
                    return
                
                table = Table(title=f"Papers for Project {pid[:8]}...")
                table.add_column("#", style="dim")
                table.add_column("Title", style="green")
                table.add_column("Year", style="blue")
                table.add_column("Citations", style="yellow")
                table.add_column("Source", style="cyan")
                
                for i, p in enumerate(papers[:15], 1):
                    table.add_row(
                        str(i),
                        p.get("title", "N/A")[:50] + "...",
                        str(p.get("year", "N/A")),
                        str(p.get("citations", "N/A")),
                        p.get("source", "N/A")
                    )
                
                console.print(table)
                console.print(f"[green]{len(papers)} papers retrieved[/green]")
            else:
                console.print(f"[red]Failed: {resp.json().get('detail')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def analyze_gaps(self, project_id: Optional[str] = None):
        """Run gap analysis on retrieved papers."""
        pid = project_id or self.current_project
        if not pid:
            console.print("[red]No project selected.[/red]")
            return
        
        try:
            console.print("[yellow]Running gap analysis (this may take 2-5 minutes)...[/yellow]")
            console.print("[dim]Fetching full text for papers...[/dim]")
            
            resp = self.client.post(
                f"{API_BASE}/agents/analyze-gaps",
                headers=self._headers(),
                json={"project_id": pid}
            )
            
            if resp.status_code == 200:
                gaps = resp.json().get("gaps", [])
                if not gaps:
                    console.print("[yellow]No gaps identified.[/yellow]")
                    return
                
                console.print(f"\n[green]✓ Found {len(gaps)} research gaps![/green]\n")
                
                for i, gap in enumerate(gaps[:10], 1):
                    panel = Panel(
                        f"[bold]{gap.get('title', 'N/A')}[/bold]\n\n"
                        f"[dim]Type:[/dim] {gap.get('type', 'N/A')} | "
                        f"[dim]Confidence:[/dim] {gap.get('confidence', 'N/A')}\n\n"
                        f"{gap.get('description', 'N/A')[:200]}...\n\n"
                        f"[dim]Opportunity:[/dim] {gap.get('opportunity', 'N/A')[:100]}",
                        title=f"Gap #{i}",
                        border_style="green"
                    )
                    console.print(panel)
                    console.print()
            else:
                console.print(f"[red]Failed: {resp.json().get('detail')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def generate_ideas(self, project_id: Optional[str] = None):
        """Generate research ideas from gaps."""
        pid = project_id or self.current_project
        if not pid:
            console.print("[red]No project selected.[/red]")
            return
        
        try:
            console.print("[yellow]Generating research ideas...[/yellow]")
            
            resp = self.client.post(
                f"{API_BASE}/agents/generate-ideas",
                headers=self._headers(),
                json={"project_id": pid}
            )
            
            if resp.status_code == 200:
                ideas = resp.json().get("ideas", [])
                if not ideas:
                    console.print("[yellow]No ideas generated.[/yellow]")
                    return
                
                console.print(f"\n[green]✓ Generated {len(ideas)} ideas![/green]\n")
                
                for i, idea in enumerate(ideas[:5], 1):
                    panel = Panel(
                        f"[bold]{idea.get('title', 'N/A')}[/bold]\n\n"
                        f"{idea.get('description', 'N/A')[:300]}...\n\n"
                        f"[dim]Novelty:[/dim] {idea.get('novelty_score', 'N/A')}/10 | "
                        f"[dim]Feasibility:[/dim] {idea.get('feasibility_score', 'N/A')}/10",
                        title=f"Idea #{i}",
                        border_style="blue"
                    )
                    console.print(panel)
                    console.print()
            else:
                console.print(f"[red]Failed: {resp.json().get('detail')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


# Typer CLI commands
@app.command()
def login(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Login to ResearchIDE."""
    cli = ResearchCLI()
    if cli.login(email, password):
        # Save token to file
        with open("/tmp/research_ide_token", "w") as f:
            f.write(cli.token or "")
        console.print("[green]Token saved. You can now use other commands.[/green]")


@app.command()
def projects():
    """List all your research projects."""
    cli = ResearchCLI()
    _load_token(cli)
    cli.list_projects()


@app.command()
def create(
    title: str = typer.Option(..., prompt=True),
    description: str = typer.Option(..., prompt=True)
):
    """Create a new research project."""
    cli = ResearchCLI()
    _load_token(cli)
    cli.create_project(title, description)


@app.command()
def papers(
    project_id: str = typer.Option(None, "--project", "-p")
):
    """Retrieve papers for a project."""
    cli = ResearchCLI()
    _load_token(cli)
    cli.get_papers(project_id)


@app.command()
def gaps(
    project_id: str = typer.Option(None, "--project", "-p")
):
    """Analyze research gaps."""
    cli = ResearchCLI()
    _load_token(cli)
    cli.analyze_gaps(project_id)


@app.command()
def ideas(
    project_id: str = typer.Option(None, "--project", "-p")
):
    """Generate research ideas."""
    cli = ResearchCLI()
    _load_token(cli)
    cli.generate_ideas(project_id)


@app.command()
def workflow(
    title: str = typer.Option(..., prompt=True),
    description: str = typer.Option(..., prompt=True)
):
    """Run complete research workflow interactively."""
    cli = ResearchCLI()
    _load_token(cli)
    
    # Create project
    pid = cli.create_project(title, description)
    if not pid:
        return
    
    # Get papers
    console.print("\n[bold]Step 1: Retrieving papers...[/bold]")
    cli.get_papers(pid)
    
    # Analyze gaps
    if Confirm.ask("\nProceed with gap analysis?"):
        cli.analyze_gaps(pid)
    
    # Generate ideas
    if Confirm.ask("\nProceed with idea generation?"):
        cli.generate_ideas(pid)


def _load_token(cli: ResearchCLI):
    """Load saved token."""
    try:
        with open("/tmp/research_ide_token", "r") as f:
            cli.token = f.read().strip()
    except:
        console.print("[red]Not logged in. Run 'login' first.[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
