import numpy as np
from reactor import Reactor
from ship import Ship

def init_reactor_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    power,burnup,enrichment,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,0]
    return Reactor(power,burnup,enrichment,name)

def init_ship_from_file(filename):
    return

Allseas = init_reactor_from_file("inputs/reactor_allseas.txt")
print(Allseas)