
# UiO Summer Project -- Nuclear Propulsion

This repository contains the code, input files and generated outputs for a summer project on the deployment of nuclear-powered maritime vessels between 2035 and 2060. The project develops a simplified scenario model to connect fleet deployment, maritime route-network expansion, reactor and fuel-cycle requirements, and port-based nuclear service infrastructure.

The model is divided into several parts. The maritime part builds the operating fleet and route network. The reactor and fuel-cycle part estimates fuel requirements, enrichment needs, refuelling demand, spent-fuel generation and storage requirements. The port-service part allocates global nuclear-service requirements to selected nuclear-capable ports.

---

## Repository structure

Main files and folders:

```text
inputs/
  country/                  Country and port input files
  ship/                     Ship-segment input files
  scenario/                 Reactor/fuel-cycle scenario input files
  nuclear_capable_ports.txt Nuclear-capable port deployment assumptions
  port_connection_proposals.txt Candidate maritime routes

outputs/
  maritime/                 Route-network outputs and maps
  port_service_hubs/        Nuclear port-service allocation outputs and plots

country.py                  Country data structure
main_maritime_network.py    Maritime route-network model
port_service_hub_allocation.py Port-service hub allocation model
main.py                     Main reactor/fuel-cycle model
reactor.py                  Reactor definitions
ship.py                     Ship definitions
utilities.py                Input-reading utilities
sensitivity.py              Sensitivity analysis
outputs.py                  Output-writing utilities
````

---

## Maritime network model

The maritime part of the project is mainly implemented in:

```text
country.py
main_maritime_network.py
```

### `country.py`

This file defines the country-level data structure used by the maritime model. Each country can include:

* general country information;
* OECD membership;
* supply-chain role;
* port-operation status;
* port names;
* port coordinates;
* port activation years.

The corresponding input files are stored in:

```text
inputs/country/
```

The combined country file is:

```text
inputs/country/all_countries.txt
```

The country input data are used to define which countries participate in the operating maritime network, which ports are available, and when each port becomes active.

### `main_maritime_network.py`

This script builds the maritime fleet and route-network deployment.

It uses the following main inputs:

```text
outputs/deployment_baseline.txt
inputs/ship/ship_*.txt
inputs/country/country_*.txt
inputs/port_connection_proposals.txt
inputs/nuclear_capable_ports.txt
```

The script performs four main tasks.

First, it reads the ship-segment input files and the deployment baseline. From these files, it calculates how many ships of each segment are active in each year between 2035 and 2060.

Second, it calculates the annual sailing-distance capacity and annual port-call capacity of each ship segment. These values are based on the number of active ships, average speed, annual operating hours and assumed port calls per ship.

Third, it builds the route network over time. Candidate routes are read from `port_connection_proposals.txt`. A route can be selected only if its proposed operation year has been reached, both ports are active, and the ship segment is allowed to use that route. The route network is built sequentially, so routes selected in earlier years are retained in later years while new routes are added as fleet capacity grows.

Fourth, it generates route maps. The script can plot all active routes for a selected year and can also plot separate maps for each ship segment. Nuclear-capable ports are shown with red crosses when their nuclear-capability activation year has been reached.

Main maritime outputs are written to:

```text
outputs/maritime/
```

Important generated files include:

```text
outputs/maritime/route_network_summary_by_year.txt
outputs/maritime/route_network_allocation_by_year.txt
outputs/maritime/fleet_distance_capacity.pdf
outputs/maritime/fleet_portcall_capacity.pdf
outputs/maritime/all_routes/
outputs/maritime/routes_by_segment/
```

---
## Global fuel and infrastructure needs model
The global fuel and infrastructure part of the project is mainly implemented in:

```text
reactor.py
ship.py
utilities.py
outputs.py
main.py
```

### `reactor.py`

This file contains the Reactor class.
Each instance is defined by reactor power, fuel burnup, fuel enrichment, and reactor name.

### `ship.py`

This file contains the Ship and PoweredShip classes. 
An instance of the Ship class is defined by installed power,propulsion power,auxiliary power, average speed,
operational time, number of portcalls per year, and a ship segment name.

The PoweredShip class inherits from the Ship, Reactor and Country classes, but running the Country initialiser is optional.
Additionally, it contains the number of ships and reactors. The class describes a combination between a ship segment and a reactor type. The number of vessels with this combination can be adjusted after initialization.

### `utilities.py`

This file includes functions relevant for performing the model calculations for fuel requirements, for converting between different quantities, and for initialising class instances from input files.

### `outputs.py`

This file contains the FuelNeeds and InfrastructureNeeds classes. These are used for storing and grouping model outputs for a given year.

### `main.py`

This script calculates the global fuel and infrastructure needs for different scenarios. A scenario is defined by a list of ship segments, each ship segment's share of the total fleet, reactor name, country name (deprecated; PoweredShip can initialize without country name), and deployment phase. There are two deployment phases. Either a ship segment starts deployment in 2035, i.e. phase 1, or it is delayed by a given number of years in phase 2. All model outputs for a given scenario are output as a textfile. The baseline outputs are also plotted and saved in the plots folder. The fleet deployment history is also output to a textfile.

It uses the following main inputs:

```text
inputs/ship/ship_*.txt
inputs/reactor_*.txt
inputs/scenario/scenario_*.txt
inputs/country/country_*.txt (optional)

