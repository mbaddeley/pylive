import matplotlib.pyplot as plt
import numpy as np
# use ggplot style for more sophisticated visuals
plt.style.use('fivethirtyeight')

# ----------------------------------------------------------------------------#
def start():
    plt.ion()  # this is the call to matplotlib that allows dynamic plotting
    plt.show()


# ----------------------------------------------------------------------------#
def tick():
    # this pauses the data so the figure/axis can catch up
    plt.pause(0.1)


# ----------------------------------------------------------------------------#
def tock(period=1):
    # this pauses the data so the figure/axis can catch up
    #
    for pyl in PyLive._registry:
        for label in pyl.labels:
            pyl.update_series(label)
    plt.pause(0.1)


# ----------------------------------------------------------------------------#
class PyLive:
    """PyLive class."""

    _registry = []

    def __init__(self, re, parser_fnc, _str,
                 title='MyTitle', xlabel='MyXLabel', ylabel='MyYLabel', **kwargs):

        self.size = kwargs['size'] if 'size' in kwargs else 100

        self.re = re
        self.parser = parser_fnc

        self.last_data_str = ''
        self._str = _str

        self.labels = []
        self.x_vec = np.linspace(0, 1, self.size+1)[0:-1]
        self.y_vecs = {}
        self.fig = plt.figure(figsize=(13, 6))
        self.ax = self.fig.add_subplot(111)
        self.lines = {}

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)

        # Remove xticks
        # self.ax.tick_params(
        #     axis='x',           # changes apply to the x-axis
        #     which='both',       # both major and minor ticks are affected
        #     bottom=False,       # ticks along the bottom edge are off
        #     top=False,          # ticks along the top edge are off
        #     labelbottom=False)  # labels along the bottom edge are off

        self._registry.append(self)

# ----------------------------------------------------------------------------#
    def __str__(self):
        return self._str.format(self.last_data_str)

# ----------------------------------------------------------------------------#
    def add_series(self, label):
        self.labels.append(label)
        arr = np.arange(self.size, dtype=int)
        y_vec = np.full_like(arr, 0)
        self.y_vecs.update({label: y_vec})
        line, = self.ax.plot(self.x_vec, y_vec, '-o', alpha=0.8, label=label)
        self.lines.update({label: line})

# ----------------------------------------------------------------------------#
    def update(self, label, line):
        if line != '' and line is not None:
            data = self.parser(self.re, line)
            if data is not None:
                self.last_data_str = str(data)  # save for printing
                # get ys for line
                y_vec = self.y_vecs[label]
                y_vec = np.append(y_vec[1:], 0.0)
                y_vec[-1] = data
                # print(y_vec)
                self.y_vecs[label] = y_vec

                line = self.lines[label]
                line.set_ydata(y_vec)
                # adjust limits if new data goes beyond bounds
                if np.min(y_vec) <= line.axes.get_ylim()[0] or np.max(y_vec) >= line.axes.get_ylim()[1]:
                    self.ax.set_ylim([np.min(y_vec)-np.std(y_vec), np.max(y_vec) + np.std(y_vec)])
                return True
        return False
