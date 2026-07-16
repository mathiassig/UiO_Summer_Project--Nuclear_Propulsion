import numpy as np
from reactor import Reactor
from ship import Ship, PoweredShip
from country import Country

class FuelNeeds:
    def __init__(self,fuel_throughput,swu,feedmass):
        self.fuel_throughput = fuel_throughput
        self.swu = swu
        self.feedmass = feedmass
class InfrastructureNeeds:
    def __init__(self):
        pass

def init_reactor_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    power,burnup,enrichment,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,0]
    return Reactor(power,burnup,enrichment,name)

def init_ship_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,4].astype(float),file[1,5].astype(float),file[1,6].astype(float),file[1,0]
    return Ship(installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name)

def init_powered_ship_from_files(shipfilename,reactorfilename,countryfilename,number=1):
    shipfile = np.loadtxt(shipfilename, delimiter=';',dtype=str)
    reactorfile = np.loadtxt(reactorfilename, delimiter=';',dtype=str)
    power,burnup,enrichment,reactorname = reactorfile[1,1].astype(float),reactorfile[1,2].astype(float),reactorfile[1,3].astype(float),reactorfile[1,0]
    installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname = shipfile[1,1].astype(float),shipfile[1,2].astype(float),shipfile[1,3].astype(float),shipfile[1,4].astype(float),shipfile[1,5].astype(float),shipfile[1,6].astype(float),shipfile[1,0]
    try: # try to initialize with associated country
        countryfile = np.loadtxt(countryfilename, delimiter=';', dtype=str)
        row = countryfile[1, :]

        return PoweredShip(installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname,
                        power,burnup,enrichment,reactorname,
                            countryname=row[0],
                            iso3=row[1],
                            region=row[2],
                            oecd_member=str_to_bool(row[3]),
                            supply=str_to_bool(row[4]),
                            step=row[5],
                            supply_from_year=float(row[6]),
                            capacity=float(row[7]),
                            capacity_unit=row[8],
                            operation=str_to_bool(row[9]),
                            available_from_year=float(row[10]),
                            ports = float(row[11]),
                            ports_names=row[12],
                            latitude=float(row[13]),
                            longitude=float(row[14]),
                            number=number
                            )
    except: # if fail to initialize with country, initialize without
        return PoweredShip(installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname,
                    power,burnup,enrichment,reactorname,
                    countryname=None,
                    iso3=None,
                    region=None,
                    oecd_member=None,
                    supply=None,
                    step=None,
                    supply_from_year=None,
                    capacity=None,
                    capacity_unit=None,
                    operation=None,
                    available_from_year=None,
                    ports = None,
                    ports_names=None,
                    latitude=None,
                    longitude=None,
                    number=number
                    )
def fuelmass_from_burnup(power,time,burnup):
    """
    Calculate reactor fuel mass from burnup.

    Parameters
    ----------
    power : float
        The reactor power [MW].
    time : float
        Operating time [days].
    burnup : float
        Burnup of reactor [GWd/t]
    Returns
    -------
    float
        The fuel mass [metric tons].
    """
    return power*time/(burnup*1e+3)

def feedmass(fuelmass,enrichment,tail_assay,feed_assay):
    """
    Calculate the required feed mass to produce a given fuel mass with given enrichment, with given tail and feed mass assays.

    Parameters
    ----------
    fuelmass : float
        Mass of enriched uranium fuel [kg].
    enrichment : float
        The enrichment of the uranium fuel [decimal].
    tail_assay : float
        Mass assay of tail [decimal].
    feed_assay : float
        Mass assay of feed [decimal].
    Returns
    -------
    float
        Feed mass [kg].
    """
    if (tail_assay<feed_assay) and (enrichment<1 and enrichment>feed_assay):
        return fuelmass*(enrichment-tail_assay)/(feed_assay-tail_assay)
    else:
        raise ValueError("Tail assay must be smaller than feed assay, enrichment must be larger than feed assay but smaller than 1")

def SW(fuelmass,enrichment,tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2): # assume 0.4% tail assay and natural uranium feed for now
    """
    Calculate the separative work needed to produce a certain mass of enriched uranium from natural uranium.

    Parameters
    ----------
    fuelmass : float
        Mass of enriched uranium fuel [kg].
    enrichment : float
        The enrichment of the uranium fuel [decimal].
    tail_assay : float
        Mass assay of tail [decimal].
    feed_assay : float
        Mass assay of feed [decimal].
    Returns
    -------
    float
        Separative work [SWU].
    """
    F =feedmass(fuelmass,enrichment,tail_assay,feed_assay)
    W  = F-fuelmass
    return fuelmass*(1-2*enrichment)*np.log((1-enrichment)/enrichment)+W*(1-2*tail_assay)*np.log((1-tail_assay)/tail_assay)-F*(1-2*feed_assay)*np.log((1-feed_assay)/feed_assay)

def number_from_volume(volume,d_pebble):
    """
    TRISO pebble number from total volume.

    Parameters
    ----------
    volume : float
        Volume of TRISO pebbles [m^3].
    d_pebble: float
        Diameter of TRISO pebble [m]
    Returns
    -------
    int
        Number of TRISO pebbles.
    """
    pebble_number = volume/(np.pi/6*d_pebble**3)
    return pebble_number

def mass_from_volume(volume,d_pebble,m_U_pebble):
    """
    Calculate uranium mass from TRISO pebble volume.

    Parameters
    ----------
    volume : float
        Volume of TRISO pebbles [m^3].
    d_pebble : float
        Diameter of TRISO pebble [m]
    m_U_pebble : float
        Uranium mass in a single fuel pebble [g]

    Returns
    -------
    float
        Uranium mass in pebble [kg].
    """
    pebble_number = number_from_volume(volume,d_pebble)
    fuelmass = pebble_number*(m_U_pebble*1e-3)
    return fuelmass

def str_to_bool(value):
    """Convert txt-file boolean fields to Python booleans."""
    return str(value).strip().lower() == "true"

def str_to_list(value):
    """Convert comma-separated txt fields to a list of strings."""
    value = str(value).strip()
    if value.lower() in ("none", "0", ""):
        return []
    return [x.strip() for x in value.split(",")]

def str_to_float_list(value):
    """Convert comma-separated txt fields to a list of floats."""
    value = str(value).strip()
    if value.lower() in ("none", "0", ""):
        return []
    return [float(x.strip()) for x in value.split(",")]

def str_to_int(value):
    """Convert txt numeric field to integer."""
    return int(float(str(value).strip()))

def init_country_from_file(filename):
    file = np.loadtxt(filename, delimiter=";", dtype=str)
    row = file[1, :]

    return Country(
        name=row[0],
        iso3=row[1],
        region=row[2],
        oecd_member=str_to_bool(row[3]),

        supply=str_to_bool(row[4]),
        step=str_to_list(row[5]),
        supply_from_year=str_to_float_list(row[6]),
        capacity=str_to_float_list(row[7]),
        capacity_unit=str_to_list(row[8]),

        operation=str_to_bool(row[9]),
        available_from_year=str_to_float_list(row[10]),
        ports=str_to_int(row[11]),
        port_names=str_to_list(row[12]),
        latitude=str_to_float_list(row[13]),
        longitude=str_to_float_list(row[14]),
    )

def sigmoid(x,a,midpoint):
    return 1 / (1 + np.exp(-a*(x-midpoint)))