```

The calculations are described by the functions model() and deployment(). The model() function calculates the fuel related requirements for the fleet in a given year by iterating over a list of PoweredShip instances which describes the fleet for that year. The deployment() function updates the number of fleets in the ship using a sum of sigmoid functions, and then passes the updated fleet composition to the model() to get the fuel related outputs for each year. This function also calculates the infrastructure related outputs, along with fuel related outputs which depend on model() outputs from previous years. 

The results are written to file and plotted by the run_scenario() function.

Important generated files include:

```text
outputs/deployment_baseline.txt
outputs/*_global_fuel_infrastructure.txt
plots/baseline_*.png
```
---
## Nuclear port-service hub allocation

The port-service part of the project is implemented in:

```text
port_service_hub_allocation.py
```

This script connects the global fuel-cycle infrastructure requirements to the nuclear-capable port network.

It uses the following main inputs:

```text
outputs/baseline_global_fuel_infrastructure.txt
inputs/nuclear_capable_ports.txt
```

The script reads the global yearly requirements for:

* initial fuel loading;
* refuelling events;
* fresh-fuel storage volume;
* spent-fuel storage volume;
* spent-fuel truckloads.

It then distributes these global requirements among the active nuclear-capable ports. A port is active only after its nuclear-capability activation year. Each port is assigned a nominal weight and a maturity factor. The allocation share of a port is calculated from its effective weight:

```text
effective weight = port weight × maturity factor
```

This allows the model to represent the fact that not all nuclear-capable ports have the same assumed service capacity, and that newly activated ports do not immediately operate at full capacity.

Main outputs are written to:

```text
outputs/port_service_hubs/
```

Important generated files include:

```text
outputs/port_service_hubs/nuclear_port_service_summary_by_year.txt
outputs/port_service_hubs/nuclear_port_service_allocation_by_year.txt
outputs/port_service_hubs/nuclear_port_deployment_2060.pdf
outputs/port_service_hubs/avg_service_events_per_active_port_2060.pdf
outputs/port_service_hubs/avg_storage_per_active_port_2060.pdf
outputs/port_service_hubs/allocated_refuellings_by_port_2040_2060.pdf
outputs/port_service_hubs/allocated_total_storage_by_port_2040_2060.pdf
outputs/port_service_hubs/allocated_truckloads_by_port_2040_2060.pdf
```

These outputs are used to analyse how the global fuel-cycle burden is distributed across the nuclear-capable port network.

---

## Inputs and outputs from the maritime part

The most relevant input files for the maritime model are:

```text
inputs/country/country_*.txt
inputs/ship/ship_*.txt
inputs/port_connection_proposals.txt
inputs/nuclear_capable_ports.txt
outputs/deployment_baseline.txt
```

The most relevant outputs from the maritime model are:

```text
outputs/maritime/route_network_summary_by_year.txt
outputs/maritime/route_network_allocation_by_year.txt
outputs/maritime/all_routes/*.pdf
outputs/maritime/routes_by_segment/*.pdf
```

The most relevant outputs from the nuclear port-service model are:

```text
outputs/port_service_hubs/nuclear_port_service_summary_by_year.txt
outputs/port_service_hubs/nuclear_port_service_allocation_by_year.txt
outputs/port_service_hubs/*.pdf
```

---
## Sensitivity analysis

The sensitivity analysis is handled by the following file:
```text
sensitivity.py
```
### `sensitivity.py`

This script performs the sensitivity analysis by reading outputs from different scenarios simulated by the main.py script. These are plotted in tornado plots. This program is hardcoded to study the following varying inputs: refueling interval, spent fuel storage time, burnup, and enrichment. It is similarly hardcoded to study how these inputs affect the following peak global outputs: total fueling requirements per year, separative work needed per year, total storage needs, truckloads needing transport per year.

It uses the following inputs:
```text
outputs/*_global_fuel_infrastructure.txt
```

It produces the following outputs:

```text
outputs/sensitivity_*.png
```
---
## How to run

The environment can be created from:

```bash
conda env create -f environment.yml
conda activate summer-env
```
The fuel and infrastructure needs model can be run with:

```bash
python main.py
```

The maritime network model can be run with:

```bash
python main_maritime_network.py
```

The port-service hub allocation can be run with:

```bash
python port_service_hub_allocation.py
```

The sensitivity analysis can be run with:

```bash
python sensitivity.py
```
---

## Notes

This repository is a research scenario model. The results should be interpreted as order-of-magnitude infrastructure estimates, not as engineering design outputs or forecasts of actual nuclear maritime deployment.

The model is intentionally modular. Input assumptions can be changed through the `.txt` files in `inputs/`, and the corresponding outputs can be regenerated in `outputs/`.





