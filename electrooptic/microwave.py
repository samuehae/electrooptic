# -*- coding: utf-8 -*-


'''module supports microwave calculation of passive one port networks.

REFERENCES:
[1] Bolognesi, Leitungen und Filter (2010)
'''


import numpy as np
from abc import ABC, abstractmethod

from electrooptic.constants import INF
from electrooptic.constants import c_s




class PassiveNetwork(ABC):
    '''abstract class defining a passive one port network. 
    implements component of composite design pattern.'''
    
    
    @abstractmethod
    def get_input_impedance(self):
        '''get input impedance of passive one port network.'''
    
    
    @abstractmethod
    def set_input_voltage(self, v_in):
        '''set voltage at input of passive one port network.
        propagates input voltage to attached passive networks.'''
    
    
    @abstractmethod
    def get_input_voltage(self):
        '''get voltage at input of passive one port network.'''




class Termination(PassiveNetwork):
    '''class defining a microwave termination.
    implements leaf of composite design pattern.'''
    
    
    def __init__(self, z_load):
        '''initialize microwave termination.
        
        Parameters
        ----------
        z_load: scalar
            load impedance of termination
        '''
        
        # store parameters
        # asarray simplifies calculation with np.inf and division by zero
        self.z_load = np.asarray(z_load)
        
        
        # store cached parameters
        self.v_in = None
    
    
    
    def get_input_impedance(self):
        '''get input impedance of microwave termination.'''
        
        return self.z_load
    
    
    
    def set_input_voltage(self, v_in):
        '''set voltage at input of microwave termination.'''
        
        if self.v_in is not None:
            # input voltage is already cached
            # - user called method already
            # - same instance of termination appears more than once in passive network(s)
            
            raise Exception(
                f'input voltage is already cached in instance {self}.\n' \
                'potential reasons:\n' \
                '- user called method already\n' \
                '- same instance of termination appears more than once in passive network(s)'
            )
        
        # cache input voltage
        self.v_in = v_in
    
    
    
    def get_input_voltage(self):
        '''get voltage at input of microwave termination.'''
        
        if self.v_in is None:
            # input voltage is not set
            
            raise ValueError(
                'input voltage must be set previously by calling "set_input_voltage"\n' \
                f'of instance {self}.'
            )
        
        return self.v_in




class CompositeNetwork(PassiveNetwork):
    '''class defining a passive one port network with passive networks attached in parallel as load.
    implements composite of composite design pattern.'''
    
    
    def __init__(self, children: list[type[PassiveNetwork]]):
        '''initialize composite passive one port network.
        
        Parameters
        ----------
        children: list[type[PassiveNetwork]]
            elements attached in parallel to composite network as load
        
        Note
        ----
        - no children correspond to open load at composite network
        - passing children forces network to be built starting with terminations
        '''
        
        # stores children of composite
        self.children = []
        
        # iterate through children and attach them
        for child in children:
            self._attach_child(child)
        
        
        # calculate and store input impedance at port of passive network
        # as network is built from terminations the input impedance will not change anymore
        self.z_in = self._calculate_input_impedance()
        
        
        # store cached parameters
        self.v_in = None
    
    
    
    def _attach_child(self, child: type[PassiveNetwork]):
        '''attach child to composite network as load (in parallel).'''
        
        if not isinstance(child, PassiveNetwork):
            # child must be instance of PassiveNetwork
            
            raise TypeError(
                'child must be instance of PassiveNetwork.\n' \
                f'child: {child}'
            )
        
        # attach child in parallel as load of composite network
        self.children.append(child)
    
    
    
    def _calculate_input_impedance(self):
        '''calculate input impedance at port of passive network.'''
        
        # input impedance of composite network corresponds to its load impedance
        return self.get_load_impedance()
    
    
    
    def get_load_impedance(self):
        '''calculate load impedance of composite network, 
        i.e. combine input impedances of attached passive networks (in parallel).'''
        
        
        # calculate attached load impedances, i.e. input impedances of children
        z_load_children = [child.get_input_impedance() for child in self.children]
        
        
        # calculate attached load admittances
        with np.errstate(divide='ignore'):
            y_load_children = [1.0 / z_load for z_load in z_load_children]
        
        # calculate total load admittance
        y_load = np.sum(y_load_children, axis=0)
        
        
        # calculate total load impedance, i.e. input impedance of composite network
        # ignore 'divide by zero' RuntimeWarning
        with np.errstate(divide='ignore'):
            z_load = 1.0 / y_load
        
        return z_load
    
    
    
    def get_input_impedance(self):
        '''get input impedance of composite network.'''
        
        return self.z_in
    
    
    
    def set_input_voltage(self, v_in):
        '''set voltage at input of composite network.
        propagates input voltage to attached passive networks.'''
        
        
        if self.v_in is not None:
            # input voltage is already cached
            # - user called method already
            # - same instance of composite network appears more than once in passive network(s)
            
            raise Exception(
                f'input voltage is already cached in instance {self}.\n' \
                'potential reasons:\n' \
                '- user called method already\n' \
                '- same instance of composite network appears more than once in passive network(s)'
            )
        
        # cache input voltage
        self.v_in = v_in
        
        
        # children are attached in parallel, thus they have same input voltage
        for child in self.children:
            child.set_input_voltage(v_in)
    
    
    
    def get_input_voltage(self):
        '''get voltage at input of composite network.'''
        
        if self.v_in is None:
            # input voltage is not set
            
            raise ValueError(
                'input voltage must be set previously by calling "set_input_voltage"\n' \
                f'of instance {self}.'
            )
        
        return self.v_in




