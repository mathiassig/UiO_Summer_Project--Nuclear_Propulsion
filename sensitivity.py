import numpy as np
import matplotlib.pyplot as plt
def matrix_to_dictionary(matrix):
    """
    Convert 2D matrix to dictionary with column keys.

    Parameters
    ----------
    matrix : nested list
        2D matrix.
    Returns
    -------
    dict:
        Dictionary with column keys.
    """
    data_dict = {matrix[0,idx]: list(col) for idx, col in enumerate(zip(*matrix[1:,:]))}
    
    return data_dict
def tornadoplot(low_values,high_values,base_value,value_label,variables = ['Reactor burnup','Fuel enrichment', 'Refueling interval', 'Spent fuel storage time']):
    """
    Make tornado plot.

    Parameters
    ----------
    low_values : iterable
        Values for lower estimate of different input variables.
    high_values : iterable
        Values for lower estimate of different input variables.
    base_value: float
        Baseline value.
    value_label: tuple of strings
        (Name of the output variable being analyzed, Unit).
    variables: iterable of strings
        Names of input variables.
    Returns
    -------
    void
    """
    # 1. Define your data
    #base_value = 100  # The baseline/central reference point

    # Values representing the output when the variable is at its 'Low' and 'High' state
    #low_values = np.array([85, 90, 95, 80])
    #high_values = np.array([120, 115, 108, 105])

    # Calculate distances from the baseline
    low_widths = low_values - base_value
    high_widths = high_values - base_value

    # Sort by the largest overall impact (the "tornado" effect)
    total_range = np.abs(high_values - low_values)
    sorted_indices = np.argsort(total_range)

    variables = [variables[i] for i in sorted_indices]
    low_widths = low_widths[sorted_indices]
    high_widths = high_widths[sorted_indices]

    # 2. Plotting
    fig, ax = plt.subplots(figsize=(8, 5))

    # Draw the low and high impact bars using the 'left' parameter
    bar_low = ax.barh(variables, low_widths, left=base_value, color='#0072B2', label='Low Estimate')
    bar_high = ax.barh(variables, high_widths, left=base_value, color='#D55E00', label='High Estimate')

    # Add a vertical baseline
    ax.axvline(base_value, color='black', linestyle='--', linewidth=1.5,label="Baseline")

    # Formatting
    ax.set_title(f'Sensitivity analysis of {value_label[0]}', fontsize=14, pad=15)
    ax.set_xlabel(f'{value_label[0]} [{value_label[1]}]', fontsize=12)
    ax.grid(axis='x', linestyle=':', alpha=0.6)
    ax.legend(loc='lower right')

    # Remove top and right borders for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"outputs/sensitivity_{value_label[0]}.png")
    plt.close()
def is_even(number):
    return (number & 1) == 0
def step_function(x):
    return np.where(x >= 0, 1, 0)
def is_string(a):
    if type(a) == str:
        return True
    else:
        return False
def main():
    scenarios = ["baseline","high-burnup","low-burnup","high-enrichment","low-enrichment","7R","4R","10S","4S"] # make sure that scenarios[0] is baseline, odd index is high and even index is low
    data = {}
    for scenario in scenarios:
        data[scenario] = matrix_to_dictionary(np.loadtxt(f"outputs/{scenario}_global_fuel_infrastructure.txt",delimiter=';',dtype=str))
    value_labels = [("Separative work","SWU"),("Fuel requirements","tons of uranium"),("Truckloads","number of transport casks"),("Storage needs",r"$m^3$")]
    for value_label in value_labels:
        # extract data
        if value_label[0] == "Separative work":
            key1 = "seperative work [SWU]"
            key2 = None
        elif value_label[0] == "Fuel requirements":
            key1 = "initial fuel loading [tons]"
            key2 = "refueling [tons]"
        elif value_label[0] == "Truckloads":
            key1 = "truckloads of waste transported"
            key2 = None
        elif value_label[0] == "Storage needs":
            key1 = "fresh fuel storage [m^3]"
            key2 = "spent fuel storage [m^3]"
        low_values,high_values = [],[]
        base_value = None
        for i in range(len(scenarios)):
            temp = (np.array(data[scenarios[i]][key1],dtype=float)).max()
            if is_string(key2):
                temp+= (np.array(data[scenarios[i]][key2],dtype=float)).max()
            if i==0:
                base_value = temp
            elif is_even(i):
                low_values.append(temp)
            else:
                high_values.append(temp)
        low_values = np.array(low_values)
        high_values = np.array(high_values)
        tornadoplot(low_values,high_values,base_value,value_label,variables = ['Reactor burnup','Fuel enrichment', 'Refueling interval', 'Spent fuel storage time'])
if __name__ == "__main__":
    main()