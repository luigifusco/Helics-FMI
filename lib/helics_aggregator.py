import pandas as pd
import numpy as np
from math import *
import sys
import json
import helics as h

if __name__ == "__main__":

    command = None
    start_date = pd.to_datetime('2013-07-18 22:00:00+00:00')

    for option in sys.argv:
        if option == '--matlab':
            command = solver_call('matlab')

    sim_name = sys.argv[1]
    input_size = int(sys.argv[2])

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
    pub_name = f"{sim_name}/output"
    pubid[0] = h.helicsFederateRegisterGlobalTypePublication(
        fed, pub_name, "double", "X"
    )

    subid = {}
    for i in range(input_size):
        sub_name = f"{sim_name}/input{i}"
        subid[i] = h.helicsFederateRegisterSubscription(fed, sub_name, "X")
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

    while grantedtime < total_interval:

        requested_time = grantedtime + update_interval
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)

        curtime = grantedtime

        tot_value = 0
        for i in range(sub_count):
            tot_value += h.helicsInputGetDouble((subid[i]))

        var_name = pubid[0].name.split('/')[1]
        h.helicsPublicationPublishDouble(pubid[i], tot_value)




    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()

    if command is not None:
        command.kill()