class UniformTransmissionLine(CompositeNetwork):
    '''class defining a uniform transmission line with passive networks attached in parallel as load.'''
    
    
    def __init__(self, alpha, nu_m, n_m, z_0, length, children: list[type[PassiveNetwork]]):
        '''initialize uniform transmission line with load.
        
        Parameters
        ----------
        alpha: scalar
            linear attenuation constant of microwave field
        
        nu_m: scalar
            microwave frequency
        
        n_m: scalar
            microwave effective index
        
        z_0: scalar
            characteristic impedance of transmission line
        
        length: scalar
            length of transmission line
        
        children: list[type[PassiveNetwork]]
            elements attached in parallel to line as load
        
        
        Note
        ----
        see notes in docstring of CompositeNetwork
        '''
        
        # store parameters
        self.alpha = alpha
        self.nu_m = nu_m
        self.n_m = n_m
        self.z_0 = z_0
        self.length = length
        
        
        # calculate angular frequency
        self.omega = 2 * np.pi * nu_m
        
        # calculate phase constant
        self.beta = 2*np.pi * nu_m / c_s * n_m
        
        # calculate complex propagation constant
        self.gamma = alpha + 1j * self.beta
        
        
        # initialize composite network
        # call after storing parameters as parameters needed to calculate input impedance
        super().__init__(children)
    
    
    
    def _calculate_input_impedance(self):
        '''calculate input impedance at port of uniform transmission line.'''
        
        # calculate load impedance of uniform transmission line
        z_load = self.get_load_impedance()
        
        
        # methods to calculate input impedance from load impedance
        # 1) transformation via reflection amplitudes (formulae (7.10) and (7.12) in [1])
        # 2) direct transformation of impedances (formula (7.8) in [1])
        
        # method 2) is numerically more stable with infinite impedances
        
        
        # normalize load impedance with characteristic impedance
        z_load_norm = z_load / self.z_0
        
        # convert array-like to simplify handling singularity
        z_load_norm = np.asarray(z_load_norm)
        
        # replace infinite by large values to handle singularity
        z_load_norm[np.isinf(z_load_norm)] = INF
        
        
        # calculate electrical length of transmission line
        theta = self.gamma * self.length
        
        
        # calculate and return input impedance, formula (7.8) in [1]
        return (z_load_norm + np.tanh(theta)) / (1 + z_load_norm * np.tanh(theta)) * self.z_0
    
    
    
    def get_length(self):
        '''get length of transmission line.'''
        return self.length
    
    
    
    def get_alpha(self):
        '''get linear attenuation coefficient.'''
        return self.alpha
    
    
    
    def get_beta(self):
        '''get phase constant.'''
        return self.beta
    
    
    
    def get_omega(self):
        '''get angular frequency.'''
        return self.omega
    
    
    
    def get_voltage_amplitudes(self):
        '''get voltage amplitudes V^{+} and V^{-} at input of transmission line.
        see docstring of get_distribution.
        
        Return
        ------
        v_plus: scalar
            voltage amplitude for wave in +x direction
        
        v_minus: scalar
            voltage amplitude for wave in -x direction
        '''
        
        # get input voltage (raises exception if not yet calculated)
        v_in = self.get_input_voltage()
        
        # calculate voltage amplitudes
        v_plus = 0.5 * (1.0 + self.z_0 / self.z_in) * self.v_in
        v_minus = 0.5 * (1.0 - self.z_0 / self.z_in) * self.v_in
        
        return v_plus, v_minus
    
    
    
    def get_current_amplitudes(self):
        '''get current amplitudes I^{+} and I^{-} at input of transmission line.
        see docstring of get_distribution.
        
        Return
        ------
        i_plus: scalar
            current amplitude for wave in +x direction
        
        i_minus: scalar
            current amplitude for wave in -x direction
        '''
        
        # calculate voltage amplitudes
        v_plus, v_minus = self.get_voltage_amplitudes()
        
        # calculate and return current amplitudes
        return v_plus / self.z_0, -v_minus / self.z_0
    
    
    
    def get_distribution(self, t, x, quantity, mode):
        '''get voltage distribution along transmission line.
        
        Parameters
        ----------
        t: scalar or array
            time
        
        x: scalar or array
            position. value zero at side of microwave source, 
            value length at side of microwave load.
        
        quantity: {'voltage', 'current'}
            voltage: distribution of voltage
            current: distribution of current
        
        mode: {'total', 'contributions'}
            total: total field amplitude
            contributions: amplitudes of waves in +x and -x directions
        
        
        Note
        ----
        voltage and current distributions:
        V(x, t) = V^{+} exp(j*omega*t - gamma*x) + V^{-} exp(j*omega*t + gamma*x)
        I(x, t) = I^{+} exp(j*omega*t - gamma*x) + I^{-} exp(j*omega*t + gamma*x)
        
        - voltage amplitude for wave in +x and -x direction: V^{+} and V^{-}
        - curent amplitude for wave in +x and -x direction: I^{+} and I^{-}
        
        - angular frequency of field: omega = 2 * pi * nu
        - complex propagation constant: gamma = alpha + j*beta
        - linear attenuation constant: alpha (Np/m)
        - phase constant: beta (1/m)
        '''
        
        # calculate parameters in exponent
        u_plus = 1j * self.omega * t - self.gamma * x
        u_minus = 1j * self.omega * t + self.gamma * x
        
        
        # calculate amplitudes at input of transmission line
        if quantity == 'voltage':
            amplitude_plus, amplitude_minus = self.get_voltage_amplitudes()
        
        elif quantity == 'current':
            amplitude_plus, amplitude_minus = self.get_current_amplitudes()
        
        else:
            raise ValueError(f'unknown value "{quantity}" for parameter "quantity".')
        
        
        # calculate and return total field or individual contributions
        if mode == 'total':
            return amplitude_plus * np.exp(u_plus) + amplitude_minus * np.exp(u_minus)
        
        elif mode == 'contributions':
            return amplitude_plus * np.exp(u_plus), amplitude_minus * np.exp(u_minus)
        
        else:
            raise ValueError(f'unknown value "{mode}" for parameter "mode".')
    
    
    
    def set_input_voltage(self, v_in):
        '''set voltage at input of uniform transmission line.
        propagates input voltage to attached passive networks.'''
        
        if self.v_in is not None:
            # input voltage is already cached
            # - user called method already
            # - same instance of transmission line appears more than once in passive network(s)
            
            raise Exception(
                f'input voltage is already cached in instance {self}.\n' \
                'potential reasons:\n' \
                '- user called method already\n' \
                '- same instance of transmission line appears more than once in passive network(s)'
            )
        
        # cache input voltage
        self.v_in = v_in
        
        
        # calculate voltage at end of transmission line
        v_out = self.get_distribution(t=0, x=self.length, quantity='voltage', mode='total')
        
        # children are attached in parallel, thus they have same input voltage
        for child in self.children:
            child.set_input_voltage(v_out)






