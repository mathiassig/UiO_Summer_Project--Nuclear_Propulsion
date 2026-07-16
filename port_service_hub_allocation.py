"""
Allocate global fleet fuel-infrastructure requirements to nuclear-capable ports.

Inputs
------
1. *_infrastructure.txt
   Global yearly fleet demands: fuel throughput, fresh/spent storage,
   refuellings, new ship loadings, truckloads, etc.

2. nuclear_capable_ports.txt
   Nuclear-capable port activation years:
   port_name;nuclear_available_from_year

Outputs
-------
1. nuclear_port_service_summary_by_year.txt
   One row per year with global demand and average demand per active port.

2. nuclear_port_service_allocation_by_year.txt
   One row per active port and year with allocated refuellings, storage,
   fuel throughput and truckloads.

Method
------
For each year, only ports with nuclear_available_from_year <= year are active.
Global demand is distributed across active ports using normalized weights.

By default all ports have the same nominal weight, but a maturity factor is used:
newly activated ports start at 50% of full capacity, reach 75% in the following
year, and full capacity from the third year onward. The normalized shares still
sum to 1, so the full global yearly demand is allocated.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


DEFAULT_GLOBAL_FILE = Path("outputs") / "baseline_global_fuel_infrastructure.txt"
DEFAULT_NUCLEAR_PORT_FILE = Path("inputs") / "nuclear_capable_ports.txt"
DEFAULT_OUTPUT_DIR = Path("outputs") / "port_service_hubs"


# Optional future extension:
# Give some ports higher or lower nominal capacity if justified later.
# For the baseline, leave all ports equal.
PORT_WEIGHTS = {
    "Rotterdam": 1.30,
    "Singapore": 1.35,
    "Hamburg": 1.30,
    "Shanghai": 1.50,
    "Provideniya": 0.80,
    "Busan": 1.15,
    "Jebel Ali": 1.40,
    "Los Angeles": 0.95,
    "Algeciras": 1.50,
    "Murmansk": 1.15,
    "Savannah": 1.25,
    "Santos": 0.90,
    "Melbourne": 0.70,
    "Durban": 0.85,
    "Tromsø": 1.00,
    "Port Klang": 1.20,
}


def to_float(value: str) -> float:
    """Convert table value to float, accepting empty values as 0."""
    if value is None:
        return 0.0
    value = str(value).strip()
    if value == "":
        return 0.0
    return float(value)

def to_int(value: str) -> int:
    """Convert table value to int through float, accepting values such as 5.0."""
    return int(round(to_float(value)))

def maturity_factor(
    year: int,
    activation_year: int,
    ramp_years: int = 3,
    first_year_factor: float = 0.50,
) -> float:
    """
    Return the available capacity fraction of a nuclear-capable port.

    Example with default settings:
        activation year: 0.50
        next year:       0.75
        following years: 1.00
    """

    age = year - activation_year

    if age < 0:
        return 0.0

    if ramp_years <= 1:
        return 1.0

    factor = first_year_factor + (1.0 - first_year_factor) * age / (ramp_years - 1)
    return min(1.0, factor)

def read_global_fuel_infrastructure(input_file: Path) -> list[dict]:
    """Read global yearly fleet fuel and infrastructure demand."""
    rows = []

    with open(input_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            row["year"] = to_int(row["year"])
            rows.append(row)

    return rows

def read_nuclear_capable_ports(input_file: Path) -> list[dict]:
    """Read nuclear-capable ports and their activation years."""
    ports = []

    with open(input_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            ports.append(
                {
                    "port_name": row["port_name"].strip(),
                    "nuclear_available_from_year": to_int(
                        row["nuclear_available_from_year"]
                    ),
                }
            )

    return ports

def get_active_ports_for_year(
    nuclear_ports: list[dict],
    year: int,
    ramp_years: int,
    first_year_factor: float,
) -> list[dict]:
    """Return active nuclear-capable ports and their normalized weights."""
    active_ports = []

    for port in nuclear_ports:
        activation_year = port["nuclear_available_from_year"]

        if year < activation_year:
            continue

        nominal_weight = PORT_WEIGHTS.get(port["port_name"], 1.0)

        capacity_factor = maturity_factor(
            year=year,
            activation_year=activation_year,
            ramp_years=ramp_years,
            first_year_factor=first_year_factor,
        )

        effective_weight = nominal_weight * capacity_factor

        active_ports.append(
            {
                "port_name": port["port_name"],
                "nuclear_available_from_year": activation_year,
                "maturity_factor": capacity_factor,
                "nominal_weight": nominal_weight,
                "effective_weight": effective_weight,
            }
        )

    total_effective_weight = sum(
        port["effective_weight"]
        for port in active_ports
    )

    for port in active_ports:
        if total_effective_weight > 0:
            port["allocation_share"] = port["effective_weight"] / total_effective_weight
        else:
            port["allocation_share"] = 0.0

    return active_ports

def allocate_global_demands_to_ports(
    global_rows: list[dict],
    nuclear_ports: list[dict],
    ramp_years: int = 3,
    first_year_factor: float = 0.50,
) -> tuple[list[dict], list[dict]]:
    """
    Allocate global yearly infrastructure demand to active nuclear-capable ports.

    Returns
    -------
    summary_rows:
        One row per year.

    allocation_rows:
        One row per active port and year.
    """
    summary_rows = []
    allocation_rows = []

    for global_row in global_rows:
        year = to_int(global_row["year"])

        active_ports = get_active_ports_for_year(
            nuclear_ports=nuclear_ports,
            year=year,
            ramp_years=ramp_years,
            first_year_factor=first_year_factor,
        )

        number_active_ports = len(active_ports)
        effective_port_units = sum(
            port["effective_weight"]
            for port in active_ports
        )

        new_ship_loadings = to_float(global_row["new ships deployed"])
        refuellings = to_float(global_row["number of refuelings"])
        service_events = new_ship_loadings + refuellings

        fresh_storage = to_float(global_row["fresh fuel storage [m^3]"])
        spent_storage = to_float(global_row["spent fuel storage [m^3]"])
        truckloads = to_float(global_row["truckloads of waste transported"])
        fuel_throughput_tons = to_float(global_row["fuel throughput [tons]"])
        fuel_throughput_pebbles = to_float(global_row["fuel throughput [pebbles]"])
        initial_loading_tons = to_float(global_row["initial fuel loading [tons]"])
        refueling_tons = to_float(global_row["refueling [tons]"])
        initial_loading_pebbles = to_float(global_row["initial fuel loading [pebbles]"])
        refueling_pebbles = to_float(global_row["refueling [pebbles]"])
        waste_m3 = to_float(global_row["waste [m^3]"])

        summary_rows.append(
            {
                "year": year,
                "active_nuclear_ports": number_active_ports,
                "effective_port_units": effective_port_units,
                "global_new_ship_loadings": new_ship_loadings,
                "global_refuellings": refuellings,
                "global_total_service_events": service_events,
                "global_fresh_fuel_storage_m3": fresh_storage,
                "global_spent_fuel_storage_m3": spent_storage,
                "global_truckloads": truckloads,
                "average_service_events_per_active_port": (
                    service_events / number_active_ports
                    if number_active_ports > 0
                    else 0.0
                ),
                "average_refuellings_per_active_port": (
                    refuellings / number_active_ports
                    if number_active_ports > 0
                    else 0.0
                ),
                "average_fresh_storage_m3_per_active_port": (
                    fresh_storage / number_active_ports
                    if number_active_ports > 0
                    else 0.0
                ),
                "average_spent_storage_m3_per_active_port": (
                    spent_storage / number_active_ports
                    if number_active_ports > 0
                    else 0.0
                ),
                "average_truckloads_per_active_port": (
                    truckloads / number_active_ports
                    if number_active_ports > 0
                    else 0.0
                ),
            }
        )

        for port in active_ports:
            share = port["allocation_share"]

            allocation_rows.append(
                {
                    "year": year,
                    "port_name": port["port_name"],
                    "nuclear_available_from_year": port[
                        "nuclear_available_from_year"
                    ],
                    "maturity_factor": port["maturity_factor"],
                    "allocation_share": share,
                    "allocated_new_ship_loadings": new_ship_loadings * share,
                    "allocated_refuellings": refuellings * share,
                    "allocated_total_service_events": service_events * share,
                    "allocated_initial_fuel_loading_tons": initial_loading_tons * share,
                    "allocated_refueling_tons": refueling_tons * share,
                    "allocated_fuel_throughput_tons": fuel_throughput_tons * share,
                    "allocated_initial_fuel_loading_pebbles": (
                        initial_loading_pebbles * share
                    ),
                    "allocated_refueling_pebbles": refueling_pebbles * share,
                    "allocated_fuel_throughput_pebbles": (
                        fuel_throughput_pebbles * share
                    ),
                    "allocated_fresh_fuel_storage_m3": fresh_storage * share,
                    "allocated_spent_fuel_storage_m3": spent_storage * share,
                    "allocated_waste_m3": waste_m3 * share,
                    "allocated_truckloads": truckloads * share,
                }
            )

    return summary_rows, allocation_rows

def write_table(rows: list[dict], output_file: Path) -> None:
    """Write a semicolon-separated table."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError(f"No rows to write to {output_file}")

    fieldnames = list(rows[0].keys())

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)

