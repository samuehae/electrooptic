# -*- coding: utf-8 -*-


'''module simplifies building optical and microwave parts of specific modulation structures.'''


import numpy as np

from electrooptic import optical
from electrooptic import microwave
from electrooptic.constants import c_s




# dictionary to flip parameter orientation
FLIPPED_ORIENTATION = {
    'parallel': 'antiparallel', 
    'antiparallel': 'parallel', 
}


# dictionary to flip parameter light_entrance
FLIPPED_LIGHT_ENTRANCE = {
    'source': 'load', 
    'load': 'source', 
}




class HStructureMiddleFeeding:
    '''class defining optical ring resonator with H-shaped microwave electrodes.
    details in [1]
    
    Geometry
    --------
    * ring resonator has two modulating (straight) and two non-modulating 
      (bent) sections
    
    * ring resonator is optically pumped in one bent section (bend a), 
      opposite bend is named as bend b.
    
    * each straight section is covered by two metal electrodes of opposite 
      polarity modelled as transmission lines. positive voltages on the 
      transmission lines lead to E-fields that are parallel (antiparallel) 
      to the crystal axis of the active medium in one (other) section.
    
    * microwaves enter the electrodes in the middle
    
    References
    ----------
    [1] Zhang et al., Nature 568, 373–77 (2019)
    [2] Ghione, Semiconductor Devices for High-Speed Optoelectronics (2009)
    '''
    
    
    def __init__(self, n_r, r_pockels, lambda_o, overlap, gap, alpha_m, nu_m, n_m, z_0, length, 
        z_load_a, z_load_b, fsr, n_o, delay_asymmetry, feeding_asymmetry):
        '''initialize electro-optic structure.
        
        Parameters
        ----------
        n_r: scalar
            refractive index of active material in absence of external field
        
        r_pockels: scalar
            pockels coefficient of active material
        
        lambda_o: scalar
            vacuum wavelength of light
        
        overlap: scalar
            overlap between optical and microwave modes (defined on p. 371 in [2])
        
        gap: scalar
            distance between electrodes
        
        alpha_m: scalar
            linear attenuation constant of microwave field
        
        nu_m: scalar
            microwave frequency
        
        n_m: scalar
            microwave effective index
        
        z_0: scalar
            characteristic impedance of transmission lines
        
        length: scalar or array
            length of modulation section (electrodes) in symmetric case (see feeding_asymmetry)
        
        z_load_a: scalar
            load impedance at transmission lines on side a
        
        z_load_b: scalar
            load impedance at transmission lines on side b
        
        fsr: scalar
            free spectral range of of optical ring
        
        n_o: scalar
            optical group index (see footnote on p. 383 in [2])
        
        delay_asymmetry: scalar in [-1, +1]
            delay in bends normalized to symmetric delay:
            * bend a: 1 + delay_asymmetry
            * bend b: 1 - delay_asymmetry
        
        feeding_asymmetry: scalar in [-1, +1]
            electrode length normalized to symmetric case:
            * side a: 1 + feeding_asymmetry
            * side b: 1 - feeding_asymmetry
        '''
        
        # store parameters
        self.n_r = n_r
        self.r_pockels = r_pockels
        self.lambda_o = lambda_o
        self.overlap = overlap
        self.gap = gap
        
        self.alpha_m = alpha_m
        self.nu_m = nu_m
        self.n_m = n_m
        self.z_0 = z_0
        self.length = length
        self.z_load_a = z_load_a
        self.z_load_b = z_load_b
        
        self.fsr = fsr
        self.n_o = n_o
        self.delay_asymmetry = delay_asymmetry
        self.feeding_asymmetry = feeding_asymmetry
        
        
        # calculate speed of light in waveguide
        self.v_o = c_s / n_o
        
        
        # calculate and store electrode lengths
        self._calculate_lengths()
        
        # calculate and store timings of wave packet
        self._calculate_timing()
        
        # create and store microwave lines and composite network of structure
        self._create_microwave_network()
    
    
    
    def _calculate_lengths(self):
        '''calculate and store electrode lengths.'''
        
        
        # calculate electrode lengths on side a and b
        length_a = (1 + self.feeding_asymmetry) * self.length
        length_b = (1 - self.feeding_asymmetry) * self.length
        
        
        # ensure that lengths are non-negative (physical)
        if not(np.all(length_a >= 0) and np.all(length_b >= 0)):
            raise ValueError('lengths of electrodes must be non-negative.')
        
        
        # store parameters
        self.length_a = length_a
        self.length_b = length_b
    
    
    
    def _calculate_timing(self):
        '''calculate and store timings of wave packet.'''
        
        
        # time wave packet travels through ring (round-trip group delay)
        t_round_trip = 1 / self.fsr
        
        
        # time wave packet travels through an electrode (on side a and b)
        t_electrode_a = self.length_a / self.v_o
        t_electrode_b = self.length_b / self.v_o
        
        
        # time wave packet travels through delay bend in symmetric case
        # helps to calculate delays in present (potentially asymmetric) case
        t_delay_bend = 0.5 * (t_round_trip - 2*t_electrode_a - 2*t_electrode_b)
        
        # time wave packet travels through delay bend (on side a and b)
        t_delay_a = (1 + self.delay_asymmetry) * t_delay_bend
        t_delay_b = (1 - self.delay_asymmetry) * t_delay_bend
        
        
        # ensure that timings are non-negative (physical)
        if not(np.all(t_electrode_a >= 0) and np.all(t_electrode_b >= 0)):
            raise ValueError('travelling time through electrode must be non-negative.')
        
        if not(np.all(t_delay_a >= 0) and np.all(t_delay_b >= 0)):
            raise ValueError('delay time of bends must be non-negative.')
        
        
        # store parameters
        self.t_round_trip = t_round_trip
        self.t_electrode_a = t_electrode_a
        self.t_electrode_b = t_electrode_b
        self.t_delay_a = t_delay_a
        self.t_delay_b = t_delay_b
    
    
    
    def _create_microwave_network(self):
        '''create and store microwave lines and composite network of structure.'''
        
        
        # stores electro-optically active transmission lines of structure
        # relevant for creating modulation segments (see extend_optical_path)
        active_microwave_lines = []
        
        
        # stores load impedance and electrode lengths of transmission lines (on side a and b)
        z_loads = [self.z_load_a, self.z_load_a, self.z_load_b, self.z_load_b]
        lengths = [self.length_a, self.length_a, self.length_b, self.length_b]
        
        
        for z_load, length in zip(z_loads, lengths):
            
            # create microwave termination
            termination = microwave.Termination(z_load)
            
            # create transmission line with termination
            microwave_line = microwave.UniformTransmissionLine(
                self.alpha_m, self.nu_m, self.n_m, self.z_0, length, children=[termination]
            )
            
            # append active transmission line
            active_microwave_lines.append(microwave_line)
        
        
        # create passive network representing microwave part of structure
        self.microwave_structure = microwave.CompositeNetwork(children=active_microwave_lines)
        
        
        # store active transmission lines
        # key: (side, orientation to crystal axis)
        self.active_microwave_lines = {
            ('a', 'parallel'): active_microwave_lines[0], 
            ('a', 'antiparallel'): active_microwave_lines[1], 
            ('b', 'parallel'): active_microwave_lines[2], 
            ('b', 'antiparallel'): active_microwave_lines[3], 
        }
    
    
    
    def get_microwave_structure(self):
        '''get microwave network (microwave.PassiveNetwork) of structure.'''
        
        return self.microwave_structure
    
    
    
    def get_active_microwave_lines(self):
        '''get electro-optically active microwave lines of structure.'''
        
        return self.active_microwave_lines
    
    
    
    def extend_optical_path(self, optical_path: type[optical.OpticalPath], orientation):
        '''extend optical path with modulation segments of structure.
        
        Parameters
        ----------
        optical_path: instance of OpticalPath
            optical path
        
        orientation: {'parallel', 'antiparallel'}
            orientation of modulation segment that wave packet enters first.
            defines sense of circulation of wave packet in ring resonator.
        '''
        
        if not isinstance(optical_path, optical.OpticalPath):
            # optical_path must be instance of OpticalPath
            
            raise TypeError(
                'optical_path must be instance of OpticalPath.\n' \
                f'optical_path: {optical_path}'
            )
        
        
        # check value of parameter orientation
        if orientation not in ['parallel', 'antiparallel']:
            raise ValueError(f'unknown value "{orientation}" for parameter "orientation".')
        
        
        # default parameters of modulation segments
        default_modulation_segment = dict(
            n_r = self.n_r, 
            r_pockels = self.r_pockels, 
            lambda_o = self.lambda_o, 
            overlap = self.overlap, 
            gap = self.gap, 
            n_o = self.n_o, 
        )
        
        
        # add delay segment between ring entrance (middle of bend a) 
        # and first modulation segment
        optical_path.add_optical_segment(
            optical.DelaySegment(self.t_delay_a / 2.0)
        )
        
        
        # add first two modulation segments
        for side, light_entrance in zip(['a', 'b'], ['load', 'source']):
            
            optical_path.add_optical_segment(
                optical.ModulationSegment(
                    light_entrance=light_entrance, 
                    orientation=orientation, 
                    microwave_line=self.active_microwave_lines[side, orientation], 
                    **default_modulation_segment, 
                )
            )
        
        
        # add delay segment for bend b
        optical_path.add_optical_segment(
            optical.DelaySegment(self.t_delay_b)
        )
        
        
        # extract orientation of following modulation segments. 
        # orientation changes due to flipped electrical polarity. 
        orientation = FLIPPED_ORIENTATION[orientation]
        
        
        # add following two modulation segments
        for side, light_entrance in zip(['b', 'a'], ['load', 'source']):
            
            optical_path.add_optical_segment(
                optical.ModulationSegment(
                    light_entrance=light_entrance, 
                    orientation=orientation, 
                    microwave_line=self.active_microwave_lines[side, orientation], 
                    **default_modulation_segment, 
                )
            )
        
        
        # add half delay segment to close round-trip
        optical_path.add_optical_segment(
            optical.DelaySegment(self.t_delay_a / 2.0)
        )





