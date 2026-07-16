import numpy as np
from matplotlib import pyplot as plt
from utilities import fuelmass_from_burnup,SW,feedmass,init_powered_ship_from_files,sigmoid,mass_from_volume
from outputs import FuelNeeds,InfrastructureNeeds
import math

def model(powered_ships,
          tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2, # assume tail assay of 0.40% and natural uranium as feed as default
          m_U_pebble = 8,
          d_pebble = 6*1e-2,
          geometric_factor = 25 
          ):
    """
    Main function for calculating model outputs for a single year.

    Parameters
    ----------
    powered_ships : list of instances of PoweredShip class
        The input paramaters for the different combinations of ship and reactor.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    m_U_pebble : float
        Uranium mass in a single fuel pebble [g]
    d_pebble: float
        Diameter of TRISO pebble [m]
    geometric_factor: float
        Conversion factor between pebble volume and storage cylinder volume.
    Returns
    -------
    instance of FuelNeeds class
        Fuel related outputs.
    """
    fuel_throughput  = 0.0 # metric tons
    _feedmass = 0.0 # metric tons
    pebble_number = 0.0 # number of fuel pebbles
    waste = 0.0 # m^3 volume of waste pebbles
    swu = 0.0 # SWU 
    for powered_ship in powered_ships:
        # The following returns masses/SWUs needed per year. Must multiply by N_years to get per refueling
        fuelmass  = fuelmass_from_burnup(powered_ship.power,powered_ship.op_time/24,powered_ship.burnup)*powered_ship.total_reactornumber
        fuel_throughput += fuelmass
        swu  += SW(fuelmass*1e+3,powered_ship.enrichment*1e-2,tail_assay,feed_assay)
        _feedmass += feedmass(fuelmass,powered_ship.enrichment*1e-2,tail_assay,feed_assay)
        pebble_number += fuelmass/(m_U_pebble*1e-6)
    waste = pebble_number*np.pi/6*d_pebble**3*geometric_factor # waste volume
    return FuelNeeds(fuel_throughput,swu,_feedmass,pebble_number,waste)

