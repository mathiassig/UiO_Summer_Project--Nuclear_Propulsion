class Country:
    def __init__(
        self,
        name,
        iso3,
        region,
        oecd_member,
        supply,
        step,
        supply_from_year,
        capacity,
        capacity_unit,
        operation,
        available_from_year,
        ports,
        port_names,
        latitude,
        longitude,
    ):
        self.name = name
        self.iso3 = iso3
        self.region = region
        self.oecd_member = oecd_member

        self.supply = supply
        self.step = step
        self.supply_from_year = supply_from_year
        self.capacity = capacity
        self.capacity_unit = capacity_unit

        self.operation = operation
        self.available_from_year = available_from_year
        self.ports = ports
        self.port_names = port_names
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return (
            f"=== {self.name} ({self.iso3}) country characteristics ===\n"
            f"Region: {self.region}\n"
            f"OECD member: {self.oecd_member}\n"
            f"Taking part in the supply chain: {self.supply}\n"
            f"Step in the supply chain: {self.step}\n"
            f"Taking part in the supply chain from year: {self.supply_from_year}\n"
            f"Production: {self.capacity} {self.capacity_unit}\n"
            f"Taking part in the fleet operation routes: {self.operation}\n"
            f"Ports available from year: {self.available_from_year}\n"
            f"Number of relevant ports: {self.ports}\n"
            f"Port names: {self.port_names}\n"
            f"Latitude: {self.latitude}\n"
            f"Longitude: {self.longitude}\n"
        )
