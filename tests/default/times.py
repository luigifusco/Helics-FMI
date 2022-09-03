from jinja2 import Template
import time
import subprocess

ITER = 3

periods = [1, 5, 15, 30, 60, 150, 300]

with open('ApartmentNoPV_template.json') as file:
    ap_template = Template(file.read())

with open('PolimiPV_template.json') as file:
    pv_template = Template(file.read())

logfile = open('experiment.log', 'w+')

for r in periods:
    print(f'---------- Experimenting with period {r} ----------')
    diffs = []
    render_data = {'period': r}
    with open(f'ApartmentNoPV.json', 'w+') as file:
        file.write(ap_template.render(render_data))

    with open(f'PolimiPV.json', 'w+') as file:
        file.write(pv_template.render(render_data))

    for i in range(ITER):
        print(f'experiment {i}: ', end='', flush=True)

        initial_time = time.time()
        subprocess.run(['helics', 'run', '--path=no_pv_polimi_pv.json'], stdout=subprocess.DEVNULL)
        final_time = time.time()

        diff = final_time - initial_time
        diffs.append(diff)

        print(diff)
    
    logstring = str(r)
    for diff in diffs:
        logstring += ',' + str(diff)
    logfile.write(logstring)
    logfile.write('\n')

logfile.close()
    
