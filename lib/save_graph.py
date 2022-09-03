import matplotlib.pyplot as plt
from statistics import mean
import seaborn as sns

sns.set_theme()

with open('experiment.log') as file:
    raw_data = file.read().split('\n')

pairs = []
means = []
readings = []
for raw_line in raw_data:
    if len(raw_line) == 0:
        continue
    raw_line = raw_line.split(',')
    pairs.append(int(raw_line[0]))
    rds = [float(elem) for elem in raw_line[1:]]
    means.append(mean(rds))
    readings.append(rds)

fig, ax = plt.subplots()
ax.plot(pairs, means)
ax.scatter(pairs, means)
ax.set_xlabel('pairs')
ax.set_ylabel('co-simulation time (s)')
ax.set_ylim([0, 450])
fig.savefig('results.png')
plt.close(fig)


diffs = [means[i+1] - means[i] for i in range(len(means)-1)]
fig, ax = plt.subplots()
ax.plot(pairs[1:], diffs)
ax.scatter(pairs[1:], diffs)
ax.set_xlabel('pairs')
ax.set_ylabel('difference (s)')
ax.set_ylim([0,60])
fig.savefig('increases.png')
plt.close(fig)
