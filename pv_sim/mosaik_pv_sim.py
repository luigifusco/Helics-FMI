import mosaik_api
import pv_sim

META = {
    'models': {
        'PVsimulator': {
            'public': True,
            'params': ['P_sytem','slope','aspect','latitude','longitude','elevation',
				'Tc_noct','T_ex_noct','a_p','ta','P_mpdule',
				'G_noct','G_stc','Area','Tc_stc','ghi', 'T_ext', 'start_date'],
            'attrs': ['power_dc'],
        },
    },
}


class PVSIM(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.simulator = pv_sim.PVsimulator()
        self.eid_prefix = 'PyModel_'
        self.entities = {}  # Maps EIDs to model indices in self.simulator

    def init(self, sid, eid_prefix=None,start_date=None):
    	self.start_date=pd.to_datetime(start_date)
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model, P_sytem=1000 ,slope=0,aspect=0,latitude=0,longitude=0,elevation=0,
				Tc_noct=45,T_ex_noct=20,a_p=0.0038,ta=0.9,P_module=283,
				G_noct=800,G_stc=1000,Area=1.725,Tc_stc=25.0):
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.simulator.add_PV(P_sytem=1000 ,slope=0,aspect=0,latitude=0,longitude=0,elevation=0,
				Tc_noct=45,T_ex_noct=20,a_p=0.0038,ta=0.9,P_module=283,
				G_noct=800,G_stc=1000,Area=1.725,Tc_stc=25.0)
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities



    def step(self, time, inputs):
        # TODO finire comando step
        sim_time=self.start_date + pd.Timedelta(time,unit='s')
        # Perform simulation step
        self.simulator.step(ghi,T_ext,sim_time)

        return time + 900  # Step size is 1 minute

    def get_data(self, outputs):
        models = self.simulator.models
        data = {}
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['PVsimulator']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)

                # Get model.val or model.delta:
                data[eid][attr] = getattr(models[model_idx], attr)

        return data


def main():
    return mosaik_api.start_simulation(ExampleSim())


if __name__ == '__main__':
    main()