# Deployment over time (2035-2060)
def deployment(scenario,ships_total = 600,N_years = 5,tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2,
               end_year = 2060,phasechange =7,storeyears = 10,steepness = 1.0,
               m_U_pebble = 8,d_pebble = 6*1e-2,m_truck=8.4,geometric_factor = 25):
    """
    Get model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
    N_years : int
        Years between refuelings.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    end_year : int
        Year when deployment ends.
    phasechange : int
        Year after 2035 where phase 2 starts.
    storeyears : int
        Years spent fuel are stored in port.
    steepness : float
        Steepness of sigmoid deployment curve.
    m_U_pebble : float
        Uranium mass in a single fuel pebble [g]
    d_pebble: float
        Diameter of TRISO pebble [m]
    m_truck : float
        Uranium mass per truckload of spent fuel [kg]
    geometric_factor: float
        Conversion factor between pebble volume and storage cylinder volume.
    Returns
    -------
    List of instances of FuelNeeds class
        Fuel related outputs over time.
    List of instances of InfrastructureNeeds class
        Infrastructure related outputs over time.
    List of lists of instances of PoweredShip class
        Fleet composition over time
    List of floats
        Years after 2035.
    """
    def two_phase_deployment(ships_end,phase,year,phasechange,end_year,steepness=1.0):
        """
        Calculate the number of ships in a segment for a year after 2035.

        Parameters
        ----------
        ships_end : float
            Number of ships of this segment at end of deployment.
        phase : int
            Phase number, 1 or 2.
        year : int
            Year after 2035.
        phasechange : int
            Year after 2035 where phase 2 starts.
        end_year : int
            Year where deployment ends.
        steepness : float
            Steepness of sigmoid deployment curve.
        Returns
        -------
        int
            Number of ships of this segment at year {year} after 2035.
        """
        if phase == 1:
            K1 = ships_end
            K2 = 0
        elif phase == 2:
            K1 = 0
            K2 = ships_end
        return round(K1*sigmoid(year,steepness,(end_year-2035)/2)+K2*sigmoid(year,steepness,(end_year-2035+phasechange)/2))
    years = [i for i in range(end_year-2035+1)]# years after 2035
    fleet_shares = np.loadtxt(f"inputs/scenario/scenario_{scenario}.txt",delimiter=';',dtype=str)
    fleet = []
    fuel_needs = []
    infrastructure_needs = []
    ships_in_fleet = [] # total number of ships in fleet per year
    for year in years: # loop over years after 2035
        fleet_i = []
        ships_in_fleet_i = 0
        for j in range(1,len(fleet_shares[:,0])): # loop over ship segments
            shipnumber= two_phase_deployment(fleet_shares[j,1].astype(float)*1e-2*ships_total,
                                                                                    fleet_shares[j,4].astype(int),
                                                                                    year,
                                                                                    phasechange=phasechange,
                                                                                    end_year=end_year,
                                                                                    steepness=steepness)
            ships_in_fleet_i+=shipnumber
            fleet_i.append(init_powered_ship_from_files(f"inputs/ship/ship_{fleet_shares[j,0]}.txt", # ship file
                                                        f"inputs/reactor_{fleet_shares[j,2]}.txt", # reactor file
                                                        f"inputs/country/country_{fleet_shares[j,3]}.txt", # country file
                                                        #number=round(fleet_shares[j,1].astype(float)*1e-2*ships_total*sigmoid(year,1,years[-1]/2)))
                                                        number=shipnumber
                                                        ))
        ships_in_fleet.append(ships_in_fleet_i)
        fleet.append(fleet_i)
        fuel_needs_i = model(fleet_i,tail_assay,feed_assay,m_U_pebble,d_pebble,geometric_factor)
        fuel_needs.append(fuel_needs_i)
        # calculate fresh and spent fuel storage needs
        if year == 0:
            fresh_store=N_years*fuel_needs[year].waste # "waste" is a measure of total pebble volume burnt per year on average
            fuelinit = ships_in_fleet[0]
            fuelinit_tons = N_years*fuel_needs_i.fuel_throughput
            fuelinit_pebbles = N_years*fuel_needs_i.pebble_number
        else:
            fresh_store = N_years*(fuel_needs[year].waste-fuel_needs[year-1].waste)
            fuelinit = ships_in_fleet[year]-ships_in_fleet[year-1]
            fuelinit_tons =  N_years*(fuel_needs[year].fuel_throughput-fuel_needs[year-1].fuel_throughput)
            fuelinit_pebbles =  N_years*(fuel_needs[year].pebble_number-fuel_needs[year-1].pebble_number)
        if year-N_years>=0: # if old ships need refueling
            refuelings = 0
            refueling_tons=0.0
            refueling_pebbles=0
            truckloads_waste = 0
            for n in range(1,math.floor(year/N_years)+1):
                refuelings += infrastructure_needs[year-n*N_years].fuelinit
                refueling_tons += infrastructure_needs[year-n*N_years].fuelinit_tons
                refueling_pebbles += infrastructure_needs[year-n*N_years].fuelinit_pebbles
            fresh_store += infrastructure_needs[year-N_years].fresh_store#N_years*(fuel_needs[year-N_years*(i+1)].waste-fuel_needs[year-N_years*(i+1)-1].waste)
            spent_store = infrastructure_needs[year-1].spent_store+infrastructure_needs[year-N_years].fresh_store # spent fuel storage = fresh fuel storage at refueling
            if year-N_years-storeyears>=0:# remove spent fuel from storage at certain time interval
                spent_store-= infrastructure_needs[year-N_years-storeyears].fresh_store
                truckloads_waste += math.ceil(mass_from_volume(infrastructure_needs[year-N_years-storeyears].fresh_store/geometric_factor,d_pebble,m_U_pebble)/m_truck)
        else:
            spent_store = 0.0
            refuelings = 0
            refueling_tons = 0.0
            refueling_pebbles = 0
            truckloads_waste = 0
        _swu = SW((fuelinit_tons+refueling_tons)*1e+3,fleet_i[0].enrichment*1e-2,tail_assay,feed_assay) # Warning! Only accurate if all reactors use fuel with same enrichment
        _feedmass = feedmass((fuelinit_tons+refueling_tons)*1e+3,fleet_i[0].enrichment*1e-2,tail_assay,feed_assay) # Warning! Only accurate if all reactors use fuel with same enrichment
        infrastructure_needs.append(InfrastructureNeeds(fresh_store,spent_store,
                                                        refuelings,refueling_tons,refueling_pebbles,
                                                        fuelinit,fuelinit_tons,fuelinit_pebbles,truckloads_waste,
                                                        _swu,_feedmass))
    return fuel_needs,infrastructure_needs,fleet,years

