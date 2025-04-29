# -*- coding: utf-8 -*-


'''module supports defining optical paths in presence of microwave fields.

REFERENCES:
[1] Ghione, Semiconductor Devices for High-Speed Optoelectronics (2009)
'''


import numpy as np
from abc import ABC, abstractmethod

from electrooptic import microwave
from electrooptic.constants import c_s




class AbstractSegment(ABC):
    '''abstract class defining an optical segment.'''
    
    
    @abstractmethod
    def get_transit_time(self):
        '''get transit time of wave packet across segment.'''
    
    
    @abstractmethod
    def get_electrooptic_phase_shift(self, t0):
        '''get optical phase shift induced by electrooptic modulation.
        
        Notes
        -----
        * shift expressed in coordinate system parallel to light propagation
        * sign convention: phase factor on electric field exp(1j*phi)
        '''




class DelaySegment(AbstractSegment):
    '''class defining an optical delay segment without electrodes.'''
    
    
    def __init__(self, t_transit):
        '''initialize delay segment.
        
        Parameters
        ----------
        t_transit: scalar
            transit time of wave packet across segment
        '''
        
        # stores parameters
        self.t_transit = t_transit
    
    
    
    def get_transit_time(self):
        '''get transit time of wave packet across delay segment.'''
        
        return self.t_transit
    
    
    
    def get_electrooptic_phase_shift(self, t0):
        '''get optical phase shift induced by electrooptic modulation.
        
        Parameters
        ----------
        t0: scalar
            time when wave packet enters delay segment
        
        Notes
        -----
        * shift expressed in coordinate system parallel to light propagation
        * sign convention: phase factor on electric field exp(1j*phi)
        '''
        
        return 0




def f(u):
    '''convenience function for compact notation.'''
    return (1 - np.exp(u)) / u



class ModulationSegment(AbstractSegment):
    '''class defining a modulation segment with uniform electrodes.
    
    Assumptions
    -----------
    1) pockels effect dominates over kerr effect
    
    2) applied microwave field E does not change principal axes of active medium, 
       only changes refractive index: n(E) = n_r - n_r^3 * r_pockels / 2 * E
    
    3) optical and microwave fields can be inhomogeneous over interaction region. 
       considered with field overlap integral (defined on p. 371 in [1]).
       
       equivalent uniform electric field E = overlap * voltage / gap
       with voltage and distance (gap) between electrodes
    
    Notes
    -----
    * more details about assumptions in [1], chapter 6.3
    * formulae for electro-optic modulation based on [1], chapter 6.5
    
    [1] Ghione, Semiconductor Devices for High-Speed Optoelectronics (2009)
    '''
    
    
    def __init__(self, n_r, r_pockels, lambda_o, overlap, gap, n_o, light_entrance, 
        orientation, microwave_line: type[microwave.UniformTransmissionLine]):
        '''initialize modulation segment.
        
        Parameters
        ----------
        n_r: scalar
            refractive index of active material in absence of external field
        
        r_pockels: scalar
            pockels coefficient of active material
        
        lambda_o: scalar or array
            vacuum wavelength of light
        
        overlap: scalar
            overlap between optical and microwave modes (defined on p. 371 in [1])
        
        gap: scalar
            distance between electrodes
        
        n_o: scalar or array
            optical group index (see footnote on p. 383 in [1])
        
        light_entrance: {'source', 'load'}
            source: light enters from side of microwave source
            load: light enters from side of microwave load
        
        orientation: {'parallel', 'antiparallel'}
            parallel: optical axis parallel to positive electric field (voltage)
            antiparallel: optical axis antiparallel to positive electric field (voltage)
        
        microwave_line: instance of microwave.UniformTransmissionLine
            transmission line providing microwave field for modulation
        '''
        
        # check value of parameter light_entrance
        if light_entrance not in ['source', 'load']:
            raise ValueError(f'unknown value "{light_entrance}" for parameter "light_entrance".')
        
        
        # check value of parameter orientation
        if orientation not in ['parallel', 'antiparallel']:
            raise ValueError(f'unknown value "{orientation}" for parameter "orientation".')
        
        
        if not isinstance(microwave_line, microwave.UniformTransmissionLine):
            # microwave_line must be instance of microwave.UniformTransmissionLine
            
            raise TypeError(
                'microwave_line must be instance of UniformTransmissionLine.\n' \
                f'microwave_line: {microwave_line}'
            )
        
        
        # stores parameters
        self.n_r = n_r
        self.r_pockels = r_pockels
        self.lambda_o = lambda_o
        
        self.overlap = overlap
        self.gap = gap
        
        self.n_o = n_o
        self.light_entrance = light_entrance
        self.orientation = orientation
        
        self.microwave_line = microwave_line
        
        
        # calculate speed of light in waveguide
        self.v_o = c_s / n_o
    
    
    
    def get_transit_time(self):
        '''get transit time of wave packet across modulation segment.'''
        
        return self.microwave_line.get_length() / self.v_o
    
    
    
    def get_arrival_time(self, t0, x):
        '''get arrival time of wave packet at position.
        
        Parameters
        ----------
        t0: scalar or array
            time when wave packet enters modulation segment
        
        x: scalar or array
            position. value zero at side of microwave source, 
            value length at side of microwave load.
        '''
        
        if self.light_entrance == 'source':
            
            # calculate time when wave packet arrives at location
            t = t0 + x / self.v_o
        
        else: # light_entrance == 'load'
            
            # extract length of modulation segment
            length = self.microwave_line.get_length()
            
            # calculate time when wave packet arrives at location
            t = t0 + (length - x) / self.v_o
        
        return t
    
    
    
    def get_electrooptic_phase_shift(self, t0):
        '''get optical phase shift induced by electrooptic modulation.
        
        Parameters
        ----------
        t0: scalar
            time when wave packet enters modulation segment
        
        Notes
        -----
        * shift expressed in coordinate system parallel to light propagation
        * sign convention: phase factor on electric field exp(1j*phi)
        '''
        
        # extract parameters for convenience
        length = self.microwave_line.get_length()
        alpha_m = self.microwave_line.get_alpha()
        omega_m = self.microwave_line.get_omega()
        
        
        # calculate voltage amplitudes
        v_plus, v_minus = self.microwave_line.get_voltage_amplitudes()
        
        # wave vector of microwave field
        beta_m = self.microwave_line.get_beta()
        
        
        # calculate 'wave vector' of optical field
        # note: uses microwave frequency instead of optical frequency
        beta_o = omega_m / c_s * self.n_o
        
        
        
        if self.light_entrance == 'source':
            # parameter u for waves in +x and -x direction (formula (6.29) in [1])
            # natural unit: 1
            u_plus = 1j * (beta_o - beta_m) * length - alpha_m * length
            u_minus = 1j * (beta_o + beta_m) * length + alpha_m * length
            
            # prefactor of entrance time (part of formula (6.21) in [1])
            # natural unit: 1
            factor_time = np.exp(1j * omega_m * t0)
        
        
        else: # light_entrance == 'load'
            # formulae derived based on [1], chapter 6.5
            
            # parameter u for waves in +x and -x direction
            # natural unit: 1
            u_plus = 1j * (-beta_o - beta_m) * length - alpha_m * length
            u_minus = 1j * (-beta_o + beta_m) * length + alpha_m * length
            
            # prefactor of entrance time
            # natural unit: 1
            factor_time = np.exp(1j * omega_m * t0 + 1j * beta_o * length)
        
        
        # prefactor of material properties (part of formula (6.21) in [1])
        # natural unit: 1/V
        factor_material = np.pi * self.n_r**3 * self.r_pockels / self.lambda_o
        
        
        # prefactor of electrode geometry (part of formula (6.21) in [1])
        # natural unit: 1
        factor_electrode = self.overlap * length / self.gap
        
        # calculate optical phase shift (formula (6.21) in [1])
        # reversed sign compared to [1] (see formula (6.21) and above): phase factor exp(j*phi) not exp(-j*phi) on E-field
        phase_shift = - factor_material * factor_electrode * factor_time * (v_plus * f(u_plus) + v_minus * f(u_minus))
        
        
        if self.orientation == 'antiparallel':
            phase_shift *= -1
        
        return phase_shift





