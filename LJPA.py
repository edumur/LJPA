# This Python file uses the following encoding: utf-8

# Implementation of the Pumpistor model of a flux pumped SQUID in the
# three wave mixing degenerate case ω_p = ω_s + ω_i and ω_p = ω_s.
#
# Based on an article of K. M. Sundqvist et al:
# "The pumpistor: A linearized model of a flux-pumped superconducting
# quantum interference device for use as a negative-resistance parametric
# amplifier"
# APL 109 102603 (2013)

# Copyright (C) 2016 Dumur Étienne
# etienne.dumur@gmail.com

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import numpy as np
import scipy.constants as cst
from scipy.optimize import fsolve
import scipy.optimize as opt

from JPA import JPA


class LJPA(JPA):



    def __init__(self, C, L_s, I_c, phi_s, phi_dc, phi_ac, theta_p,
                 theta_s = 0.):
        """
        Implementation of the LJPA in the three wave mixing degenerate case
        ω_p = ω_s + ω_i and ω_p = ω_s.

        Based on an article of K. M. Sundqvist et al:
        "Design and characterization of a lumped element single-ended
        superconducting microwave parametric amplifier with on-chip
        flux bias line"
        APL 103 122602 (2013)

        ...

        Attributes
        ----------
        C : float
            Resonator capacitance in farad.
        L_s : float
            Resonator stray inductance in henry.
        I_c : float
            Critical current of the SQUID in ampere.
        phi_s : float
            Amplitude of the signal in rad.
        phi_dc : float
            DC amplitude of the pump in weber.
        phi_ac : float
            AC amplitude of the pump in weber.
        theta_p : float
            Phase of the pump in rad.
        theta_s : float, optional
            Phase of the pump in rad, default is zero which implies that that\
            the signal phase is the reference.

        Raises
        ------
        ValueError
            If the parameters are not in the good type.
        """

        if type(C) is not float:
            raise ValueError('C parameter must be float type.')
        if type(L_s) is not float:
            raise ValueError('L_s parameter must be float type')

        JPA.__init__(self, I_c, phi_s, phi_dc, phi_ac, theta_p,
                           theta_s = 0.)

        self.C   = C
        self.L_s = L_s


    def impedance(self, f):
        """
        Return the impedance of the resonator formed by the SQUID, the stray
        inductance and the capacitance.

        Parameters
        ----------
        f : float, np.ndarray
            The frequency in Hz
        """

        o = 2.*np.pi*f

        return 1./(1j*self.C*o + 1./(1j*o*(self.L_s + self.squid_inductance())))


    def angular_resonance_frequency(self):
        """
        Return the angular resonance frequency in rad.Hz of the resonator formed
        by the SQUID, the stray inductance and the capacitance.
        """

        return 1./np.sqrt(self.C*(self.L_s+self.squid_inductance().real))


    def resonance_frequency(self):
        """
        Return the resonance frequency in Hz of the resonator formed by the
        SQUID, the stray inductance and the capacitance.
        """

        return 1./np.sqrt(self.C*(self.L_s+self.squid_inductance().real))/2./np.pi



    def equivalent_resistance(self):
        """
        Return the resistance in ohm of the equivalente resonator formed by the
        SQUID, the stray inductance and the capacitance.
        """

        a = self.squid_inductance().real
        b = self.squid_inductance().imag

        o0 = self.angular_resonance_frequency()

        return -o0*(self.L_s + a)**2./b



    def equivalent_capacitance(self):
        """
        Return the capacitance in farad of the equivalente resonator formed by
        the SQUID, the stray inductance and the capacitance.
        """

        a = self.squid_inductance().real
        b = self.squid_inductance().imag

        o0 = self.angular_resonance_frequency()

        return 2.*self.C - (self.L_s + a)/o0**2./(b**2. + (self.L_s + a)**2.)



    def equivalent_inductance(self):
        """
        Return the inductance in henry of the equivalente resonator formed by
        the SQUID, the stray inductance and the capacitance.
        """

        a = self.squid_inductance().real
        b = self.squid_inductance().imag

        o0 = self.angular_resonance_frequency()

        return (b**2. + (self.L_s + a)**2.)\
              /(2.*self.C*o0**2.*(b**2. + (self.L_s + a)**2.) - self.L_s - a)



    def equivalent_impedance(self, f):
        """
        Return the impedance of the equivalente resonator formed by the SQUID,
        the stray inductance and the capacitance.
        """

        o = 2.*np.pi*f

        return 1./(1./self.equivalent_resistance()\
                   + 1j*o*self.equivalent_capacitance()\
                   + 1./1j/o/self.equivalent_inductance())



    def equivalent_angular_resonance_frequency(self):
        """
        Return the angular resonance frequency in rad.Hz of the equivalent_capacitance
        resonator formed by the SQUID, the stray inductance and the capacitance.
        """

        return 1./np.sqrt(self.equivalent_capacitance()\
                          *self.equivalent_inductance())/2./np.pi



    def equivalent_resonance_frequency(self):
        """
        Return the resonance frequency in Hz of the equivalent resonator formed
        by the SQUID, the stray inductance and the capacitance.
        """

        return 1./np.sqrt(self.equivalent_capacitance()\
                          *self.equivalent_inductance())/2./np.pi



    def internal_quality_factor(self):
        """
        Return the internal quality factor (Qi) of the equivalente resonator
        formed by the SQUID, the stray inductance and the capacitance.
        Since there is not dissipation in the model, Qi is related to the
        flux pumped SQUID more than losses.
        """

        return self.equivalent_resistance()\
               *np.sqrt( self.equivalent_capacitance()\
                        /self.equivalent_inductance())



    def coupling_quality_factor(self, R0=50.):
        """
        Return the coupling quality factor (Qc) of the equivalente resonator
        formed by the SQUID, the stray inductance and the capacitance.

        Parameters
        ----------
        R0 : float, optional
            The characteristic impedance of the incoming line. Assumed to be
            losses line so real and 50 ohm.
        """

        return R0*np.sqrt( self.equivalent_capacitance()\
                           /self.equivalent_inductance())



    def total_quality_factor(self, R0=50.):
        """
        Return the total quality factor (Q0) of the equivalente resonator
        formed by the SQUID, the stray inductance and the capacitance.

        Parameters
        ----------
        R0 : float, optional
            The characteristic impedance of the incoming line. Assumed to be
            losses line so real and 50 ohm.
        """

        return 1./(  1./self.internal_quality_factor()\
                   + 1./self.coupling_quality_factor(R0))



    def find_fwhm(self, span=10e9):
        """
        Return the half width at half maximum in Hz of the power reflection.
        Numerically estimated.

        Parameters
        ----------
        span : float, optional
            The span in which the fwhm is calculated in Hz.
        """

        f0 = self.resonance_frequency()
        f = np.linspace(f0-span/2., f0+span/2., 1e6)
        y = abs(self.reflection(f))**2.
        half_max = y.max()/2
        f1 = f[abs(y[:len(y)/2] - half_max).argmin()]
        f2 = f[len(y)/2 + abs(y[len(y)/2:] - half_max).argmin()]

        return f2 - f1



    def find_angular_resonance_frequency(self, span=10e9):
        """
        Return the angular resonance frequency in Hz of the power reflection.
        Numerically estimated.

        Parameters
        ----------
        span : float, optional
            The span in which the fwhm is calculated in Hz.
        """

        o0 = self.resonance_frequency()
        o = np.linspace(o0-span/2., o0+span/2., 1e6)
        y = abs(self.reflection(o))**2.

        return o[y.argmax()]



    def find_resonance_frequency(self, span=10e9):
        """
        Return the resonance frequency in Hz of the power reflection.
        Numerically estimated.

        Parameters
        ----------
        span : float, optional
            The span in which the fwhm is calculated in Hz.
        """

        f0 = self.resonance_frequency()
        f = np.linspace(f0-span/2., f0+span/2., 1e6)
        y = abs(self.reflection(f))**2.

        return f[y.argmax()]



    def optimized_squid_inductance_imag(self, R0=50.):
        """
        Return the imaginary part of the SQUID inductance for which the
        internal quality factor equalizes the coupling quality factor.

        Parameters
        ----------
        R0 : float, optional
            The characteristic impedance of the incoming line. Assumed to be
            losses line so real and 50 ohm.
        """

        a = self.squid_inductance().real

        return (R0 - np.sqrt(R0**2. - 4.*np.sqrt((self.L_s + a)**3./self.C)))/2.



    def find_max_gain(self, span=10e9, scale='log'):
        """
        Return the maximum power gain.
        Numerically estimated.

        Parameters
        ----------
        span : float, optional
            The span in which the fwhm is calculated in Hz.
        scale: {log, linear}, optional
            The power reflection will be returned in log or linear scale.

        Raises
        ------
        ValueError
            If the parameters are not in the good type.
        """

        if scale not in ('log', 'linear'):
            raise ValueError("Parameter 'scale' must be 'log' or 'linear'")

        f0 = self.resonance_frequency()
        f = np.linspace(f0-span/2., f0+span/2., 1e6)
        y = abs(self.reflection(f))**2.

        if scale.lower() == 'log':
            return 10.*np.log10(y.max())
        elif scale.lower() == 'linear':
            return y.max()



    def optimized_resonator_capacitance(self, R0=50.):
        """
        Return the resonator capacitance for which the internal quality factor
        equalizes the coupling quality factor.

        Parameters
        ----------
        R0 : float, optional
            The characteristic impedance of the incoming line. Assumed to be
            losses line so real and 50 ohm.
        """

        a = self.squid_inductance().real
        b = self.squid_inductance().imag

        return (self.L_s + a)**3./b**2./(b - R0)**2.



    def test(self, f0, Qc, update_parameters=False):
        """
            Work on progress:
                Find parameters for given f0 and Qc.
        """

        def func(x):

            phi_ac, C, L_s = x

            self.phi_ac = abs(phi_ac)
            self.C   = abs(C)
            self.L_s = abs(L_s)

            current_f0 = self.find_resonance_frequency()
            current_Qc = self.coupling_quality_factor()
            current_Qi = self.internal_quality_factor()
            print phi_ac, C, L_s
            print current_f0, current_Qc, current_Qi
            print current_f0 - f0,\
                   current_Qc - Qc,\
                   current_Qi + Qc
            print ''

            return current_f0 - f0,\
                   current_Qc - Qc,\
                   current_Qi + Qc

        backup_phi_ac = self.phi_ac
        backup_C   = self.C
        backup_L_s = self.L_s

        # results = abs(opt.newton_krylov(func, [self.phi_ac, self.C, self.L_s]))
        results = abs(opt.fsolve(func, [self.phi_ac, self.C, self.L_s]))
        # , args=(f0, Qc)))

        if not update_parameters:

            self.phi_ac = backup_I_c
            self.C   = backup_C
            self.L_s = backup_L_s

        return results



    def reflection(self, f, z0=50.):
        """
        Return the reflection of the LJPA.

        Parameters
        ----------
        f : float, np.ndarray
            The frequency in hertz.
        z0 : float, optional
            The characteristic impedance of the transmission line connected to
            the SQUID, default is 50 Ω.

        Raises
        ------
        ValueError
            If the parameters are not in the good type
        """

        if type(f) in (str, list, dict):
            raise ValueError('f parameter must be float or np.ndarray type')

        return  (self.impedance(f) - z0)\
               /(self.impedance(f) + z0)



    def _parse_number(self, number, precision, inverse = False):

        power_ten = int(np.log10(abs(number)))/3*3

        if power_ten >= -24 and power_ten <= 18 :

            prefix = {-24 : 'y',
                      -21 : 'z',
                      -18 : 'a',
                      -15 : 'p',
                      -12 : 'p',
                       -9 : 'n',
                       -6 : 'µ',
                       -3 : 'm',
                        0 : '',
                        3 : 'k',
                        6 : 'M',
                        9 : 'G',
                       12 : 'T',
                       15 : 'p',
                       18 : 'E'}

            if inverse:
                return str(round(number*10.**-power_ten, precision)),\
                       prefix[-power_ten]
            else:
                return str(round(number*10.**-power_ten, precision)),\
                       prefix[power_ten]
        else:
            return str(round(number, precision)), ''



    def __str__(self):

        Ic_p, Ic_t = self._parse_number(self.I_c, 3)
        delta_theta_p, delta_theta_t = self._parse_number(self.delta_theta()/np.pi, 3)
        phi_s_p, phi_s_t = self._parse_number(self.phi_s/cst.hbar*2.*cst.e, 3)
        phi_dc_p, phi_dc_t = self._parse_number(self.phi_dc/cst.hbar*2.*cst.e, 3)
        phi_ac_p, phi_ac_t = self._parse_number(self.phi_ac/cst.hbar*2.*cst.e, 3)

        C_p, C_t = self._parse_number(self.C, 3)
        Ls_p, Ls_t = self._parse_number(self.L_s, 3)



        return '------------------------------------------------------------\n'\
               'LJPA instanced with following parameters:\n'\
               '\n'\
               '    Pumpistor parameters:\n'\
               '        SQUID critical current:       '+Ic_p+' '+Ic_t+'A\n'\
               '        Signal-pump phase difference: '+delta_theta_p+' '+delta_theta_t+'π\n'\
               '        Signal amplitude:             '+phi_s_p+' '+phi_s_t+'Φ0\n'\
               '        DC pump amplitude:            '+phi_dc_p+' '+phi_dc_t+'Φ0\n'\
               '        AC pump amplitude:            '+phi_ac_p+' '+phi_ac_t+'Φ0\n'\
               '\n'\
               '    Resonator parameters:\n'\
               '        Capacitance:      '+C_p+' '+C_t+'F\n'\
               '        Stray inductance: '+Ls_p+' '+Ls_t+'H\n'\
               '------------------------------------------------------------\n'


    def print_result(self):

        f0_p, f0_t = self._parse_number(self.find_resonance_frequency(), 3)
        fwhm_p, fwhm_t = self._parse_number(self.find_fwhm(), 3)
        max_gain_p, max_gain_t = self._parse_number(self.find_max_gain(scale='log'), 3)
        Qi_p, Qi_t = self._parse_number(self.internal_quality_factor(), 3)
        Qc_p, Qc_t = self._parse_number(self.coupling_quality_factor(), 3)

        return '------------------------------------------------------------\n'\
               '                       Results:\n'\
               '\n'\
               '    Resonator:\n'\
               '        Resonance frequency:     '+f0_p+' '+f0_t+'Hz\n'\
               '        FWHM:                    '+fwhm_p+' '+fwhm_t+'Hz\n'\
               '        Max gain:                '+max_gain_p+' '+max_gain_t+'dB\n'\
               '        Internal quality factor: '+Qi_p+' '+Qi_t+'\n'\
               '        Coupling quality factor: '+Qc_p+' '+Qc_t+'\n'\
               '------------------------------------------------------------\n'