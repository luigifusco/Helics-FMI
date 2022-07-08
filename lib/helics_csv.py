import helics as h
import sys
import arrow

DATE_FORMAT = 'YYYY-MM-DD HH:mm:ss'

def read_next_row(datafile):
    try:
        next_row = next(datafile).strip().split(',')
        next_row[0] = arrow.get(next_row[0], DATE_FORMAT)
    except StopIteration:
        next_row = None

    return next_row


if __name__ == '__main__':
    time_resolution = 1.
    eids = []
    datafile = open(sys.argv[2])
    start_date = arrow.get(sys.argv[3], DATE_FORMAT)
    next_date = start_date
    modelname = next(datafile).strip()
    attrs = next(datafile).strip().split(',')[1:]
    for i, attr in enumerate(attrs):
        try:
            # Try stripping comments
            attr = attr[:attr.index('#')]
        except ValueError:
            pass
        attrs[i] = attr.strip()


    next_row = read_next_row(datafile)
    if start_date < next_row[0]:
        raise ValueError('Start date "%s" not in CSV file.' %
                            start_date.format(DATE_FORMAT))
    while start_date > next_row[0]:
        next_row = read_next_row(datafile)
        if next_row is None:
            raise ValueError('Start date "%s" not in CSV file.' %
                                start_date.format(DATE_FORMAT))

    #######  FEDERATE CREATION  #########
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, 'zmq')
    h.helicsFederateInfoSetCoreInitString(fedinfo, ' --federates=1')
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 7)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 15*60)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    fed = h.helicsCreateCombinationFederate(sys.argv[1], fedinfo)
    ################

    ######### PUBS ########
    pubid = {}
    for i in range(len(attrs)):
        pub_name = f"{sys.argv[1]}/{attrs[i]}"
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
            fed, pub_name, "double", "X"
        )
    ################

    pub_count = h.helicsFederateGetPublicationCount(fed)

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)

    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    next_row = read_next_row(datafile)

    while next_row is not None:

        requested_time = grantedtime + update_interval
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)

        data = next_row
        if data is None:
            raise IndexError('End of CSV file reached.')

        # Chacke date
        date = data[0]
        expected_date = start_date.shift(seconds=grantedtime)

        if date != expected_date:
            raise IndexError('Wrong date "%s", expected "%s"' % (
                date.format(DATE_FORMAT),
                expected_date.format(DATE_FORMAT)))

        # Put data into the cache for get_data() calls
        cache = {}
        for attr, val in zip(attrs, data[1:]):
            cache[attr] = float(val)

        for i in range(pub_count):
            var_name = pubid[i].name.split('/')[1]
            var_value = cache[var_name]
            h.helicsPublicationPublishDouble(pubid[i], var_value)

        next_row = read_next_row(datafile)


    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    datafile.close()
