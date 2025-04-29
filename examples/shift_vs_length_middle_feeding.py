# -*- coding: utf-8 -*-

import numpy as np

from electrooptic import optical
from electrooptic import structure
from electrooptic import microwave

import matplotlib.pyplot as pp



'''calculate induced optical phase shift for H structure with middle feeding.

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
    length = np.linspace(1e-5, 814.653e-6, num=501), 
    
    # asymmetry of microwave feeding location
    feeding_asymmetry = 0.0, 
    
    
    # DEFAULT PARAMETERS
    **default
)



optical_path_kw = dict(
    # defines travel orientation of wave packet in ring
    orientation = 'parallel', 
)



# colors for plotting phase shift in different segments
colors = ['#3367d6', '#4285f4', '#7baaf7', '#c6dafc']



def get_optimal_rotation(shift):
    '''calculate rotation rot (|rot| == 1) such that real(shift * rot) reaches maximum.
    
    Parameters
    ----------
    shift: array
    '''
    
    # calculate optimal rotation (see docstring)
    return np.conj(shift) / np.abs(shift)






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



# calculate electrooptic phase shift for one round-trip (total) and in each segment (contributions)
phase_shift_total = optical_path.get_electrooptic_phase_shift(0.0, 'entrance', 'total')
phase_shift_contributions = optical_path.get_electrooptic_phase_shift(0.0, 'entrance', 'contributions')




rot_optimal = get_optimal_rotation(phase_shift_total)



# phase shift in each segment leading to maximum total phase shift
# indices of segments: delay (0), modulation segments (1, 2, 4, 5)
contributions = [
    np.real(phase_shift_contributions[ind_segment] * rot_optimal) 
    for ind_segment in [0, 1, 2, 4, 5]
]


# accumulate phase shifts up to certain segment
contributions_cum = np.cumsum(contributions, axis=0)





fig, ax = pp.subplots()

# plot maximum phase shift for one round-trip versus electrode lengths
ax.plot(structure_kw['length']*1e3, np.abs(phase_shift_total), 'k')


# plot contribution of each segment versus electrode lengths
for k, color in enumerate(colors):
    
    ax.fill_between(
        structure_kw['length']*1e3, 
        contributions_cum[k], contributions_cum[k+1], 
        color=color, 
    )


ax.set_xlabel('electrode length (mm)')
ax.set_ylabel('optical phase shift (rad)')

ax.ticklabel_format(style='sci', axis='y', scilimits=(-1, 1))

ax.set_ylim(0.0, 0.17)


pp.show()
