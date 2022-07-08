import matplotlib.pyplot as plt
from statistics import mean
import seaborn as sns

sns.set_theme()

with open('experiment.log') as file:
    raw_data = file.read().split('\n')

times = []
means = []
readings = []
for raw_line in raw_data:
    if len(raw_line) == 0:
        continue
    raw_line = raw_line.split(',')
    times.append(int(raw_line[0]))
    rds = [float(elem) for elem in raw_line[1:]]
    means.append(mean(rds))
    readings.append(rds)

fig, ax = plt.subplots()
ax.plot(times[:-1], means[:-1])
ax.scatter(times[:-1], means[:-1])
ax.set_xlabel('period')
ax.set_ylabel('sim time')
fig.savefig('results.png')
plt.close(fig)
