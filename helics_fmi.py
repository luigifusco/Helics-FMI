import helics as h
import numpy as np
import matplotlib.pyplot as plt
import sys

from fmpy import dump, read_model_description
from pyfmi import load_fmu
import pyfmi.fmi

if __name__ == "__main__":
    fmu_name = sys.argv[1]

    #######  FMU INITIALIZATION  ########
    fmu = load_fmu(fmu_name+'.fmu')
    model_description = fmu.get_description()
    fmiVersion = fmu.get_version()

    start_vrs=False
    start_in_vrs=False
    fmiVersion='xxx'
    start_time = 0
    stop_time = 3600
    if start_vrs:
        fmu.set(list(start_vrs.keys()), list(start_vrs.values()))

    if fmiVersion == '2.0':
        fmu.setup_experiment(start_time=start_time, stop_time=stop_time)
        fmu.enter_initialization_mode()
        if start_in_vrs:
            fmu.set(list(start_in_vrs.keys()), list(start_in_vrs.values()))
        fmu.exit_initialization_mode()
    else:
        if start_in_vrs:
            fmu.set(list(start_in_vrs.keys()), list(start_in_vrs.values()))
        fmu.initialize(start_time=start_time, stop_time=stop_time)
    ################


    #######  FEDERATE CREATION  #########
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, 'zmq')
    h.helicsFederateInfoSetCoreInitString(fedinfo, ' --federates=1')
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 7)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 60)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    fed = h.helicsCreateCombinationFederate(fmu_name, fedinfo)
    #fed = h.helicsCreateValueFederateFromConfig(fmu_name + ".json")
    ################

    #########  PUBS AND SUBS ########
    description = read_model_description(fmu_name+'.fmu')
    inputs = [v.name for v in description.modelVariables if v.causality == 'input']
    outputs = [v.name for v in description.modelVariables if v.causality == 'output']
    print(inputs)
    print(outputs)

    pubid = {}
    for i in range(len(outputs)):
        pub_name = f"{fmu_name}/{outputs[i]}"
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
            fed, pub_name, "double", "X"
        )

    subid = {}
    for i in range(len(inputs)):
        sub_name = f"EXTERNAL/{inputs[i]}"
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

    print(subid)
    print(pubid)

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)

    hours = 24 * 7
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0


    while grantedtime < total_interval:

        requested_time = grantedtime + update_interval
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)

        for i in range(sub_count):
            charging_voltage = h.helicsInputGetDouble((subid[i]))

        for i in range(pub_count):
            h.helicsPublicationPublishDouble(pubid[i], charging_current)


    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()