class OpticalPath:
    '''class defining an optical path, a chain of optical segments.'''
    
    
    def __init__(self):
        '''initialize optical path.'''
        
        # stores chain of optical segments
        self.segments = []
        
        # stores transit time of wave packet across optical path
        self.t_transit = 0.0
    
    
    
    def add_optical_segment(self, segment: type[AbstractSegment]):
        '''append segment to optical path.
        
        Parameters
        ----------
        segment: instance of AbstractSegment
            optical segment
        '''
        
        if not isinstance(segment, AbstractSegment):
            # segment must be instance of AbstractSegment
            
            raise TypeError(
                'segment must be instance of AbstractSegment.\n' \
                f'segment: {segment}'
            )
        
        
        # append optical segment
        self.segments.append(segment)
        
        # update transit time by adding transit time of added segment
        self.t_transit += segment.get_transit_time()
    
    
    
    def get_transit_time(self):
        '''get transit time of wave packet across optical path.'''
        
        return self.t_transit
    
    
    
    def get_entrance_times(self, time, location):
        '''get entrance time of wave packet for each segment along optical path.
        
        Parameters
        ----------
        time: scalar
            time at specified location
        
        location: {'entrance', 'exit'}
            entrance: time specified at entrance of optical path
            exit: time specified at exit of optical path
        '''
        
        # calculate entrance time of wave packet into optical path
        if location == 'entrance':
            t0 = time
        
        elif location == 'exit':
            t0 = time - self.t_transit
        
        else:
            raise ValueError(f'unknown value "{location}" for parameter "location".')
        
        
        # stores entrance time of wave packet into each segment
        t_entrance = []
        
        # iterate through segments
        for segment in self.segments:
            
            # append entrance time into segment
            t_entrance.append(t0)
            
            # update entrance time for next segment
            # avoid addition assignment (+=) in case transit time is array
            t0 = t0 + segment.get_transit_time()
        
        return t_entrance
    
    
    
    def get_electrooptic_phase_shift(self, time, location, mode):
        '''get optical phase shift induced by electrooptic modulation.
        
        Parameters
        ----------
        time: scalar
            time at specified location
        
        location: {'entrance', 'exit'}
            entrance: time specified at entrance of optical path
            exit: time specified at exit of optical path
        
        mode: {'total', 'contributions'}
            total: total phase shift of optical path
            contributions: phase shift of each optical segment
        
        Notes
        -----
        * shift expressed in coordinate system parallel to light propagation
        * sign convention: phase factor on electric field exp(1j*phi)
        '''
        
        # get entrance time of wave packet for each segment along optical path
        t_entrance = self.get_entrance_times(time, location)
        
        
        # calculate phase shift induced by electrooptic modulation in each optical segment
        phase_shifts = [
            segment.get_electrooptic_phase_shift(t0) 
            for t0, segment in zip(t_entrance, self.segments)
        ]
        
        
        if mode == 'total':
            # return total phase shift along optical path
            return sum(phase_shifts)
        
        elif mode == 'contributions':
            # return phase shift in each segment
            return phase_shifts
        
        else:
            raise ValueError(f'unknown value "{mode}" for parameter "mode".')
