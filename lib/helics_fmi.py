import helics as h
import sys

from fmpy import dump, read_model_description
from pyfmi import load_fmu
import pyfmi.fmi
from time import time

import json

def solver_call(solver, num=1):
    # TODO: da migliorare perchè la path non è relativa e bosonga installare matlab
    if solver == 'matlab':
        print(f'Starting solver {solver} #{num}.')
        command = Popen(["/usr/local/MATLAB/R2021b/toolbox/shared/fmu_share/script/fmu-matlab-setup",
                                f'{num}'], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        while command.stdout.readline().decode('utf-8').split('.')[0] != f'Launched MATLAB #{num}':
            pass

        print(f'Launched MATLAB #{num}')

        return command

if __name__ == "__main__":

    command = None
    logg = False
    gettimes = False

    times = {}

    for option in sys.argv:
        if option == '--matlab':
            command = solver_call('matlab')
        if option == '--log':
            logg = True
        if option == '--time':
            gettimes = True

    init_time = time()
    sim_name = sys.argv[1]

    with open(sim_name+'.json') as file:
        json_config = json.load(file)

    #######  FMU INITIALIZATION  ########
    fmu = load_fmu(json_config['fmu'], kind='CS')
    model_description = fmu.get_description()
    fmiVersion = fmu.get_version()

    start_vrs = json_config.get('start_vrs', False)
    start_in_vrs = json_config.get('start_in_vrs', False)
    fmiVersion = json_config.get('fmiVersion', '2.0')
    start_time = json_config.get('start_time', 0)
    total_interval = json_config.get('total_interval', 0)
    log_vars = json_config.get('log_vars', [])
    if log_vars == []:
        logg = False
    if start_vrs:
        fmu.set(list(start_vrs.keys()), list(start_vrs.values()))


    if fmiVersion == '2.0':
        fmu.setup_experiment(start_time=start_time, stop_time=total_interval)
        fmu.enter_initialization_mode()
        if start_in_vrs:
            fmu.set(list(start_in_vrs.keys()), list(start_in_vrs.values()))
        fmu.exit_initialization_mode()
    else:
        if start_in_vrs:
            fmu.set(list(start_in_vrs.keys()), list(start_in_vrs.values()))
        fmu.initialize(start_time=start_time, stop_time=total_interval)
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
            print("CONNECTING TO: " + o.split('=')[1])
            h.helicsFederateInfoSetBroker(fedinfo, o.split('=')[1])
    fed = h.helicsCreateCombinationFederate(sim_name, fedinfo)
    ################

    #########  PUBS AND SUBS ########
    description = read_model_description(json_config['fmu'])
    inputs = [v.name for v in description.modelVariables if v.causality == 'input']
    outputs = [v.name for v in description.modelVariables if v.causality == 'output']

    print(inputs)
    print(outputs)

    pubid = {}
    for i in range(len(outputs)):
        pub_name = f"{sim_name}/{outputs[i]}"
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
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

    times['init_time'] = time() - init_time
    ##############  Entering Execution Mode  ##################################
    times['steps'] = []
    times['waits'] = []
    wait_time = -1
    h.helicsFederateEnterExecutingMode(fed)

    hours = 24 * 7
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    curtime = start_time
    grantedtime = h.helicsFederateRequestTime(fed, start_time)

    if logg:
        logfile = open(sim_name + '.csv', 'w+')
        header_line = 'helics_simulation_time'
        for i in log_vars:
            header_line += ',' + i
        logfile.write(header_line+'\n')

    ErrorDict=['FMI_OK', 'FMI_WARNING', 'FMI_DISCARD', 'FMI_ERROR','FMI_FATAL','FMI_PENDING']

    first_step = True

    while grantedtime < total_interval:
        requested_time = grantedtime + update_interval
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)

        if wait_time > 0:
            times['waits'].append(time() - wait_time)
        step_time = time()
        step_recording = []


        status = fmu.do_step(current_t=curtime, step_size=grantedtime - curtime, new_step=True)

        step_recording.append(time() - step_time)
        step_time = time()
        if status > 0:
            print('error in do_step function: ' + ErrorDict[status])
        curtime = grantedtime

        if not first_step:
            for i in range(sub_count):
                var_value = h.helicsInputGetDouble((subid[i]))
                for var_name in reverse_mappings[subid[i].target]:
                    try:
                        fmu.set(var_name, var_value)
                    except Exception as e:
                        print(e)
        first_step = False

        step_recording.append(time() - step_time)
        step_time = time()

        for i in range(pub_count):
            var_name = pubid[i].name.split('/')[1]
            try:
                var_value = fmu.get(var_name).item()
                h.helicsPublicationPublishDouble(pubid[i], var_value)
            except Exception as e:
                print(e)

        step_recording.append(time() - step_time)
        times['steps'].append(step_recording)

        if logg:
            logline = str(grantedtime)

            for i in log_vars:
                try:
                    var_value = fmu.get(i).item()
                    logline += ','+ str(var_value)
                except Exception:
                    logline += ',-1'

            logfile.write(logline+'\n')

        wait_time = time()

    
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()

    if logg:
        logfile.close()

    if gettimes:
        with open(sim_name + '_times' + str(json_config['period']) + '.json', 'w+') as timefile:
            json.dump(times, timefile)

    if command is not None:
        command.kill()