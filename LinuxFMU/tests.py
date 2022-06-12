from jinja2 import Template
import time
import subprocess

ITER = 5

periods = [5, 10, 15, 30, 60, 120, 300, 600, 3600]

with open('ApartmentNoPV_template.json') as file:
    ap_template = Template(file.read())

with open('PolimiPV_template.json') as file:
    pv_template = Template(file.read())

logfile = open('experiment.log', 'w+')

for p in periods:
    print(f'---------- Experimenting with period {p} ----------')
    diffs = []
    for i in range(ITER):
        print(f'experiment {i}: ', end='', flush=True)
        render_data = {'period': p}
        with open('ApartmentNoPV.json', 'w+') as file:
            file.write(ap_template.render(render_data))

        with open('PolimiPV.json', 'w+') as file:
            file.write(pv_template.render(render_data))

        initial_time = time.time()
        subprocess.run(['helics', 'run', '--path=no_pv_polimi_pv.json'], stdout=subprocess.DEVNULL)
        final_time = time.time()

        diff = final_time - initial_time
        diffs.append(diff)

        print(diff)
    
    logstring = str(p)
    for diff in diffs:
        logstring += ',' + str(diff)
    logfile.write(logstring)
    logfile.write('\n')

logfile.close()
    
