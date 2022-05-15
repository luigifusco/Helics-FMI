import pandas as pd
import numpy as np
from math import *
import dec
import sys
import json
import helics as h

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
		


def step(model, sim_time=None):
    model.time=sim_time
    model.step()

    return model.power_dc


if __name__ == "__main__":

    command = None
    start_date = pd.to_datetime('2013-07-18 22:00:00+00:00')

    for option in sys.argv:
        if option == '--matlab':
            command = solver_call('matlab')

    sim_name = sys.argv[1]

    model = PVmodel()

    with open(sim_name+'.json') as file:
        json_config = json.load(file)

    total_interval = json_config.get('total_interval', 0)
    ################


    #######  FEDERATE CREATION  #########
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, 'zmq')
    h.helicsFederateInfoSetCoreInitString(fedinfo, ' --federates=1')
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 7)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, json_config['period'])
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    for o in sys.argv:
        if o.startswith('--broker'):
            h.helicsFederateInfoSetBroker(fedinfo, o.split('=')[1])
    fed = h.helicsCreateCombinationFederate(sim_name, fedinfo)
    ################

    #########  PUBS AND SUBS ########
    pubid = {}
    pub_name = f"{sim_name}/powerOutput.real"
    pubid[0] = h.helicsFederateRegisterGlobalTypePublication(
        fed, pub_name, "double", "X"
    )

    subid = {}
    mappings = list(json_config['mappings'].items())
    for i in range(len(mappings)):
        sub_name = mappings[i][1]
        subid[i] = h.helicsFederateRegisterSubscription(fed, sub_name, "X")

    reverse_mappings = {}
    for m in mappings:
        if m[1] not in reverse_mappings:
            reverse_mappings[m[1]] = []
        reverse_mappings[m[1]].append(m[0])
    ################


    federate_name = h.helicsFederateGetName(fed)

    sub_count = h.helicsFederateGetInputCount(fed)
    pub_count = h.helicsFederateGetPublicationCount(fed)

    subid = {}
    for i in range(sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsSubscriptionGetTarget(subid[i])

    pubid = {}
    for i in range(pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pubid[i])


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)

    hours = 24 * 7
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    curtime = 0
    grantedtime = 0

    ghi_sub = h.helicsFederateRegisterSubscription(fed, 'Apartment/weaBus.HGloHor', "X")
    t_ext_sub = h.helicsFederateRegisterSubscription(fed, 'Apartment/weaBus.TDryBul', "X")

    while grantedtime < total_interval:

        requested_time = grantedtime + update_interval
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)

        step(model, start_date + pd.Timedelta(grantedtime, unit='s'))

        curtime = grantedtime

        model.ghi = h.helicsInputGetDouble(ghi_sub)
        model.T_ext = h.helicsInputGetDouble(t_ext_sub)

        var_name = pubid[0].name.split('/')[1]
        var_value = model.power_dc
        h.helicsPublicationPublishDouble(pubid[i], var_value)




    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()

    if command is not None:
        command.kill()