"""Rich CLI interface for the NumWorks probe tool."""

import sys
import os
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

from .device import NumWorksDevice
from .probe import CalculatorProbe
from .storage import Storage, Script

console = Console()


@click.group()
def cli():
    """NumWorks Calculator Hardware & Firmware Probe Tool."""
    pass


@cli.command("info")
def info_cmd():
    """Quick USB and Hardware identification of connected calculator."""
    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        console.print("Please check that the calculator is turned ON and connected with a data cable.")
        sys.exit(1)

    info = dev.get_info()
    table = Table(title="NumWorks Calculator USB Device Info", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Model", info.model_name)
    table.add_row("Product Name", info.product_name)
    table.add_row("Manufacturer", info.manufacturer)
    table.add_row("Serial Number", info.serial_number or "[dim]N/A[/dim]")
    table.add_row("Hardware Revision", f"0x{info.revision:04x}")
    table.add_row("USB Vendor ID", f"0x{info.vendor_id:04x}")
    table.add_row("USB Product ID", f"0x{info.product_id:04x}")
    table.add_row("USB Bus / Address", f"Bus {info.bus}, Device {info.address}")
    table.add_row("Mode", "[bold red]DFU Recovery[/bold red]" if info.is_dfu_mode else "[bold green]Normal (Epsilon OS)[/bold green]")

    console.print(table)


@cli.command("probe")
def probe_cmd():
    """Run a comprehensive probe of hardware, firmware, memory layout, and scripts."""
    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        console.print("Please check that the calculator is turned ON and connected with a data cable.")
        sys.exit(1)

    with console.status("[bold green]Probing NumWorks calculator...") as status:
        probe = CalculatorProbe(dev)
        result = probe.probe(progress_callback=lambda msg: status.update(f"[bold green]{msg}"))

    info = result.device_info

    # 1. Device Info Table
    dev_table = Table(title="Hardware & Device Info", show_header=True, header_style="bold cyan")
    dev_table.add_column("Property", style="bold")
    dev_table.add_column("Value", style="green")

    dev_table.add_row("Model", info.model_name)
    dev_table.add_row("Serial Number", info.serial_number or "[dim]N/A[/dim]")
    dev_table.add_row("Hardware Revision", f"0x{info.revision:04x}")
    dev_table.add_row("USB ID", f"0x{info.vendor_id:04x}:0x{info.product_id:04x}")
    dev_table.add_row("Location", f"Bus {info.bus} Device {info.address} (Port {info.port})")
    console.print(dev_table)
    console.print()

    # If error occurred during deep probe
    if result.error:
        console.print(Panel(f"[bold red]Probe Notice:[/bold red]\n{result.error}", title="Probe Status", border_style="yellow"))
        return

    # 2. Firmware Info Table
    fw = result.firmware_info
    fw_table = Table(title="Firmware & OS Info", show_header=True, header_style="bold magenta")
    fw_table.add_column("Property", style="bold")
    fw_table.add_column("Value", style="green")

    fw_table.add_row("Epsilon Version", fw.kernel_version)
    fw_table.add_row("Git Commit / Patch", fw.kernel_patch)
    fw_table.add_row("Storage Address", f"0x{fw.storage_address:08x}" if fw.storage_address else "Unknown")
    fw_table.add_row("Storage Buffer Size", f"{fw.storage_size} bytes" if fw.storage_size else "Unknown")
    console.print(fw_table)
    console.print()

    # 3. Memory Layout
    if result.memory_layout:
        mem_table = Table(title="Flash / Memory Layout", show_header=True, header_style="bold blue")
        mem_table.add_column("Start Address", style="cyan")
        mem_table.add_column("End Address", style="cyan")
        mem_table.add_column("Size", style="green")
        mem_table.add_column("Pages", style="white")
        mem_table.add_column("Page Size", style="white")

        for seg in result.memory_layout:
            mem_table.add_row(
                f"0x{seg['address']:08x}",
                f"0x{seg['last_address']:08x}",
                f"{seg['size'] // 1024} KB ({seg['size']} bytes)",
                str(seg["nb_pages"]),
                f"{seg['page_size'] // 1024} KB",
            )
        console.print(mem_table)
        console.print()

    # 4. Scripts Table
    if result.scripts:
        scr_table = Table(title=f"Stored Python Scripts ({len(result.scripts)})", show_header=True, header_style="bold yellow")
        scr_table.add_column("Script Name", style="bold")
        scr_table.add_column("Size (bytes)", style="cyan")
        scr_table.add_column("Lines", style="white")
        scr_table.add_column("Auto-Import", style="green")

        for s in result.scripts:
            line_count = len(s.code.splitlines())
            scr_table.add_row(
                s.name,
                str(s.size),
                str(line_count),
                "Yes" if s.auto_import else "No",
            )
        console.print(scr_table)
    elif result.raw_storage_accessible:
        console.print("[dim]No Python scripts currently found in calculator storage.[/dim]")


@cli.group("scripts")
def scripts_group():
    """Manage and inspect Python scripts on the calculator."""
    pass


@scripts_group.command("list")
def list_scripts_cmd():
    """List Python scripts stored on the calculator."""
    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        sys.exit(1)

    probe = CalculatorProbe(dev)
    result = probe.probe()

    if result.error:
        console.print(f"[bold red]{result.error}[/bold red]")
        sys.exit(1)

    if not result.scripts:
        console.print("[dim]No Python scripts found on device.[/dim]")
        return

    table = Table(title=f"Python Scripts on Calculator ({len(result.scripts)})")
    table.add_column("Name", style="bold cyan")
    table.add_column("Size", style="green")
    table.add_column("Auto-Import", style="yellow")

    for s in result.scripts:
        table.add_row(s.name, f"{s.size} B", "Yes" if s.auto_import else "No")

    console.print(table)


@scripts_group.command("view")
@click.argument("name")
def view_script_cmd(name: str):
    """Display the contents of a Python script from the calculator."""
    if not name.endswith(".py"):
        name += ".py"

    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        sys.exit(1)

    probe = CalculatorProbe(dev)
    result = probe.probe()

    target = None
    for s in result.scripts:
        if s.name == name:
            target = s
            break

    if not target:
        console.print(f"[bold red]Script '{name}' not found on calculator.[/bold red]")
        sys.exit(1)

    console.print(Panel(
        Syntax(target.code, "python", theme="monokai", line_numbers=True),
        title=f"Script: {target.name} ({target.size} bytes)",
        border_style="cyan"
    ))


@scripts_group.command("dump")
@click.argument("output_dir", default="scripts", type=click.Path())
def dump_scripts_cmd(output_dir: str):
    """Dump all Python scripts from the calculator into a local directory."""
    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        sys.exit(1)

    probe = CalculatorProbe(dev)
    result = probe.probe()

    if not result.scripts:
        console.print("[dim]No scripts found to dump.[/dim]")
        return

    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)

    for s in result.scripts:
        file_path = dest / s.name
        file_path.write_text(s.code, encoding="utf-8")
        console.print(f"[green]Saved:[/green] {file_path}")

    console.print(f"\n[bold green]Successfully dumped {len(result.scripts)} script(s) to {dest}/[/bold green]")


@cli.command("dump-memory")
@click.argument("address")
@click.argument("length", type=int)
@click.argument("output_file", type=click.Path())
def dump_memory_cmd(address: str, length: int, output_file: str):
    """Dump a raw memory/flash range via DFU upload. ADDRESS can be hex (0x...) or dec."""
    addr = int(address, 0)
    dev = NumWorksDevice.find_first()
    if not dev:
        console.print("[bold red]No NumWorks calculator detected![/bold red]")
        sys.exit(1)

    probe = CalculatorProbe(dev)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
    ) as progress:
        task = progress.add_task(f"Dumping {length} bytes from 0x{addr:08x}...", total=length)

        data = probe.dump_memory(
            addr,
            length,
            progress_callback=lambda current, total: progress.update(task, completed=current),
        )

    out_path = Path(output_file)
    out_path.write_bytes(data)
    console.print(f"[bold green]Dumped {len(data)} bytes to {out_path}[/bold green]")


def main():
    cli()


if __name__ == "__main__":
    main()