def run_scenario(scenario,ships_total = 600,N_years = 5,tail_assay=0.55*1e-2,feed_assay = 0.72*1e-2,
                  end_year=2060,phasechange= 7,storeyears = 10,steepness = 1.0,
                  geometric_factor=25,store_container_height = 2.78,
                  save_deployment=True,save_plots=True,plotting = True):
    """
    Plot model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
    N_years : int
        Years between refuelings.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    end_year : int
        Year when deployment ends.
    phasechange : int
        Year after 2035 where phase 2 starts.
    storeyears : int
        Years spent fuel are stored in port.
    steepness : float
        Steepness of sigmoid deployment curve.
    geometric_factor: float
        Conversion factor between pebble volume and storage cylinder volume.
    store_container_height : float
        Height of fuel storage containers.
    save_deployment : boolean
        Whether to save time development of number of vessels in each ship segment to file.
    Returns
    -------
    void
    """
    # consider adding option for loading stored results from file
    fuel_needs,infrastructure_needs,fleet,years = deployment(scenario,ships_total,N_years,tail_assay,feed_assay,
                                                             end_year=end_year,phasechange=phasechange,storeyears=storeyears,
                                                             steepness=steepness,geometric_factor=geometric_factor)
    # extract data
    fuel_throughput  = [fuel_needs[i].fuel_throughput for i in range(len(fuel_needs))]
    pebble_number  = [fuel_needs[i].pebble_number for i in range(len(fuel_needs))]
    swu = [infrastructure_needs[i].swu for i in range(len(fuel_needs))]
    feedmass = [infrastructure_needs[i].feedmass for i in range(len(fuel_needs))]
    waste  = [fuel_needs[i].waste for i in range(len(fuel_needs))]
    fresh_store = [infrastructure_needs[i].fresh_store for i in range(len(infrastructure_needs))]
    spent_store = [infrastructure_needs[i].spent_store for i in range(len(infrastructure_needs))]
    fuelinit = [infrastructure_needs[i].fuelinit for i in range(len(infrastructure_needs))]
    refuelings = [infrastructure_needs[i].refuelings for i in range(len(infrastructure_needs))]
    fuelinit_tons = [infrastructure_needs[i].fuelinit_tons for i in range(len(infrastructure_needs))]
    refueling_tons = [infrastructure_needs[i].refueling_tons for i in range(len(infrastructure_needs))]
    fuelinit_pebbles = [infrastructure_needs[i].fuelinit_pebbles for i in range(len(infrastructure_needs))]
    refueling_pebbles = [infrastructure_needs[i].refueling_pebbles for i in range(len(infrastructure_needs))]
    truckloads_waste = [infrastructure_needs[i].truckloads_waste for i in range(len(infrastructure_needs))]

    fleet_matrix = np.array(fleet)
    ships_total_over_time = np.zeros(len(fleet_matrix[:,0]))

    # save data in files
    if save_deployment:
        deployment_matrix = []
        deployment_matrix.append([fleet_matrix[0,j].shipname for j in range(len(fleet_matrix[0,:]))])
        for i in range(len(fleet_matrix[:,0])):
            deployment_matrix.append([str(fleet_matrix[i,j].shipnumber) for j in range(len(fleet_matrix[i,:]))])
        np.savetxt(f"outputs/deployment_{scenario}.txt", deployment_matrix,fmt='%s')
    data_matrix = []
    data_matrix.append(["year","fuel throughput [tons]","fuel throughput [pebbles]", "seperative work [SWU]", "feedmass [tons]",
                        "waste [m^3]","fresh fuel storage [m^3]","spent fuel storage [m^3]",
                          "new ships deployed", "number of refuelings", "initial fuel loading [tons]","refueling [tons]",
                          "initial fuel loading [pebbles]", "refueling [pebbles]","truckloads of waste transported"])
    for i in range(len(years)):
        data_matrix.append([years[i]+2035,fuel_throughput[i],pebble_number[i],swu[i],feedmass[i],waste[i],
                            fresh_store[i],spent_store[i],fuelinit[i],refuelings[i],fuelinit_tons[i],refueling_tons[i],
                            fuelinit_pebbles[i],refueling_pebbles[i],truckloads_waste[i]])
    np.savetxt(f"outputs/{scenario}_global_fuel_infrastructure.txt", data_matrix,fmt='%s',delimiter=';')

    if plotting:
        # plot fresh fuel throughput
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        #plt.plot(np.array(years)+2035,np.array(fuel_throughput)/N_years,marker ='o',color='g') # divide by N_years to get yearly value
        #plt.plot(np.array(years)+2035,np.array(pebble_number)/N_years,marker ='s',color='r') 
        ax1.plot(np.array(years)+2035,np.array(fuel_throughput),marker ='o',color='g',label="Uranium")
        ax2.plot(np.array(years)+2035,np.array(pebble_number),marker ='s',color='r',label="TRISO Pebbles")
        plt.title(f"Fuel throughput per year for a {ships_total} ship fleet \n in {scenario} scenario")
        #plt.xlabel("Year")
        #plt.ylabel("tons")
        ax1.set_xlabel("Year")
        ax1.set_ylabel("Tons of uranium")
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax2.set_ylabel("Number of TRISO pebbles")
        ax2.tick_params(axis='y', labelcolor='tab:red')
        if save_plots:
            plt.savefig(f"plots/{scenario}_fuel_throughput.png")
        plt.close()

        # plot separative work
        plt.plot(np.array(years)+2035,np.array(swu)*1e-6,marker='o')
        plt.title(f"Separative work required per year \n in {scenario} scenario\n natural uranium feed, {tail_assay*1e+2:.2f}% tail assay")
        plt.xlabel("Year")
        plt.ylabel("MSWU")
        plt.tight_layout()
        if save_plots:
            plt.savefig(f"plots/{scenario}_swu.png")
        plt.close()

        # plot natural uranium consumption
        plt.plot(np.array(years)+2035,np.array(feedmass)*1e-3,color='m',marker='s')
        plt.title(f"Natural uranium required per year \n in {scenario} scenario, {tail_assay*1e+2:.2f}% tail assay")
        plt.xlabel("Year")
        plt.ylabel("tons")
        if save_plots:
            plt.savefig(f"plots/{scenario}_feedmass.png")
        plt.close()

        # plot waste volume
        plt.plot(np.array(years)+2035,np.array(waste),color='m',marker='s') 
        plt.title(f"Waste production per year \n in {scenario} scenario")
        plt.xlabel("Year")
        plt.ylabel(r"Volume [$m^3$]")
        if save_plots:
            plt.savefig(f"plots/{scenario}_waste.png")
        plt.close()

        # plot truckloads of waste per year
        plt.plot(np.array(years)+2035,np.array(truckloads_waste),color='m',marker='s') 
        plt.title(f"Truckloads of spent fuel moved from interim storage per year\n in {scenario} scenario, {N_years} year refueling interval, {storeyears} year storage")
        plt.xlabel("Year")
        plt.ylabel(r"Number of truckloads")
        if save_plots:
            plt.savefig(f"plots/{scenario}_truckloads_waste.png")
        plt.close()

        # plot fresh fuel storage needs
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(np.array(years)+2035,np.array(fresh_store),color='m',marker='d')
        ax2.plot(np.array(years)+2035,np.array(fresh_store)/store_container_height,color='m',marker='d') 
        plt.title(f"Fresh fuel storage needs per year \n in {scenario} scenario, {N_years} year refueling interval")
        ax1.set_xlabel("Year")
        ax1.set_ylabel(r"Volume [$m^3$]")
        ax1.tick_params(axis='y')#, labelcolor='tab:blue')
        ax2.set_ylabel(r"Floor space [$m^2$]")
        ax2.tick_params(axis='y')#, labelcolor='tab:red')
        fig.tight_layout()
        if save_plots:        
            plt.savefig(f"plots/{scenario}_fresh_store.png")
        plt.close()


        # plot spent fuel storage needs
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(np.array(years)+2035,np.array(spent_store),color='c',marker='o')
        ax2.plot(np.array(years)+2035,np.array(spent_store)/store_container_height,color='c',marker='o')
        plt.title(f"Spent fuel storage needs per year \n in {scenario} scenario, {N_years} year refueling interval, {storeyears} year storage")
        ax1.set_xlabel("Year")
        ax1.set_ylabel(r"Volume [$m^3$]")
        ax1.tick_params(axis='y')#, labelcolor='tab:blue')
        ax2.set_ylabel(r"Floor space [$m^2$]")
        ax2.tick_params(axis='y')#, labelcolor='tab:red')
        fig.tight_layout()
        if save_plots:
            plt.savefig(f"plots/{scenario}_spent_store.png")
        plt.close()

        # Plot ships deployed and ships refueled per year
        plt.plot(np.array(years)+2035,np.array(fuelinit),label = "Ships deployed",color='c',marker='o') 
        plt.plot(np.array(years)+2035,np.array(refuelings),label="Ships refueled",color='m',marker='d')
        plt.plot(np.array(years)+2035,np.array(refuelings)+np.array(fuelinit),label="Total ships serviced",color='y',marker='s')
        #plt.plot(np.array(years)+2035,(np.array(refuelings)+np.array(fuelinit)).mean()*np.ones(len(years)),label="Mean",color='k',linestyle=':')
        plt.title(f"Ships deployed and refueled per year\n in {scenario} scenario, {N_years} year refueling interval")
        plt.xlabel("Year")
        plt.ylabel(r"Number of ships")
        plt.legend()
        plt.tight_layout()
        if save_plots:
            plt.savefig(f"plots/{scenario}_refuelings.png")
        plt.close()

        # Plot initial fuel loadings and refueling amounts per year
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        #plt.plot(np.array(years)+2035,np.array(fuel_throughput)/N_years,marker ='o',color='g') # divide by N_years to get yearly value
        #plt.plot(np.array(years)+2035,np.array(pebble_number)/N_years,marker ='s',color='r') 
        ax1.plot(np.array(years)+2035,np.array(fuelinit_tons),marker ='o',color='g',label="Initial fuel loading")
        ax1.plot(np.array(years)+2035,np.array(refueling_tons),marker ='s',color='r',label="Refueling")
        ax1.plot(np.array(years)+2035,np.array(fuelinit_tons)+np.array(refueling_tons),marker ='^',color='k',linestyle='--',label="Total")
        ax2.plot(np.array(years)+2035,np.array(fuelinit_pebbles),marker ='o',color='g',label="_initial")
        ax2.plot(np.array(years)+2035,np.array(refueling_pebbles),marker ='s',color='r',label="_refuel")
        ax2.plot(np.array(years)+2035,np.array(fuelinit_pebbles)+np.array(refueling_pebbles),marker ='^',color='k',linestyle='--',label="_total")
        plt.title(f"Initial fuel loadings and refuelings per year\n in {scenario} scenario")
        #plt.xlabel("Year")
        #plt.ylabel("tons")
        ax1.set_xlabel("Year")
        ax1.set_ylabel("Tons of uranium")
        ax1.tick_params(axis='y')#, labelcolor='tab:blue')
        ax2.set_ylabel("Number of TRISO pebbles")
        ax2.tick_params(axis='y')#, labelcolor='tab:red')
        fig.legend(loc='upper left', bbox_to_anchor=(0.15, 0.8))
        #fig.tight_layout()
        if save_plots:
            plt.savefig(f"plots/{scenario}_refueling_requirements.png")
        plt.close()

        # plot number of ships
        for j in range(len(fleet_matrix[0,:])):
            shipnumber = np.array([fleet_matrix[i,j].shipnumber for i in range(len(fleet_matrix[:,j]))])
            ships_total_over_time += shipnumber
            plt.plot(np.array(years)+2035,shipnumber,label=fleet_matrix[0,j].shipname)            
        plt.plot(np.array(years)+2035,ships_total_over_time,label="Total",lw =4,color='k')
        plt.title(f"Fleet size over time\n in {scenario} scenario")
        plt.xlabel("Year")
        plt.ylabel("Number of vessels")
        plt.legend()
        if save_plots:
            plt.savefig(f"plots/{scenario}_fleet.png")
        plt.close()
    return