class Source(ABC):
    '''abstract class defining a microwave source.'''
    
    
    @abstractmethod
    def get_output_voltage(self, z_load):
        '''get voltage over load.'''
    
    
    @abstractmethod
    def get_output_current(self, z_load):
        '''get current through load.'''




class SourceOpenVoltage(Source):
    '''class defining source with constant open-circuit voltage.'''
    
    
    def __init__(self, v_source, z_source):
        '''initialize source.
        
        Parameters
        ----------
        v_source: scalar
            open-circuit voltage of source
        
        z_source: scalar
            internal impedance of source
        '''
        
        # stores parameters
        self.v_source = v_source
        self.z_source = z_source
    
    
    
    def get_output_voltage(self, z_load):
        '''get voltage over load.'''
        
        # calculate and return voltage over load
        # note: formula written to allow for infinite z_load
        return self.v_source / (self.z_source / z_load + 1.0)
    
    
    
    def get_output_current(self, z_load):
        '''get current through load.'''
        
        # calculate and return current through load
        # note: formula written to allow for infinite z_load
        return self.v_source / (self.z_source + z_load)




class SourceActivePower(Source):
    '''class defining source with constant active power.'''
    
    
    def __init__(self, p_active, z_source, mode):
        '''initialize source.
        
        Parameters
        ----------
        p_active: scalar
            active (real) power
        
        z_source: scalar
            internal impedance of source
        
        mode: {'source', 'load', 'total'}
            source: active power dissipated in source
            load: active power dissipated in load
            total: active power dissipated in source and load
        '''
        
        # check value of parameter mode
        if mode not in ['source', 'load', 'total']:
            raise ValueError(f'unknown value "{mode}" for parameter "mode".')
        
        
        # stores parameters
        self.p_active = p_active
        self.z_source = z_source
        self.mode = mode
    
    
    
    def get_output_voltage(self, z_load):
        '''get voltage over load.'''
        
        # calculate current through load
        i_load = self.get_output_current(z_load)
        
        # calculate and return voltage over load
        return i_load * z_load
    
    
    
    def get_output_current(self, z_load):
        '''get current through load.'''
        
        # extract resistance (real part of impedance) which dissipates given active power
        if self.mode == 'source':
            resistance = np.real(self.z_source)
        
        elif self.mode == 'load':
            resistance = np.real(z_load)
        
        elif self.mode == 'total':
            resistance = np.real(self.z_source + z_load)
        
        else:
            raise ValueError(f'unknown value "{self.mode}" for parameter "mode".')
        
        
        if np.any(np.isclose(resistance, 0.0)):
            # resistance is zero (nothing dissipates)
            
            raise ValueError(
                'impedance must have nonzero resistance (real part).\n' \
                f'impedance: z_source, z_load or z_source + z_load depending on mode.'
            )
        
        # calculate and return current through load
        # factor two ensures to calculate current amplitude (peak value)
        return np.sqrt(2 * self.p_active / resistance)






class Circuit:
    '''class defining a microwave circuit consisting of source and passive one port network.'''
    
    
    def __init__(self, source: type[Source], network: type[PassiveNetwork]):
        '''initialize microwave circuit.
        
        Parameters
        ----------
        source: instance of Source
            microwave source
        
        network: instance of PassiveNetwork
            passive one port network attached to source
        '''
        
        
        if not isinstance(source, Source):
            # source must be instance of Source
            
            raise TypeError(
                'source must be instance of Source.\n' \
                f'source: {source}'
            )
        
        
        if not isinstance(network, PassiveNetwork):
            # network must be instance of PassiveNetwork
            
            raise TypeError(
                'network must be instance of PassiveNetwork.\n' \
                f'network: {network}'
            )
        
        
        # stores parameters
        self.source = source
        self.network = network
        
        
        # calculate load impedance attached to source, i.e. input impedance of network
        z_load = network.get_input_impedance()
        
        # calculate voltage over load
        v_load = source.get_output_voltage(z_load)
        
        # set input voltage at network
        network.set_input_voltage(v_load)
