# -*- coding: utf-8 -*-

import numpy as np

from electrooptic import optical
from electrooptic import structure
from electrooptic import microwave

import matplotlib.pyplot as pp



'''plot voltage distribution on electrodes at fixed (black) and dynamic (green) time 
as seen by wave packet for H structure with middle feeding.

hint: experiment with the terminations (z_load_a and z_load_b) of the electrodes, 
for example open (np.inf), short-circuited (0 Ohm) and matched (100.0 Ohm) terminations.
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



# parameters for H structure with middle fed microwaves

structure_kw = dict(
    # MICROWAVE PROPERTIES
    
    # termination impedance at loads, in Ohm
    # both lines with terminations on side a (side of optical feeding)
    z_load_a = np.inf, 
    
    # both lines with terminations on side b (opposite side to side with optical feeding)
    z_load_b = np.inf, 
    
    
    # GEOMETRY
    
    # length of one electrode (symmetric case), in m
    length = 450.000e-6, 
    
    # asymmetry of microwave feeding location
    feeding_asymmetry = 0.0, 
    
    
    # DEFAULT PARAMETERS
    **default
)



optical_path_kw = dict(
    # defines travel orientation of wave packet in ring
    orientation = 'parallel', 
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
    ind_segments = [1, 2, 4, 5]
    
    # orientation of x axis
    x_flips = [-1, 1, 1, -1]
    
    
    for ind_segment, ax, x_flip in zip(ind_segments, axs, x_flips):
        
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
        
        
        ax.plot(x_flip * x, np.real(v_static), 'k')
        ax.plot(x_flip * x, np.real(v_dynamic), 'green')
        
        # indicate area of reachable voltages over period of microwave
        ax.fill_between(x_flip * x, -np.abs(v_static), np.abs(v_static), color='0.6', alpha=0.3, lw=0)




# create structure for building microwave and optical systems
struct = structure.HStructureMiddleFeeding(**structure_kw)

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
    [axs[0], axs[0], axs[1], axs[1]], 
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
