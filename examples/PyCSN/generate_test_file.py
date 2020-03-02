import random

N_DATA = 10000 # 4 seconds worth of data


def generate_timestamp_file():
    with open('./timestamp.txt', 'w') as fpout:
        for i in range(N_DATA):
            fpout.write('{}\n'.format(0.004*i))


def generate_acc_file(acc_idx):
    with open('./acc_{}.txt'.format(acc_idx), 'w') as fpout:
        for i in range(N_DATA):
            fpout.write('{}\n'.format(random.uniform(-1, 1)))


if __name__ == '__main__':
    generate_timestamp_file()
    generate_acc_file('n')
    generate_acc_file('e')
    generate_acc_file('z')
