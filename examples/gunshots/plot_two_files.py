"""
From the command line enter
        python plot_two_files filename_1 filename_2
to plot both files on the same diagram.
For example,
        python plot_two_files x_file_data.txt y_file_data.txt

"""
import matplotlib.pyplot as plt
import sys

def plot_two_files(filename_1, filename_2):
        with open(filename_1, 'r') as the_file:
                data_1 = [float(v) for v in the_file.read().split()]
        with open(filename_2, 'r') as the_file:
                data_2 = [float(v) for v in the_file.read().split()]
        plt.figure(1)
        plt.subplot(211)
        plt.plot(data_1)
        plt.subplot(212)
        plt.plot(data_2)
        plt.show()

if __name__ == '__main__':
    args = sys.argv
    plot_two_files(
        filename_1=args[1],
        filename_2=args[2]
        )