def main():
    scenarios = ["baseline","high-burnup","low-burnup","high-enrichment","low-enrichment","4R","7R","4S","10S"]
    for scenario in scenarios:
        if scenario == "baseline":
            run_scenario(scenario,ships_total=800,end_year=2060,storeyears=5,steepness=0.55,phasechange=7,
                      save_deployment=True,tail_assay=0.4*1e-2,plotting=True)
        elif (scenario[0] in ["4","7"]) or (scenario[0:2]=="10"):
            if scenario[0:2] == "10":
                time = int(scenario[0:2])
                if scenario[2]=="R":
                    run_scenario(scenario,ships_total=800,end_year=2060,storeyears=5,N_years=time,steepness=0.55,phasechange=7,
                                save_deployment=False,tail_assay=0.4*1e-2,plotting=False)
                elif scenario[2]=="S":
                    run_scenario(scenario,ships_total=800,end_year=2060,storeyears=time,N_years=5,steepness=0.55,phasechange=7,
                                save_deployment=False,tail_assay=0.4*1e-2,plotting=False)
                else:
                    print(f"Error: refueling time or storage time change scenario failed, code:{scenario}")
                    break
            else:
                time = int(scenario[0])
                if scenario[1]=="R":
                    run_scenario(scenario,ships_total=800,end_year=2060,storeyears=5,N_years=time,steepness=0.55,phasechange=7,
                                save_deployment=False,tail_assay=0.4*1e-2,plotting=False)
                elif scenario[1]=="S":
                    run_scenario(scenario,ships_total=800,end_year=2060,storeyears=time,N_years=5,steepness=0.55,phasechange=7,
                                save_deployment=False,tail_assay=0.4*1e-2,plotting=False)
                else:
                    print(f"Error: refueling time or storage time change scenario failed, code:{scenario}")
                    break
        else:
            run_scenario(scenario,ships_total=800,end_year=2060,storeyears=5,N_years=5,steepness=0.55,phasechange=7,
                          save_deployment=False,tail_assay=0.4*1e-2,plotting=False)
    
if __name__ == "__main__":
    main()