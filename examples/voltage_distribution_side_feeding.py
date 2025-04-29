# -*- coding: utf-8 -*-

import numpy as np

from electrooptic import optical
from electrooptic import structure
from electrooptic import microwave

import matplotlib.pyplot as pp



'''plot voltage distribution on electrodes at fixed (black) and dynamic (blue) time 
as seen by wave packet for H structure with side feeding.

hint: experiment with the termination (z_load) of the electrodes, 
for example open (np.inf), short-circuited (0 Ohm) and matched (100.0 Ohm) termination.
'''




default = dict(
    # MATERIAL PROPERTIES
    # extraordinary refractive index of LN at 1.55um
    # source: https://refractiveindex.info
    n_r = 2.1376, 
    
    # pockels (electro-optic) coefficient, m/V
    # source: [DOI: 10.1038/s41524-020-00399-z], table 1
    r_pockels = 33e-12, 
    
    # vacuum wavelength of light, in m
    lambda_o = 1.55e-6, 
    
    # overlap between optical and microwave modes
    # global scaling factor irrelevant for behavior
    overlap = 1.0, 
    
    # distance between electrodes, in m
    gap = 7e-6, 
    
    
    # OPTICAL PROPERTIES
    
    # optical group index
    n_o = 2.3, 
    
    # free spectral range, in Hz
    fsr = 40e9, 
    
    
    # MICROWAVE PROPERTIES
    
    # microwave frequency, in Hz
    nu_m = 40e9, 
    
    # characteristic impedance of electrode pair, in Ohm
    z_0 = 100.0, 
    
    # microwave effective index
    n_m = 2.0, 
    
    # linear attenuation constant, in Np/m
    alpha_m = 0.0, 
    
    
    # GEOMETRY
    
    # relative asymmetry of delay bends
    delay_asymmetry = 0.0, 
)



# parameters for H structure with side fed microwaves

structure_kw = dict(
    # MICROWAVE PROPERTIES
    
    # termination impedance at loads, in Ohm
    z_load = np.inf, 
    
    
    # GEOMETRY
    
    # length of one electrode (symmetric case), in m
    # factor two simplifies comparison between middle and side fed structures
    # reason: electrode lengths are defined differently in these two cases
    length = 2 * 450.000e-6, 
    
    
    # DEFAULT PARAMETERS
    **default
)



optical_path_kw = dict(
    # defines side where light enters ring
    light_entrance='source', 
    
    # defines travel orientation of wave packet in ring
    orientation='parallel', 
)






def get_optimal_rotation(shift):
    '''calculate rotation rot (|rot| == 1) such that real(shift * rot) reaches maximum.
    
    Parameters
    ----------
    shift: array
    '''
    
    # calculate optimal rotation (see docstring)
    return np.conj(shift) / np.abs(shift)




def plot_voltage_distribution(axs, optical_path, nu_m):
    
    # calculate electrooptic phase shift for one round-trip (total)
    phase_shift = optical_path.get_electrooptic_phase_shift(0.0, 'entrance', 'total')
    
    
    # calculate rotation to maximize electrooptic phase shift
    rot_optimal = get_optimal_rotation(phase_shift)
    
    # calculate entrance time to maximize electrooptic phase shift
    t0 = np.angle(rot_optimal) / (2*np.pi * nu_m)
    
    # time for plotting fixed voltage distribution
    # entrance time into first electrode segment
    t_static = optical_path.get_entrance_times(t0, 'entrance')[1]
    
    
    # indices of modulation segments for plotting
    # related to order in optical_path
    ind_segments = [1, 3]
    
    
    for ind_segment, ax in zip(ind_segments, axs):
        
        # extract modulation segment and corresponding microwave line
        modulation_segment = optical_path.segments[ind_segment]
        line = modulation_segment.microwave_line
        
        
        # position along electrode, in m
        x = np.linspace(0, line.length, num=101)
        
        
        # voltage distribution at fixed time
        v_static = line.get_distribution(t_static, x, 'voltage', 'total')
        
        
        # calculate entrance time in modulation segment
        t_entrance = optical_path.get_entrance_times(t0, 'entrance')[ind_segment]
        
        # time when light arrives at location, in s
        t_dynamic = modulation_segment.get_arrival_time(t_entrance, x)
        
        # voltage distribution as seen by light along path
        v_dynamic = line.get_distribution(t_dynamic, x, 'voltage', 'total')
        
        
        ax.plot(x, np.real(v_static), 'k')
        ax.plot(x, np.real(v_dynamic), 'blue')
        
        # indicate area of reachable voltages over period of microwave
        ax.fill_between(x, -np.abs(v_static), np.abs(v_static), color='0.6', alpha=0.3, lw=0)







# create structure for building microwave and optical systems
struct = structure.HStructureSideFeeding(**structure_kw)

# extract microwave network of structure
network = struct.get_microwave_structure()



# create microwave source with given open-circuit voltage and internal resistance
source = microwave.SourceOpenVoltage(v_source=1.0, z_source=50.0)

# combine microwave source and network
# relevant to resolve voltage amplitudes in each microwave line
circuit = microwave.Circuit(source, network)




# create optical path for calculating induced optical phase shift
optical_path = optical.OpticalPath()


# extend optical path with present segments in struct (for delay and modulation)
struct.extend_optical_path(optical_path, **optical_path_kw)




fig, axs = pp.subplots(nrows=2, sharex=True, sharey=True)

plot_voltage_distribution(
    [axs[0], axs[1]], 
    optical_path, structure_kw['nu_m']
)


axs[0].set_ylim(-1.01, 1.01)
axs[0].set_yticks([-1, -0.5, 0, 0.5, 1])

for ax in axs:
    ax.grid(visible=True)
    ax.set_ylabel('normalized voltage')

axs[-1].set_xlabel('position (mm)')
axs[-1].ticklabel_format(style='sci', scilimits=(-1, 1), axis='x')


pp.show()
