"""
Created on Mon May 13 17:33:09 2019

@author: nleder
"""

import argparse
import sys

from collections.abc import Collection
from ctypes import CDLL, c_double, c_size_t, POINTER
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # Load the Pandas libraries with alias 'pd'


def get_arguments():
    """
    Returns the given Function Parameters off the script-call

    @return Returns the parameters
    """
    parser = argparse.ArgumentParser(
        description='This script is used to plot an existing ICOc log-data.' +
        ' For standard the file log.hdf5 in the file order is used.')
    parser.add_argument('-i',
                        '--input',
                        metavar='Inputfile',
                        help='Chose another input file')
    args = parser.parse_args()

    if args.input is not None:
        filename = args.input
        print('INPUTFILE CHANGED')
    else:
        filename = 'log.hdf5'
    return filename


class IFTLibrary:

    library = CDLL((Path(__file__).parent / "ift.dll").as_posix())
    ift_value_function = library.ift_value
    ift_value_function.argtypes = [
        POINTER(c_double),  # double samples[]
        c_size_t,  # size_t sample_size
        c_double,  # double window_length
        c_double,  # double sampling_frequency
        c_double,  # A2
        c_double,  # A3
        c_double,  # A4
        c_double,  # A5
        POINTER(c_double),  # double output[]
    ]

    @classmethod
    def ift_value(
        cls,
        samples: Collection[float],
        sampling_frequency: float,
        window_length: float,
    ) -> list[float]:
        len_samples = len(samples)
        samples_arg = (c_double * len_samples)(*samples)
        output = (c_double * len_samples)()

        status = cls.ift_value_function(samples_arg, len_samples,
                                        window_length, sampling_frequency, 0,
                                        0, 0, 0, output)

        print(f"Return value: {status}")

        return list(output)


def main():
    """
    Main function of the ICOplotter
    """
    log_file = get_arguments()
    data = pd.read_hdf(log_file, key="acceleration")
    timestamps = data["timestamp"]
    n_points = len(timestamps)

    f_sample = n_points / \
        (timestamps.iloc[n_points-1]-timestamps.iloc[0])*1000000
    stats = data.describe()

    axes = [axis for axis in ('x', 'y', 'z') if data.get(axis) is not None]
    nr_of_axis = len(axes)

    if nr_of_axis <= 0:
        print("Error: No axis data available", file=sys.stderr)
        sys.exit(1)

    print(" ".join([
        f"Avg {axis.upper()}: {int(stats.loc['mean', [axis]])}"
        for axis in axes
    ]))

    std_dev = stats.loc['std', axes]
    snr = 20 * np.log10(std_dev / (np.power(2, 16) - 1))
    print(f"SNR of this file is : {min(snr):.2f} dB and {max(snr):.2f} dB "
          f"@ {f_sample / 1000:.2f} kHz")

    plt.subplots(2, 1, figsize=(20, 10))
    plt.subplot(211)
    for axis in axes:
        plt.plot(timestamps, data[axis], label=axis)
    plt.legend()

    plt.subplot(212)
    for axis in axes:
        plt.psd(data[axis] - data[axis].mean(), 512, f_sample, label=axis)
    plt.legend()

    plt.show()


if __name__ == "__main__":
    values = IFTLibrary.ift_value(samples=range(1000),
                                  sampling_frequency=1000,
                                  window_length=0.005)
    print(f"Values: {values}")
    # main()
