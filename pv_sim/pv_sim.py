import pandas as pd
import numpy as np
from math import *
import pvlib as pv
import dec

np.seterr(divide='ignore', invalid='ignore')

class PVmodel:
	"""docstring for PVmodel"""
	def __init__(self, P_system=1000 ,slope=20,aspect=270,latitude=45.06,longitude=7.66,elevation=250,
				Tc_noct=45,T_ex_noct=20,a_p=0.0038,ta=0.9,P_module=283,
				G_noct=800,G_stc=1000,Area=1.725,Tc_stc=25.0):
		self.slope=slope #from horizontal
		self.aspect=aspect #from north
		self.latitude=latitude
		self.longitude=longitude
		self.elevation=elevation
		self.Tc_stc=Tc_stc+273.15
		self.Tc_noct=Tc_noct+273.15
		self.T_ex_noct=T_ex_noct+273.15
		self.a_p=a_p
		self.ta=ta
		self.P_module=P_module
		self.G_noct=G_noct
		self.G_stc=G_stc
		self.Area=Area
		self.n_mp_stc=P_module/Area/G_stc#*(1-7*0.01)
		self.P_sytem=P_system
		self.ghi=0
		self.T_ext=0
		self.time=0
		self.gti=0
		self.power_dc=0
		self.size=self.P_sytem/self.P_module*self.Area

	def step(self):
		data=pd.DataFrame(data=self.ghi,index=[self.time],columns=['ghi']) 
		self.gti=dec.main(data,self.latitude,self.longitude,self.elevation,self.slope,self.aspect).values[0]
		T_sol=self.T_ext+273.15+0.05*self.gti
		Tc=T_sol+(self.Tc_noct-self.T_ex_noct)*(self.gti/self.G_noct)*(1-(self.n_mp_stc*(1-self.a_p*self.Tc_stc)/self.ta))/(1+(self.Tc_noct-self.T_ex_noct)*(self.gti/self.G_noct)*(self.a_p*self.n_mp_stc/self.ta))
		n_mp=self.n_mp_stc*(1-self.a_p*(Tc-self.Tc_stc))
		self.power_dc=self.size*self.gti*n_mp
		

class PVsimulator(object):

	def __init__(self):
		self.models = []
		self.data = []

	def add_PV(self, P_system, slope, aspect, latitude, longitude,
                                  elevation,
                                  Tc_noct, T_ex_noct, a_p, ta, P_module,
                                  G_noct, G_stc, Area, Tc_stc):
		"""Create an instances of ``Model`` with *init_val*."""
		model = PVmodel(P_system=P_system ,slope=slope,aspect=aspect,latitude=latitude,longitude=longitude,
						elevation=elevation,
				Tc_noct=Tc_noct,T_ex_noct=T_ex_noct,a_p=a_p,ta=ta,P_module=P_module,
				G_noct=G_noct,G_stc=G_stc,Area=Area,Tc_stc=Tc_stc)
		self.models.append(model)
		self.data.append([])  # Add list for simulation data


	def step(self, ghi=None, T_ext=None, sim_time=None):

		for i, model in enumerate(self.models):
			model.ghi=ghi
			model.T_ext=T_ext
			model.time=sim_time
			model.step()
			self.data[i].append(model.power_dc)