"""
Command-line interface for the Agentic RAG system.
Provides interactive chat and management commands.
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from core.logger  import get_logger
from config.settings import settings

logger  = get_logger(__name__)
console = Console()


def get_llm():
    """Initialize and return LLM instance."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model       = settings.groq_model,
        api_key     = settings.groq_api_key,
        temperature = settings.groq_temperature,
        max_tokens  = settings.groq_max_tokens
    )


def get_orchestrator():
    """Initialize and return orchestrator."""
    from agents.orchestrator import Orchestrator
    return Orchestrator(get_llm())


@click.group()
def cli():
    """
    Agentic RAG System CLI.
    Use commands below to interact with the system.
    """
    pass


@cli.command()
@click.option(
    "--session",
    default = "cli_session",
    help    = "Session ID for memory continuity"
)
def chat(session: str):
    """
    Start an interactive chat session with the RAG system.
    Type 'exit' or 'quit' to end the session.
    """
    console.print(Panel(
        "[bold green]Agentic RAG System[/bold green]\n"
        f"Session: {session}\n"
        "Type [bold]exit[/bold] to quit",
        title   = "Welcome",
        border_style = "green"
    ))

    orchestrator = get_orchestrator()

    while True:
        try:
            query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not query:
                continue

            if query.lower() in ("exit", "quit", "q"):
                console.print(
                    "[yellow]Goodbye! Session ended.[/yellow]"
                )
                break

            console.print("[dim]Processing...[/dim]")

            result = orchestrator.run(
                query      = query,
                session_id = session,
                use_cache  = True
            )

            # Display answer
            console.print(Panel(
                result.get("answer", "No answer generated"),
                title        = f"[bold]Assistant[/bold] "
                               f"[dim](route: {result.get('route', 'N/A')})[/dim]",
                border_style = "blue"
            ))

            # Display metadata
            score     = result.get("score", 0.0)
            sources   = result.get("sources", [])
            from_cache = result.get("from_cache", False)
            latency   = result.get("total_time_ms", 0.0)

            meta = (
                f"Score: {score:.1f}/10 | "
                f"Sources: {', '.join(sources) if sources else 'none'} | "
                f"Cache: {'hit' if from_cache else 'miss'} | "
                f"Time: {latency:.0f}ms"
            )
            console.print(f"[dim]{meta}[/dim]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.error(f"CLI chat error: {e}")


@cli.command()
@click.argument("directory", default="data/raw")
def ingest(directory: str):
    """
    Ingest documents from a directory into the vector store.

    DIRECTORY: Path to directory containing documents (default: data/raw)
    """
    from scripts.ingest_documents import ingest_from_directory

    console.print(f"[cyan]Ingesting from: {directory}[/cyan]")

    try:
        result = ingest_from_directory(directory)
        console.print(Panel(
            f"[green]✅ Ingestion Complete[/green]\n\n"
            f"Documents : {result.get('docs', 0)}\n"
            f"Chunks    : {result.get('chunks', 0)}\n"
            f"Vectors   : {result.get('vectors', 0)}",
            title        = "Ingestion Result",
            border_style = "green"
        ))
    except Exception as e:
        console.print(f"[red]Ingestion failed: {e}[/red]")
        logger.error(f"CLI ingest error: {e}")


@cli.command()
def stats():
    """Show system statistics and metrics."""
    try:
        from database.sqlite_db              import sqlite_db
        from observability.tracer            import tracer
        from observability.metrics_collector import metrics_collector
        from vectorstore.faiss_store         import faiss_store
        from cache.response_cache            import ResponseCache

        db_stats      = sqlite_db.get_stats()
        tracer_metrics = tracer.get_metrics()
        cache         = ResponseCache()
        cache_stats   = cache.stats()

        # Vector store
        try:
            faiss_store.load()
            vector_count = faiss_store.total_vectors
        except Exception:
            vector_count = 0

        table = Table(title="System Statistics", show_header=True)
        table.add_column("Metric",     style="cyan",  no_wrap=True)
        table.add_column("Value",      style="green")

        table.add_row("Total Requests",  str(tracer_metrics.get("total_requests", 0)))
        table.add_row("Successful",      str(tracer_metrics.get("successful", 0)))
        table.add_row("Failed",          str(tracer_metrics.get("failed", 0)))
        table.add_row("Avg Latency",     f"{tracer_metrics.get('avg_latency_ms', 0):.1f}ms")
        table.add_row("Cache Hits",      str(tracer_metrics.get("cache_hits", 0)))
        table.add_row("Cache Misses",    str(tracer_metrics.get("cache_misses", 0)))
        table.add_row("Cache Entries",   str(cache_stats.get("total_entries", 0)))
        table.add_row("Query History",   str(db_stats.get("query_history", 0)))
        table.add_row("Tool Results",    str(db_stats.get("tool_results", 0)))
        table.add_row("Avg Score",       f"{db_stats.get('avg_score', 0):.2f}/10")
        table.add_row("Vector Count",    str(vector_count))
        table.add_row("LLM Model",       settings.groq_model)
        table.add_row("Embedding Model", settings.embedding_model)
        table.add_row("Environment",     settings.environment)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Stats error: {e}[/red]")
        logger.error(f"CLI stats error: {e}")


@cli.command()
@click.argument("query")
@click.option(
    "--session",
    default = "cli_single",
    help    = "Session ID"
)
@click.option(
    "--json-output",
    is_flag = True,
    help    = "Output as JSON"
)
def ask(query: str, session: str, json_output: bool):
    """
    Ask a single question and get an answer.

    QUERY: The question to ask
    """
    try:
        orchestrator = get_orchestrator()
        result       = orchestrator.run(
            query      = query,
            session_id = session,
            use_cache  = True
        )

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(Panel(
                result.get("answer", "No answer"),
                title        = f"Answer [dim](route: {result.get('route')})[/dim]",
                border_style = "blue"
            ))
            console.print(
                f"[dim]Score: {result.get('score', 0):.1f}/10 | "
                f"Time: {result.get('total_time_ms', 0):.0f}ms[/dim]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"CLI ask error: {e}")


@cli.command()
def clear_cache():
    """Clear the response cache."""
    try:
        from cache.response_cache import ResponseCache
        cache   = ResponseCache()
        removed = cache.clear_all()
        console.print(
            f"[green]✅ Cache cleared | removed={removed} entries[/green]"
        )
    except Exception as e:
        console.print(f"[red]Cache clear failed: {e}[/red]")


if __name__ == "__main__":
    cli()