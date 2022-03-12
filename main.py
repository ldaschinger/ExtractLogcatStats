"""
Extracts various values from Keysight Data Logger *.csv file like
average current, average power, cumulative sum of energy used

Possibility to plot the current and energy consumption with matplotlib
"""

__author__ = "Lukas Daschinger"
__version__ = "1.0.1"
__maintainer__ = "Lukas Daschinger"
__email__ = "ldaschinger@student.ethz.ch"


import getopt
import math
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import re


def analyzeWebRTCStats(filepath):
    # print head including sampling interval
    with open(filepath) as myfile:
        head = [next(myfile) for x in range(6)]
    # print(head, "\n")

    #02-15 10:21:28.803  2621  3794 I ExtendedACodec:   int32_t bitrate =
    # group 3 = hour
    # group 4 = minute
    # group 5 = second
    # group 6 = millisecond
    # group 9 = bitrate
    bitrateRegex = re.compile(r'(\d+)-(\d+)\s+(\d+):(\d+):(\d+).(\d+)\s+(\d+)\s+(\d+)\s+I\s+ExtendedACodec:\s+int32_t bitrate\s+=\s+(\d+)') #ExtendedACodec:   int32_t bitrate = 2000000
    timestampRegex = re.compile(r'(\d+)-(\d+)\s+(\d+):(\d+):(\d+).(\d+)')

    # ---1...2...3...4...end
    # difference in ms = match.group(3)*3600000 + match.group(4)*60000 + match.group(5)*1000 + match.group(6)
    timestamps_ms = []
    bitrateValues = []

    # get the last timetamp
    with open(filepath) as f:
        lines = f.readlines()
        last = lines[-1]
        #detect last line and get its timestamp
        for match in re.finditer(timestampRegex, last):
            # print(match.group(3))
            # print(match.group(4))
            # print(match.group(5))
            # print(match.group(6))
            lastTimestamp = (int(match.group(3)) * 3600000) + int(match.group(4)) * 60000 + int(match.group(5)) * 1000 + int(match.group(6))

    for i, line in enumerate(open(filepath)):
        for match in re.finditer(bitrateRegex, line):
            # print('Found on line %s: %s' % (i + 1, match.group(1)))
            # now append it to the availableOutgoingBitrate list
            bitrateValues.append(match.group(9))
            # print(match.group(3))
            # print(match.group(4))
            # print(match.group(5))
            # print(match.group(6))
            timestamp = (int(match.group(3)) * 3600000) + int(match.group(4)) * 60000 + int(match.group(5)) * 1000 + int(match.group(6))
            timestamps_ms.append(timestamp)

    # append last timestamp to list
    timestamps_ms.append(lastTimestamp)

    """
    Average calculation
    durations = [ts2-ts1, ts3-ts2, ts4-ts3, last-ts4]
    bitrates = [1,2,3,4]

    total = durations*bitrates
    average = total/(timestamps[-1]-timestamps[0])
    """

    durations = []
    for x in range(len(timestamps_ms)-1):
        # print(timestamps_ms[0])
        durations.append(timestamps_ms[x+1] - timestamps_ms[x])
        # print(durations[x])

    npArray = np.asarray(bitrateValues)
    npArrayBitrates = npArray.astype(int)
    npArray = np.asarray(durations)
    npArrayDurations = npArray.astype(int)

    # print(npArrayDurations)

    npArrayConstantTimestamps = npArrayDurations[npArrayDurations > 4500]
    # print(npArrayConstantTimestamps)
    npArrayConstantBitrates = npArrayBitrates[npArrayDurations > 4500]
    # print(npArrayConstantBitrates)


    # we do not want bitrates that are present for only a few seconds (the ones until ramp up is completed)
    # we create new arrays with durations and bitrates which were present for over 4s

    # print('average and stddev of bitrate found: ')
    # weightedAverage = np.average(npArrayBitrates[fromSampleN:], weights=npArrayDurations[fromSampleN:])
    weightedAverage = np.average(npArrayBitrates, weights=npArrayDurations)
    # print("\n\n" + filepath)
    # print(weightedAverage)

    # plt.plot(npArrayBitrates)
    # plt.plot(npArrayDurations)
    # plt.show()

    #weighted avg by hand:
    # total = sum(npArrayDurations*npArrayBitrates)
    # average = total/(timestamps_ms[-1]-timestamps_ms[0])

    # calculate stddev weighted
    variance = np.average((npArrayBitrates - weightedAverage) ** 2, weights=npArrayDurations)
    # print(math.sqrt(variance))

    # print(weighted_stddev(bitrateValues, durations))

    # does not work like this since we need to weight bitrates
    # npArray = np.asarray(bitrateValues)
    # npArray = npArray.astype(int)
    # print("\nAVERAGE bitrateValues: " + str(npArray.mean()))
    # print("STDDEV bitrateValues: " + str(npArray.std()))

    return weightedAverage


