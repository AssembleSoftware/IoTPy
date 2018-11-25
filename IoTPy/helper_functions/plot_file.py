import matplotlib.pyplot as plt
import sys

def plot_file(filename):
    with open(filename, 'r') as the_file:
            data = [float(v) for v in the_file.read().split()]
    plt.figure(1)
    plt.plot(data)
    lines = plt.plot(data)
    plt.setp(lines, linewidth=3, color='r')
    plt.axis([0, len(data), -1, 2])
    plt.show()

if __name__ == '__main__':
    args = sys.argv
    plot_file(
        filename=args[1]
        )