def plot_grouped_port_metric_by_year(
    allocation_rows: list[dict],
    output_dir: Path,
    selected_years: list[int],
    metric_keys: list[str],
    title: str,
    xlabel: str,
    output_filename: str,
) -> Path | None:
    """
    Plot a grouped horizontal bar chart by port and year.

    Each port appears once on the y-axis.
    For each port, one bar is shown for each selected year.

    Parameters
    ----------
    allocation_rows:
        Port-by-port allocation rows.

    output_dir:
        Directory where the plot is saved.

    selected_years:
        Years to compare, for example [2040, 2045, 2050, 2055, 2060].

    metric_keys:
        One or more metric columns to plot.
        If more than one key is provided, the plotted value is the sum.

        Example:
            ["allocated_refuellings"]

        Example for total storage:
            [
                "allocated_fresh_fuel_storage_m3",
                "allocated_spent_fuel_storage_m3",
            ]

    title:
        Plot title.

    xlabel:
        x-axis label.

    output_filename:
        Name of the PDF file.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_years = [int(year) for year in selected_years]

    # Keep only rows from selected years.
    selected_rows = [
        row
        for row in allocation_rows
        if to_int(row["year"]) in selected_years
    ]

    if not selected_rows:
        print(f"No allocation rows found for years {selected_years}.")
        return None

    # Dictionary: (year, port_name) -> row
    rows_by_year_and_port = {}

    for row in selected_rows:
        year = to_int(row["year"])
        port_name = row["port_name"]
        rows_by_year_and_port[(year, port_name)] = row

    # Ports appearing in any of the selected years.
    ports = sorted(
        set(row["port_name"] for row in selected_rows)
    )

    def metric_value(row):
        if row is None:
            return 0.0

        total = 0.0

        for metric_key in metric_keys:
            total += to_float(row.get(metric_key, 0.0))

        return total

    # Sort ports by the final selected year, normally 2060.
    final_year = max(selected_years)

    ports = sorted(
        ports,
        key=lambda port: metric_value(
            rows_by_year_and_port.get((final_year, port))
        ),
        reverse=True,
    )

    y_positions = list(range(len(ports)))

    number_of_years = len(selected_years)
    group_height = 0.80
    bar_height = group_height / number_of_years

    fig_height = max(6, 0.45 * len(ports))
    fig, ax = plt.subplots(figsize=(12, fig_height))

    colors = plt.cm.tab10.colors

    for year_index, year in enumerate(selected_years):
        offset = (
            year_index - (number_of_years - 1) / 2
        ) * bar_height

        values = []

        for port in ports:
            row = rows_by_year_and_port.get((year, port))
            values.append(metric_value(row))

        bar_positions = [
            position + offset
            for position in y_positions
        ]

        ax.barh(
            bar_positions,
            values,
            height=bar_height * 0.90,
            label=str(year),
            color=colors[year_index % len(colors)],
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(ports,fontsize=18)
    ax.invert_yaxis()

    ax.tick_params(axis="x", labelsize=18)
    ax.set_xlabel(xlabel,fontsize=18)
    ax.set_title(title,fontsize=18)
    ax.grid(True, axis="x", alpha=0.3)
    ax.legend(fontsize=18)

    output_file = output_dir / output_filename

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)

    return output_file

def plot_port_service_hub_results(
    summary_rows: list[dict],
    allocation_rows: list[dict],
    output_dir: Path,
    selected_year: int = 2060,
    comparison_years: list[int] | None = None,
) -> list[Path]:
    """
    Generate plots from the nuclear-port service-hub allocation.

    The plots are intended to summarize:
        1. nuclear-port deployment and effective weighted capacity,
        2. service-event demand over time,
        3. average refuelling burden per active port,
        4. average fresh/spent storage burden per active port,
        5. port-level refuelling allocation in one selected year,
        6. port-level fresh/spent storage allocation in one selected year,
        7. port-level spent-fuel truckload allocation in one selected year.

    Parameters
    ----------
    summary_rows:
        Output from allocate_global_demands_to_ports().
        One row per year.

    allocation_rows:
        Output from allocate_global_demands_to_ports().
        One row per active port and year.

    output_dir:
        Main output directory. 

    selected_year:
        Year used for the port-by-port bar charts.

    Returns
    -------
    plot_files:
        List of generated plot-file paths.
    """

    plot_dir = Path(output_dir) 
    plot_dir.mkdir(parents=True, exist_ok=True)

    plot_files = []
    if comparison_years is None:
        comparison_years = [2040, 2045, 2050, 2055, 2060]

    summary_rows = sorted(
        summary_rows,
        key=lambda row: to_int(row["year"]),
    )

    years = [to_int(row["year"]) for row in summary_rows]

    # ------------------------------------------------------------
    # Plot 1: nuclear-port deployment and weighted capacity
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        years,
        [to_float(row["active_nuclear_ports"]) for row in summary_rows],
        marker="o",
        linewidth=2,
        label="Active nuclear-capable ports",
    )

    ax.plot(
        years,
        [to_float(row["effective_port_units"]) for row in summary_rows],
        marker="s",
        linewidth=2,
        label="Effective weighted port units",
    )

    ax.set_xlabel("Year",fontsize=18)
    ax.set_ylabel("Number of ports / weighted port units",fontsize=18)
    ax.set_title("Nuclear-capable port deployment over time",fontsize=18)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16)
    ax.tick_params(axis="both", labelsize=18)

    output_file = plot_dir / f"nuclear_port_deployment_{selected_year}.pdf"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    plot_files.append(output_file)

    
    # ------------------------------------------------------------
    # Plot 2: average refuelling burden per active port
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        years,
        [
            to_float(row["average_refuellings_per_active_port"])
            for row in summary_rows
        ],
        marker="o",
        linewidth=2,
        label="Average refuellings per active port",
    )

    ax.plot(
        years,
        [
            to_float(row["average_service_events_per_active_port"])
            for row in summary_rows
        ],
        marker="s",
        linewidth=2,
        label="Average total service events per active port",
    )

    ax.set_xlabel("Year",fontsize=18)
    ax.set_ylabel("Events per active port per year",fontsize=18)
    ax.set_title("Average nuclear service burden per active port",fontsize=18)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16)
    ax.tick_params(axis="both", labelsize=18)

    output_file = plot_dir / f"avg_service_events_per_active_port_{selected_year}.pdf" 
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    plot_files.append(output_file)

    # ------------------------------------------------------------
    # Plot 3: average fresh and spent fuel storage burden per port
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        years,
        [
            to_float(row["average_fresh_storage_m3_per_active_port"])
            for row in summary_rows
        ],
        marker="o",
        linewidth=2,
        label="Fresh fuel storage",
    )

    ax.plot(
        years,
        [
            to_float(row["average_spent_storage_m3_per_active_port"])
            for row in summary_rows
        ],
        marker="s",
        linewidth=2,
        label="Spent fuel storage",
    )

    ax.set_xlabel("Year",fontsize=18)
    ax.set_ylabel("Average storage volume per active port [m$^3$]",fontsize=18)
    ax.set_title("Average fuel-storage burden per active port",fontsize=18)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16)
    ax.tick_params(axis="both", labelsize=18)

    output_file = plot_dir / f"avg_storage_per_active_port_{selected_year}.pdf"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    plot_files.append(output_file)

    # ------------------------------------------------------------
    # Plot 4: allocated refuellings by port for selected years
    # ------------------------------------------------------------
    output_file = plot_grouped_port_metric_by_year(
        allocation_rows=allocation_rows,
        output_dir=plot_dir,
        selected_years=comparison_years,
        metric_keys=["allocated_refuellings"],
        title="Allocated refuellings by nuclear-capable port",
        xlabel="Allocated refuellings per year",
        output_filename=(
            f"allocated_refuellings_by_port_"
            f"{min(comparison_years)}_{max(comparison_years)}.pdf"
        ),
    )

    if output_file is not None:
        plot_files.append(output_file)

    # ------------------------------------------------------------
    # Plot 5: allocated total fuel-storage volume by port
    # ------------------------------------------------------------
    output_file = plot_grouped_port_metric_by_year(
        allocation_rows=allocation_rows,
        output_dir=plot_dir,
        selected_years=comparison_years,
        metric_keys=[
            "allocated_fresh_fuel_storage_m3",
            "allocated_spent_fuel_storage_m3",
        ],
        title="Allocated total fuel-storage volume by port",
        xlabel="Allocated total storage volume [m$^3$]",
        output_filename=(
            f"allocated_total_storage_by_port_"
            f"{min(comparison_years)}_{max(comparison_years)}.pdf"
        ),
    )

    if output_file is not None:
        plot_files.append(output_file)

    # ------------------------------------------------------------
    # Plot 6: allocated spent-fuel truckloads by port
    # ------------------------------------------------------------
    output_file = plot_grouped_port_metric_by_year(
        allocation_rows=allocation_rows,
        output_dir=plot_dir,
        selected_years=comparison_years,
        metric_keys=["allocated_truckloads"],
        title="Allocated spent-fuel truckloads by port",
        xlabel="Allocated spent-fuel truckloads per year",
        output_filename=(
            f"allocated_truckloads_by_port_"
            f"{min(comparison_years)}_{max(comparison_years)}.pdf"
        ),
    )

    if output_file is not None:
        plot_files.append(output_file)

    return plot_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Allocate global nuclear fleet infrastructure demand to nuclear-capable ports."
    )

    parser.add_argument(
        "--global-file",
        type=Path,
        default=DEFAULT_GLOBAL_FILE,
        help="Path to baseline_global_fuel_infrastructure.txt",
    )
    parser.add_argument(
        "--nuclear-ports-file",
        type=Path,
        default=DEFAULT_NUCLEAR_PORT_FILE,
        help="Path to nuclear_capable_ports.txt",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where output tables will be written.",
    )
    parser.add_argument(
        "--ramp-years",
        type=int,
        default=3,
        help="Number of years required for a new nuclear-capable port to reach full allocation weight.",
    )
    parser.add_argument(
        "--first-year-factor",
        type=float,
        default=0.50,
        help="Capacity factor assigned to a port in its activation year.",
    )
    parser.add_argument(
        "--plot-year",
        type=int,
        default=2060,
        help="Year used for the port-by-port service-hub plots.",
    )
    parser.add_argument(
        "--comparison-years",
        type=int,
        nargs="+",
        default=[2040, 2045, 2050, 2055, 2060],
        help=(
            "Years used for grouped port-by-port comparison plots. "
            "Example: --comparison-years 2040 2045 2050 2055 2060"
        ),
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="If provided, output tables are written but plots are not generated.",
    )

    args = parser.parse_args()

    global_rows = read_global_fuel_infrastructure(args.global_file)
    nuclear_ports = read_nuclear_capable_ports(args.nuclear_ports_file)

    summary_rows, allocation_rows = allocate_global_demands_to_ports(
        global_rows=global_rows,
        nuclear_ports=nuclear_ports,
        ramp_years=args.ramp_years,
        first_year_factor=args.first_year_factor,
    )

    summary_file = args.output_dir / "nuclear_port_service_summary_by_year.txt"
    allocation_file = args.output_dir / "nuclear_port_service_allocation_by_year.txt"

    write_table(summary_rows, summary_file)
    write_table(allocation_rows, allocation_file)

    print(f"Summary table saved to: {summary_file}")
    print(f"Port allocation table saved to: {allocation_file}")

    if not args.skip_plots:
        plot_files = plot_port_service_hub_results(
            summary_rows=summary_rows,
            allocation_rows=allocation_rows,
            output_dir=args.output_dir,
            selected_year=args.plot_year,
            comparison_years=args.comparison_years,
        )

        for plot_file in plot_files:
            print(f"Plot saved to: {plot_file}")


if __name__ == "__main__":
    main()