def analyzeTestCustom(folderpath, bitrate, res1, fps1, codec1, res2="null", fps2="null", codec2="null",
                      res3="null", fps3="null", codec3="null", res4="null", fps4="null", codec4="null",
                      res5="null", fps5="null", codec5="null"):

    settings = []

    dictlist = [dict() for x in range(5)]
    dictlist[0] = {"res": res1, "fps": fps1, "codec": codec1}
    dictlist[1] = {"res": res2, "fps": fps2, "codec": codec2}
    dictlist[2] = {"res": res3, "fps": fps3, "codec": codec3}
    dictlist[3] = {"res": res4, "fps": fps4, "codec": codec4}
    dictlist[4] = {"res": res5, "fps": fps5, "codec": codec5}

    folderpaths = []
    for i in range(5):
        folderpaths.append(folderpath + dictlist[i].get("codec") + "/" + bitrate + "/" + bitrate + dictlist[i].get("res") + dictlist[i].get("fps"))

    bitrateMeans = [[0 for x in range(0)] for y in range(5)]
    for i in range(5):
        # if we have varying number of tests and therefore .csv files available we must find all in the folder
        if dictlist[i].get("res") != "null":
            for item in os.listdir(folderpaths[i]):
                name, extension = os.path.splitext(item)
                # if there is no extension it is a folder
                if extension == "" and item != ".DS_Store":
                    bitrateMeans[i].append(analyzeWebRTCStats(folderpaths[i] + "/" + item + "/" + "logcat.txt"))

    # # if we have varying number of tests and therefore .csv files available we must find all in the folder
    # for filename in os.listdir(folderpath1):
    #     name, extension = os.path.splitext(filename)
    #     if extension == ".csv":
    #         mean1.append(analyzeLoggerData(folderpath1 + "/" + filename))
    # npMean1 = np.asarray(mean1)

    npMeans = [np.empty([5]) for x in range(5)]
    for i in range(5):
        # if we have varying number of tests and therefore .csv files available we must find all in the folder
        if dictlist[i].get("res") != "null":
            npMeans[i] = np.asarray(bitrateMeans[i])


    for i in range(5):
        # if we have varying number of tests and therefore .csv files available we must find all in the folder
        if dictlist[i].get("res") != "null":
            print(str(format(npMeans[i].mean(), ".2f")) + " " + str(format(npMeans[i].std(), ".2f")) + " " + str(format(npMeans[i].std(), ".2f")) + "  ", end="", flush=True)

    print("\n")
    # print(str(format(npMean1.mean(), ".2f")) + " " + str(format(npMean1.std(), ".2f")) + " " + str(format(npMean1.std(), ".2f")) + "  " +
    #       str(format(npMean2.mean(), ".2f")) + " " + str(format(npMean2.std(), ".2f")) + " " + str(format(npMean2.std(), ".2f")) + "  " +
    #       str(format(npMean3.mean(), ".2f")) + " " + str(format(npMean3.std(), ".2f")) + " " + str(format(npMean3.std(), ".2f")) + "  " +
    #       str(format(npMean4.mean(), ".2f")) + " " + str(format(npMean4.std(), ".2f")) + " " + str(format(npMean4.std(), ".2f")) + "  " +
    #       str(format(npMean5.mean(), ".2f")) + " " + str(format(npMean5.std(), ".2f")) + " " + str(format(npMean5.std(), ".2f")))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folderpath",
                        required=True,
                        default=None,
                        help="Path to target CSV file folder")

    args = parser.parse_args()

    """
    directory structure:
    folderpath
        folderpath_small/large/auto
            dlog1.csv/dlog2.csv/dlog3.csv/dlog4.csv
    """

    # # 30fps tests
    # analyzeTestCustom(args.folderpath, bitrate="300", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="600", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="900", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="1300", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="1800", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="2700", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="4000", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="4750", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="6000", res1="_small_", fps1="30", codec1="H264",
    #                   res2="_large_", fps2="30", codec2="H264", res3="_auto_", fps3="30", codec3="H264")

    # 15fps tests
    # analyzeTestCustom(args.folderpath, bitrate="600", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="900", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="1300", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="1800", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="2700", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="4000", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")
    # analyzeTestCustom(args.folderpath, bitrate="6000", res1="_small_", fps1="15", codec1="H264",
    #                   res2="_large_", fps2="15", codec2="H264", res3="_auto_", fps3="30", codec3="H264")


    # # VP8 tests
    # analyzeTestCustom(args.folderpath, bitrate="900",
    #                   res1="_small_", fps1="30", codec1="VP8",
    #                   res2="_large_", fps2="30", codec2="VP8",
    #                   res3="_auto_", fps3="30", codec3="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="1800",
    #                   res1="_small_", fps1="30", codec1="VP8",
    #                   res2="_large_", fps2="30", codec2="VP8",
    #                   res3="_auto_", fps3="30", codec3="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="4000",
    #                   res1="_small_", fps1="30", codec1="VP8",
    #                   res2="_large_", fps2="30", codec2="VP8",
    #                   res3="_auto_", fps3="30", codec3="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="6000",
    #                   res1="_small_", fps1="30", codec1="VP8",
    #                   res2="_large_", fps2="30", codec2="VP8",
    #                   res3="_auto_", fps3="30", codec3="VP8")

    # # VP8 vs H264 tests
    # analyzeTestCustom(args.folderpath, bitrate="900",
    #                   res1="_small_", fps1="30", codec1="H264",
    #                   res2="_small_", fps2="30", codec2="VP8",
    #                   res3="_large_", fps3="30", codec3="H264",
    #                   res4="_large_", fps4="30", codec4="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="1800",
    #                   res1="_small_", fps1="30", codec1="H264",
    #                   res2="_small_", fps2="30", codec2="VP8",
    #                   res3="_large_", fps3="30", codec3="H264",
    #                   res4="_large_", fps4="30", codec4="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="4000",
    #                   res1="_small_", fps1="30", codec1="H264",
    #                   res2="_small_", fps2="30", codec2="VP8",
    #                   res3="_large_", fps3="30", codec3="H264",
    #                   res4="_large_", fps4="30", codec4="VP8")
    # analyzeTestCustom(args.folderpath, bitrate="6000",
    #                   res1="_small_", fps1="30", codec1="H264",
    #                   res2="_small_", fps2="30", codec2="VP8",
    #                   res3="_large_", fps3="30", codec3="H264",
    #                   res4="_large_", fps4="30", codec4="VP8")

    # 15fps vs 30fps H264
    analyzeTestCustom(args.folderpath, bitrate="600", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="900", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="1300", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="1800", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="2700", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="4000", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")
    analyzeTestCustom(args.folderpath, bitrate="6000", res1="_small_", fps1="15", codec1="H264",
                      res2="_small_", fps2="30", codec2="H264", res3="_large_", fps3="15", codec3="H264",
                      res4="_large_", fps4="30", codec4="H264")