class HStructureSideFeeding:
    '''class defining optical ring resonator with H-shaped microwave electrodes.
    
    Geometry
    --------
    * ring resonator has two modulating (straight) and two non-modulating 
      (bent) sections
    
    * each straight section is covered by two metal electrodes of opposite 
      polarity modelled as transmission lines. positive voltages on the 
      transmission lines lead to E-fields that are parallel (antiparallel) 
      to the crystal axis of the active medium in one (other) section.
    
    * microwaves enter the electrodes on one side (source side) and 
      experience a load impedance on the other side (load side).
    
    * ring resonator is optically pumped either on microwave source side or load side
    
    References
    ----------
    [1] Ghione, Semiconductor Devices for High-Speed Optoelectronics (2009)
    '''
    
    
    def __init__(self, n_r, r_pockels, lambda_o, overlap, gap, 
        alpha_m, nu_m, n_m, z_0, length, z_load, fsr, n_o, delay_asymmetry):
        '''initialize electro-optic structure.
        
        Parameters
        ----------
        n_r: scalar
            refractive index of active material in absence of external field
        
        r_pockels: scalar
            pockels coefficient of active material
        
        lambda_o: scalar
            vacuum wavelength of light
        
        overlap: scalar
            overlap between optical and microwave modes (defined on p. 371 in [1])
        
        gap: scalar
            distance between electrodes
        
        alpha_m: scalar
            linear attenuation constant of microwave field
        
        nu_m: scalar
            microwave frequency
        
        n_m: scalar
            microwave effective index
        
        z_0: scalar
            characteristic impedance of transmission lines
        
        length: scalar or array
            length of modulation section (electrodes) in symmetric case (see feeding_asymmetry)
        
        z_load: scalar
            load impedance at transmission lines
        
        fsr: scalar
            free spectral range of of optical ring
        
        n_o: scalar
            optical group index (see footnote on p. 383 in [1])
        
        delay_asymmetry: scalar in [-1, +1]
            delay in bends normalized to symmetric delay:
            * bend a: 1 + delay_asymmetry
            * bend b: 1 - delay_asymmetry
        '''
        
        # store parameters
        self.n_r = n_r
        self.r_pockels = r_pockels
        self.lambda_o = lambda_o
        self.overlap = overlap
        self.gap = gap
        
        self.alpha_m = alpha_m
        self.nu_m = nu_m
        self.n_m = n_m
        self.z_0 = z_0
        self.length = length
        self.z_load = z_load
        
        self.fsr = fsr
        self.n_o = n_o
        self.delay_asymmetry = delay_asymmetry
        
        
        # calculate speed of light in waveguide
        self.v_o = c_s / n_o
        
        
        # calculate and store timings of wave packet
        self._calculate_timing()
        
        # create and store microwave lines and composite network of structure
        self._create_microwave_network()
    
    
    
    def _calculate_timing(self):
        '''calculate and store timings of wave packet.'''
        
        
        # time wave packet travels through ring (round-trip group delay)
        t_round_trip = 1 / self.fsr
        
        
        # time wave packet travels through an electrode
        t_electrode = self.length / self.v_o
        
        
        # time wave packet travels through delay bend in symmetric case
        # helps to calculate delays in present (potentially asymmetric) case
        t_delay_bend = 0.5 * (t_round_trip - 2*t_electrode)
        
        # time wave packet travels through delay bend (on source and load side)
        t_delay_source_side = (1 + self.delay_asymmetry) * t_delay_bend
        t_delay_load_side = (1 - self.delay_asymmetry) * t_delay_bend
        
        
        # ensure that timings are non-negative (physical)
        if not(np.all(t_delay_source_side >= 0) and np.all(t_delay_load_side >= 0)):
            raise ValueError('delay time of bends must be non-negative.')
        
        
        # store parameters
        self.t_round_trip = t_round_trip
        self.t_electrode = t_electrode
        self.t_delay_source_side = t_delay_source_side
        self.t_delay_load_side = t_delay_load_side
    
    
    
    def _create_microwave_network(self):
        '''create and store microwave lines and composite network of structure.'''
        
        
        # stores electro-optically active transmission lines of structure
        # relevant for creating modulation segments (see extend_optical_path)
        active_microwave_lines = []
        
        
        # create active transmission lines
        for i in range(2):
            
            # create microwave termination
            termination = microwave.Termination(self.z_load)
            
            # create transmission line with termination
            microwave_line = microwave.UniformTransmissionLine(
                self.alpha_m, self.nu_m, self.n_m, self.z_0, self.length, children=[termination]
            )
            
            # append active transmission line
            active_microwave_lines.append(microwave_line)
        
        
        # create passive network representing microwave part of structure
        self.microwave_structure = microwave.CompositeNetwork(children=active_microwave_lines)
        
        
        # store active transmission lines
        # key: orientation to crystal axis
        self.active_microwave_lines = {
            'parallel': active_microwave_lines[0], 
            'antiparallel': active_microwave_lines[1], 
        }
    
    
    
    def get_microwave_structure(self):
        '''get microwave network (microwave.PassiveNetwork) of structure.'''
        
        return self.microwave_structure
    
    
    
    def get_active_microwave_lines(self):
        '''get electro-optically active microwave lines of structure.'''
        
        return self.active_microwave_lines
    
    
    
    def extend_optical_path(self, optical_path: type[optical.OpticalPath], light_entrance, orientation):
        '''extend optical path with modulation segments of structure.
        
        Parameters
        ----------
        optical_path: instance of OpticalPath
            optical path
        
        light_entrance: {'source', 'load'}
            source: light enters ring resonator from side of microwave source
            load: light enters ring resonator from side of microwave load
        
        orientation: {'parallel', 'antiparallel'}
            orientation of modulation segment that wave packet enters first. 
            defines sense of circulation of wave packet in ring resonator.
        '''
        
        if not isinstance(optical_path, optical.OpticalPath):
            # optical_path must be instance of OpticalPath
            
            raise TypeError(
                'optical_path must be instance of OpticalPath.\n' \
                f'optical_path: {optical_path}'
            )
        
        
        # check value of parameter light_entrance
        if light_entrance not in ['source', 'load']:
            raise ValueError(f'unknown value "{light_entrance}" for parameter "light_entrance".')
        
        
        # check value of parameter orientation
        if orientation not in ['parallel', 'antiparallel']:
            raise ValueError(f'unknown value "{orientation}" for parameter "orientation".')
        
        
        # default parameters of modulation segments
        default_modulation_segment = dict(
            n_r = self.n_r, 
            r_pockels = self.r_pockels, 
            lambda_o = self.lambda_o, 
            overlap = self.overlap, 
            gap = self.gap, 
            n_o = self.n_o, 
        )
        
        
        # delay in bent sections as dict
        t_delay = {
            'source': self.t_delay_source_side, 
            'load': self.t_delay_load_side, 
        }
        
        
        # add delay segment between ring entrance and first modulation segment
        optical_path.add_optical_segment(
            optical.DelaySegment(t_delay[light_entrance] / 2.0)
        )
        
        
        # add first modulation segment
        optical_path.add_optical_segment(
            optical.ModulationSegment(
                light_entrance=light_entrance, 
                orientation=orientation, 
                microwave_line=self.active_microwave_lines[orientation], 
                **default_modulation_segment, 
            )
        )
        
        
        # extract light_entrance of following segments
        light_entrance = FLIPPED_LIGHT_ENTRANCE[light_entrance]
        
        
        # extract orientation of following modulation segments. 
        # orientation changes due to flipped electrical polarity. 
        orientation = FLIPPED_ORIENTATION[orientation]
        
        
        # add delay segment for bend
        optical_path.add_optical_segment(
            optical.DelaySegment(t_delay[light_entrance])
        )
        
        
        # add following modulation segment
        optical_path.add_optical_segment(
            optical.ModulationSegment(
                light_entrance=light_entrance, 
                orientation=orientation, 
                microwave_line=self.active_microwave_lines[orientation], 
                **default_modulation_segment, 
            )
        )
        
        
        # extract light_entrance of following segments
        light_entrance = FLIPPED_LIGHT_ENTRANCE[light_entrance]
        
        
        # add half delay segment to close round-trip
        optical_path.add_optical_segment(
            optical.DelaySegment(t_delay[light_entrance] / 2.0)
        )
