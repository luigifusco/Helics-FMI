from jinja2 import Template
import time
import subprocess

ITER = 3

replicas = [1, 2, 3, 4, 5, 6, 7, 8]

with open('Apartment_template.json') as file:
    ap_template = Template(file.read())

with open('PV_template.json') as file:
    pv_template = Template(file.read())

with open('scalability_template.json') as file:
    s_template = Template(file.read())

logfile = open('experiment.log', 'w+')

for r in replicas:
    print(f'---------- Experimenting with {r} replicas ----------')
    diffs = []
    render_data = {'federates': r*2+1, 'replicas': r}
    with open('scalability.json', 'w+') as file:
            file.write(s_template.render(render_data))
    for replica_index in range(r):
        render_data = {'replica': replica_index}
        with open(f'Apartment{replica_index}.json', 'w+') as file:
            file.write(ap_template.render(render_data))

        with open(f'PV{replica_index}.json', 'w+') as file:
            file.write(pv_template.render(render_data))

    for i in range(ITER):
        print(f'experiment {i}: ', end='', flush=True)

        initial_time = time.time()
        subprocess.run(['helics', 'run', '--path=scalability.json'], stdout=subprocess.DEVNULL)
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
    
