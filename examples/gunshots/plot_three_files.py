"""
From the command line enter
        python plot_three_files filename_1 filename_2 filename_3
to plot both files on the same diagram. The first two files are in a single
plot while the third file is in a separate plot.
For example,
python plot_three_files x_file_data.txt y_file_data.txt magnitude_file.txt

"""
import matplotlib.pyplot as plt
import sys

def plot_three_files(filename_1, filename_2, filename_3):
        with open(filename_1, 'r') as the_file:
                data_1 = [float(v) for v in the_file.read().split()]
        with open(filename_2, 'r') as the_file:
                data_2 = [float(v) for v in the_file.read().split()]
        with open(filename_3, 'r') as the_file:
                data_3 = [float(v) for v in the_file.read().split()]
                
        plt.figure(1)
        plt.subplot(211)
        plt.plot(data_1)
        plt.plot(data_2)
        plt.subplot(212)
        plt.plot(data_3)
        plt.show()

if __name__ == '__main__':
    args = sys.argv
    plot_three_files(
        filename_1=args[1],
        filename_2=args[2],
        filename_3=args[3]
        )
