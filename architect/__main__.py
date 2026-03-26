"""CLI entry point for the Architect pipeline.

Usage::

    python -m architect --prompt "3-bedroom house"
"""

from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console
from rich.panel import Panel

from architect.config import DEFAULT_EDITOR_URL, DEFAULT_MODEL, DEFAULT_WS_URL

console = Console()


# ------------------------------------------------------------------
# Async pipeline runner
# ------------------------------------------------------------------

async def _run(
    model_name: str,
    prompt: str,
    editor_url: str,
    ws_url: str,
    verbose: bool,
    clear: bool,
) -> None:
    # Late imports so --help stays fast and doesn't require all deps.
    from architect.client import EditorClient
    from architect.config import get_model
    from architect.graph import compile_graph
    from architect.tools.editor import set_client

    client = EditorClient(ws_url=ws_url)
    try:
        console.print("[bold cyan]Connecting to editor...[/]")
        await client.connect()
        set_client(client)

        if clear:
            console.print("[yellow]Clearing existing scene...[/]")
            await client.clear()

        llm = get_model(model_name)
        app = compile_graph(llm)

        initial_state = {
            "prompt": prompt,
            "model_name": model_name,
            "editor_url": editor_url,
            "ws_url": ws_url,
            "current_floor_index": 0,
            "total_floors": 0,
            "floor_plans": [],
            "built_node_ids": [],
            "level_ids": [],
            "wall_id_map": {},
            "errors": [],
        }

        console.print("[bold cyan]Starting pipeline...[/]\n")

        async for event in app.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                _print_node_update(node_name, state_update, verbose)

        console.print(f"\n[bold green]Done! View at {editor_url}[/]")

    except Exception as exc:
        console.print(f"\n[bold red]Error: {exc}[/]")
        sys.exit(1)
    finally:
        await client.close()


# ------------------------------------------------------------------
# Pretty-print helpers
# ------------------------------------------------------------------

def _print_node_update(node_name: str, update: dict, verbose: bool) -> None:
    """Print a concise summary line for a graph node update."""
    errors = update.get("errors")
    if errors:
        for err in errors:
            console.print(f"  [bold red]{node_name}: ERROR - {err}[/]")
        return

    if node_name == "architect":
        spec = update.get("architect_spec") or {}
        floors = spec.get("floors", [])
        rooms = sum(len(f.get("rooms", [])) for f in floors)
        roof = spec.get("roof", {}).get("type", "none")
        console.print(
            f"  [bold cyan]{node_name}:[/] "
            f"{len(floors)} floor(s), {rooms} room(s), roof={roof}"
        )
        if verbose and spec:
            console.print(f"    [dim]{spec}[/]")

    elif node_name == "floor_planner":
        plans = update.get("floor_plans", [])
        if plans:
            latest = plans[-1] if isinstance(plans, list) else plans
            walls = len(latest.get("walls", []))
            slabs = len(latest.get("slabs", []))
            zones = len(latest.get("zones", []))
            windows = len(latest.get("windows", []))
            doors = len(latest.get("doors", []))
            console.print(
                f"  [bold yellow]{node_name}:[/] "
                f"{walls} walls, {slabs} slabs, {zones} zones, "
                f"{windows} windows, {doors} doors"
            )
        else:
            console.print(f"  [bold yellow]{node_name}:[/] planning...")
        if verbose and plans:
            console.print(f"    [dim]{plans}[/]")

    elif node_name == "builder":
        built = update.get("built_node_ids", [])
        floor_idx = update.get("current_floor_index", "?")
        total = update.get("total_floors", "?")
        console.print(
            f"  [bold green]{node_name}:[/] "
            f"{len(built)} node(s) placed "
            f"(floor {floor_idx}/{total})"
        )

    elif node_name == "furnisher":
        console.print(f"  [bold magenta]{node_name}:[/] furnishing complete")

    else:
        console.print(f"  [bold]{node_name}:[/] updated")


# ------------------------------------------------------------------
# CLI definition
# ------------------------------------------------------------------

@click.command()
@click.option("--model", default=DEFAULT_MODEL, help="LLM model name")
@click.option("--prompt", required=True, help="Building description")
@click.option("--editor-url", default=DEFAULT_EDITOR_URL, help="Editor URL")
@click.option("--ws-url", default=DEFAULT_WS_URL, help="WebSocket relay URL")
@click.option("--verbose", is_flag=True, help="Show agent reasoning")
@click.option("--clear", is_flag=True, help="Clear existing scene first")
def main(
    model: str,
    prompt: str,
    editor_url: str,
    ws_url: str,
    verbose: bool,
    clear: bool,
) -> None:
    """Architect Bot -- AI-powered building generator for Pascal Editor."""
    panel_content = (
        f"[bold]Model:[/]  {model}\n"
        f"[bold]Prompt:[/] {prompt}\n"
        f"[bold]Editor:[/] {editor_url}\n"
        f"[bold]WS:[/]     {ws_url}"
    )
    console.print(Panel(panel_content, title="Architect Bot", border_style="cyan"))
    asyncio.run(_run(model, prompt, editor_url, ws_url, verbose, clear))


if __name__ == "__main__":
    main()
