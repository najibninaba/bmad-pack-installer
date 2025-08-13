"""Command-line interface for BMAD expansion pack installer."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from .installer import install_expansion_pack, InstallationResult
from .validators import is_bmad_project, is_expansion_pack


console = Console()


def print_result(result: InstallationResult) -> None:
    """Print installation result with rich formatting.
    
    Args:
        result: Installation result to display
    """
    if result.success:
        # Success message
        rprint(f"[green]✅ {result.message}[/green]")
        
        # Installation details table
        table = Table(title="Installation Summary", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Pack Name", result.pack_name)
        table.add_row("Directory", result.pack_directory)
        table.add_row("Files Installed", str(result.files_installed))
        
        if result.symlinks_created:
            table.add_row("Symlinks Created", str(len(result.symlinks_created)))
        
        if result.symlinks_failed:
            table.add_row("Symlinks Failed", f"[red]{len(result.symlinks_failed)}[/red]")
        
        console.print(table)
        
        # Show symlinks if created
        if result.symlinks_created:
            rprint(f"\n[green]🔗 Claude Integration:[/green]")
            for symlink in result.symlinks_created[:5]:  # Show first 5
                rprint(f"  ✓ {symlink}")
            if len(result.symlinks_created) > 5:
                remaining = len(result.symlinks_created) - 5
                rprint(f"  ... and {remaining} more")
        
        # Show warnings
        if result.warnings:
            rprint(f"\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in result.warnings:
                rprint(f"  • {warning}")
    
    else:
        # Error message
        rprint(f"[red]❌ {result.message}[/red]")
        
        if result.warnings:
            rprint(f"\n[yellow]Additional Information:[/yellow]")
            for warning in result.warnings:
                rprint(f"  • {warning}")


def deploy_command(
    source_path: str,
    target_path: str,
    pack_name: Optional[str],
    command_name: Optional[str],
    ide: str,
    skip_core_update: bool,
    skip_symlinks: bool,
    force: bool,
    dry_run: bool,
    verbose: bool
) -> None:
    """Deploy BMAD expansion pack.
    
    SOURCE_PATH: Path to expansion pack directory
    TARGET_PATH: Path to target BMAD project
    
    Examples:
    
        # Basic deployment
        bmad-pack-installer deploy ./bmad-aisg-aiml /path/to/project
        
        # With custom options
        bmad-pack-installer deploy ./source /target --pack-name=ai-ml --command-name=bmadAISG
        
        # Dry run to preview
        bmad-pack-installer deploy ./source /target --dry-run
        
        # Force reinstall
        bmad-pack-installer deploy ./source /target --force
    """
    # Convert paths
    source = Path(source_path).resolve()
    target = Path(target_path).resolve()
    
    # Print header
    if verbose or dry_run:
        panel_title = "BMAD Expansion Pack Installer" + (" (DRY RUN)" if dry_run else "")
        panel = Panel.fit(
            f"Source: [cyan]{source}[/cyan]\n"
            f"Target: [cyan]{target}[/cyan]",
            title=panel_title,
            border_style="blue"
        )
        console.print(panel)
        console.print()
    
    # Quick validation
    if not is_expansion_pack(source):
        rprint(f"[red]❌ Source directory is not a valid BMAD expansion pack:[/red] {source}")
        rprint("[yellow]💡 Tip: Make sure the directory contains a config.yaml file[/yellow]")
        sys.exit(1)
    
    if not is_bmad_project(target):
        rprint(f"[red]❌ Target directory is not a BMAD-enabled project:[/red] {target}")
        rprint("[yellow]💡 Tip: Make sure the project has a .bmad-core directory[/yellow]")
        sys.exit(1)
    
    if verbose:
        rprint("[blue]🔍 Running installation...[/blue]")
        console.print()
    
    # Run installation
    result = install_expansion_pack(
        source_path=str(source),
        target_path=str(target),
        pack_name=pack_name,
        command_name=command_name,
        ide=ide,
        skip_core_update=skip_core_update,
        skip_symlinks=skip_symlinks,
        force=force,
        dry_run=dry_run
    )
    
    # Print result
    print_result(result)
    
    # Exit with appropriate code
    if not result.success:
        sys.exit(1)
    elif result.warnings:
        # Success with warnings
        sys.exit(0)
    else:
        # Complete success
        sys.exit(0)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Show version')
def cli(ctx: click.Context, version: bool) -> None:
    """BMAD Expansion Pack Installer.
    
    A tool to install BMAD expansion packs with proper directory structure,
    symbolic links, and manifest management.
    """
    if version:
        from . import __version__
        rprint(f"[cyan]BMAD Pack Installer[/cyan] [green]v{__version__}[/green]")
        return
    
    if ctx.invoked_subcommand is None:
        # If no subcommand, show help
        rprint(ctx.get_help())


@cli.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def check(project_path: str) -> None:
    """Check if a directory is a valid BMAD project.
    
    PROJECT_PATH: Path to project directory to check
    """
    project = Path(project_path).resolve()
    
    rprint(f"[blue]🔍 Checking project:[/blue] {project}")
    
    if is_bmad_project(project):
        rprint("[green]✅ Valid BMAD project[/green]")
        
        # Show additional info
        bmad_core = project / '.bmad-core'
        manifest_file = bmad_core / 'install-manifest.yaml'
        
        if manifest_file.exists():
            try:
                import yaml
                with open(manifest_file, 'r') as f:
                    manifest = yaml.safe_load(f)
                
                expansion_packs = manifest.get('expansion_packs', [])
                if expansion_packs:
                    rprint(f"[cyan]📦 Installed expansion packs:[/cyan]")
                    for pack in expansion_packs:
                        rprint(f"  • {pack}")
                else:
                    rprint("[yellow]📦 No expansion packs installed[/yellow]")
            except Exception:
                rprint("[yellow]⚠️  Could not read manifest file[/yellow]")
    else:
        rprint("[red]❌ Not a valid BMAD project[/red]")
        rprint("[yellow]💡 Tip: Initialize BMAD first or check .bmad-core directory[/yellow]")
        sys.exit(1)


@cli.command()
@click.argument('source_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def validate(source_path: str) -> None:
    """Validate if a directory is a valid BMAD expansion pack.
    
    SOURCE_PATH: Path to expansion pack directory to validate
    """
    source = Path(source_path).resolve()
    
    rprint(f"[blue]🔍 Validating expansion pack:[/blue] {source}")
    
    if is_expansion_pack(source):
        rprint("[green]✅ Valid BMAD expansion pack[/green]")
        
        # Show pack info
        try:
            from .validators import load_config
            config = load_config(source / 'config.yaml')
            
            table = Table(title="Pack Information", show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Name", config.get('name', 'Unknown'))
            table.add_row("Version", config.get('version', 'Unknown'))
            table.add_row("Description", config.get('description', 'No description'))
            
            if 'slashPrefix' in config:
                table.add_row("Command Name", config['slashPrefix'])
            
            console.print(table)
            
        except Exception as e:
            rprint(f"[yellow]⚠️  Could not read pack details: {e}[/yellow]")
    else:
        rprint("[red]❌ Not a valid BMAD expansion pack[/red]")
        rprint("[yellow]💡 Tip: Make sure the directory contains a config.yaml file[/yellow]")
        sys.exit(1)


# Wire up the deploy command
@cli.command(name='deploy')
@click.argument('source_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('target_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    '--pack-name', 
    help='Override pack name (default: from config.yaml, auto-prepends "bmad-" if missing)'
)
@click.option(
    '--command-name', 
    help='Claude command name (default: from config.yaml slashPrefix)'
)
@click.option(
    '--ide', 
    type=click.Choice(['claude-code', 'cursor', 'windsurf']),
    default='claude-code',
    help='IDE to configure (default: claude-code)'
)
@click.option(
    '--skip-core-update', 
    is_flag=True,
    help='Skip updating .bmad-core/install-manifest.yaml'
)
@click.option(
    '--skip-symlinks', 
    is_flag=True,
    help='Skip creating symbolic links'
)
@click.option(
    '--force', 
    is_flag=True,
    help='Overwrite existing installation'
)
@click.option(
    '--dry-run', 
    is_flag=True,
    help='Show what would be installed without making changes'
)
@click.option(
    '--verbose', 
    is_flag=True,
    help='Enable detailed logging'
)
def deploy_wrapper(*args, **kwargs):
    """Deploy BMAD expansion pack.
    
    SOURCE_PATH: Path to expansion pack directory
    TARGET_PATH: Path to target BMAD project
    """
    return deploy_command(*args, **kwargs)


if __name__ == '__main__':
    cli()