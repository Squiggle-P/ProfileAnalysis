""" Boilerplate Info
ProfileSimulator.PY - Using existing profile data (CSV) and existing MD/CD configuration data (config.txt), simulate
changes through the profile. This won't be perfect, but it should estimate large-scale changes (like addition of a
steambox) for rough estimates.

Created 09/01/17/PP - [R0]:


Edited  MM/DD/YY/NN - [R1]:

"""
from __future__ import print_function

from PSConfig import *
import ProfileReader as PR
import AveragesAndReels as AAR
import csv
import numpy
from random import randint

if __name__ == "__main__":

    CPGainDict = {"RL.BSWT (7)": CPBWGain,
                  "RL.MST (10)": CPMoiGain,
                  "RL.CNDWT (13)": CPCWGain,
                  "CTRL.HBDILFB (97)": 1}

    SBGainDict = {"RL.BSWT (7)": 0,
                  "RL.MST (10)": SBMoiGain,
                  "RL.CNDWT (13)": 0,
                  "CTRL.HBDILFB (97)": 0}

    ComparisonDictionary = {}

    if RebuildTables == True:

        # Get Reels
        DatasetDictionary = PR.CSV2Arrays(RawDataFile, True)

        # Remove bad reels. Limits defined in PSConfig.py - user to edit if necessary - preconfigured limits very lax.
        DatasetDictionary = PR.ScrubStandardDictionary(DatasetDictionary,
                                                       LowMoiLimit=MoiBinLimits[0], HighMoiLimit=MoiBinLimits[1],
                                                       LowWtLimit=BWBinLimits[0], HighWtLimit=BWBinLimits[1],
                                                       LowScanLimit=ScanCountLimits[0],
                                                       HighScanLimit=ScanCountLimits[1],
                                                       GradeList=GoodGradeList)

        # Remove extraneous MVDC data - just raw, good bin data: Array of float64s, length irrelevant
        DatasetDictionary = PR.JustTheData(DatasetDictionary)

        if OutputCSVs:
            print("Writing scrubbed high-res data to %s..." % StoreScrubbedHighResOriginal)
            with open(StoreScrubbedHighResOriginal, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

        # Write Some Data
        if OutputCSVs:

            ReelAveragesDict = {}
            CPAverages = {}
            SBAverages = {}
            print("Outputting chunked Roll Averages to %s..." % StoreRealRollAverages)
            with open(StoreRealRollAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    ReelAveragesDict[k] = AAR.RollAverages(v, RollsPerReel)
                    writeobject.writerow([k])
                    for reel in ReelAveragesDict[k]:
                        writeobject.writerow(reel)

            print("Outputting chunked CP Averages to %s..." % StoreRealCPAverages)
            with open(StoreRealCPAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    CPAverages[k] = AAR.RollAverages(v, CPActNum)
                    writeobject.writerow([k])
                    for actuatorbin in CPAverages[k]:
                        writeobject.writerow(actuatorbin)

            print("Outputting chunked SB Averages to %s" % StoreRealSBAverages)
            with open(StoreRealSBAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    SBAverages[k] = AAR.RollAverages(v, SBActNum)
                    writeobject.writerow([k])
                    for actuatorbin in SBAverages[k]:
                        writeobject.writerow(actuatorbin)

        # Normalize CWT using CDActuators
        All_Act_Changes = []
        # Iterate through reels CWT profiles, making adjustments to actuators. We can ignore actuator limits here (right?)
        print("Adjusting CP actuators for true moisture profile...")
        for reel in DatasetDictionary["RL.CNDWT (13)"]:
            ReelAvg = numpy.mean(reel)
            ChunkAverageReel = AAR.AverageReel(reel, CPActNum)
            ActChange = []
            for chunk in ChunkAverageReel:
                ActChange.append((ReelAvg - chunk) * (1 / CPCWGain))
                # print "Avg = %s" % ReelAvg
                # print "Profile = %s" % (chunk)
                # print "Move Actuator by: %s" % ActChange[len(ActChange)-1]
            All_Act_Changes.append(ActChange)

        TemporaryDatasetDictionary = {}
        AdjustedReels = []

        # Apply adjustments to all profiles
        print("Applying CP actuator adjustments across all relevant profiles...")
        for k, v in DatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in range(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], CPGainDict[k]))
            TemporaryDatasetDictionary[k] = AdjustedReels

        if OutputCSVs:
            print("Outputting new (intermediate) profiles to %s" % PostCPWeightDataFile)
            with open(PostCPWeightDataFile, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in TemporaryDatasetDictionary.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

        # Iterate through reels MOI profiles - making adjustments to SB actuators.
        InitialSBProfile = [StartingSBPos] * SBActNum  # Use this to get the most profiling
        All_Act_Changes = []
        SteamboxDataset = []
        print("Adjusting SB to correct extreme moisture profile...")
        for reel in TemporaryDatasetDictionary["RL.MST (10)"]:
            ReelAvg = numpy.mean(reel)
            ChunkAverageReel = AAR.AverageReel(reel, SBActNum)
            ActChange = []
            for chunk in ChunkAverageReel:
                ActChange.append((ReelAvg - chunk) * (1 / SBMoiGain))

            # Make sure nothing is outside of physical limits
            for i in range(len(ActChange)):
                if ActChange[i] > 100 - StartingSBPos:
                    ActChange[i] = 100 - StartingSBPos
                elif ActChange[i] < 0 - StartingSBPos:
                    ActChange[i] = 0 - StartingSBPos

            SteamboxDataset.append([x + 50 for x in ActChange])
            All_Act_Changes.append(ActChange)

        # Apply adjustments to everything
        PostSBDict = {}
        print("Applying SB actuator changes to moisture profiles...")
        for k, v in TemporaryDatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in range(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], SBGainDict[k]))
            PostSBDict[k] = AdjustedReels
        PostSBDict["CTRL.STMBX (??)"] = SteamboxDataset
        CPGainDict["CTRL.STMBX (??)"] = 0
        SBGainDict["CTRL.STMBX (??)"] = 1

        if OutputCSVs:
            print("Outputting new profiles to %s..." % PostSBAdjustmentDataFile)
            with open(PostSBAdjustmentDataFile, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in PostSBDict.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

        # Return profile to CP-Moisture Controlled

        All_Act_Changes = []

        print("Adjusting CP actuators to account for latest profiles...")
        for reel in TemporaryDatasetDictionary["RL.MST (10)"]:
            ReelAvg = numpy.mean(reel)
            ChunkAverageReel = AAR.AverageReel(reel, CPActNum)
            ActChange = []
            for chunk in ChunkAverageReel:
                ActChange.append((ReelAvg - chunk) * (1 / CPMoiGain))
                # print "Avg = %s" % ReelAvg
                # print "Profile = %s" % (chunk)
                # print "Move Actuator by: %s" % ActChange[len(ActChange)-1]
            All_Act_Changes.append(ActChange)

        FinalReelDict = {}
        AdjustedReels = []
        if LowerMemoryUsage:
            DatasetDictionary.clear()

        # Apply adjustments to all profiles
        print("Applying CP changes to all profiles...")
        for k, v in TemporaryDatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in range(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], CPGainDict[k]))
            FinalReelDict[k] = AdjustedReels

        if LowerMemoryUsage:
            TemporaryDatasetDictionary.clear()

        print("Calculating Final Roll Averages...")
        ReelAveragesDict = {}
        for k, v in FinalReelDict.iteritems():
            ReelAveragesDict[k] = AAR.RollAverages(v, RollsPerReel)
        HeaderList = []

        for k, v in ReelAveragesDict.iteritems():
            HeaderList.append(k)
            TempList = []

            for reel in v:
                for roll in reel:
                    TempList.append(roll)
            ReelAveragesDict[k] = TempList
        HeaderList.append("pos")
        RollPositionList = ["A", "B", "Z"] * len(ReelAveragesDict[HeaderList[0]])
        ReelAveragesDict["pos"] = RollPositionList

        print("Outputting final CSV of Roll Averages to %s..." % StoreNewRollAverages)
        TempList = []
        with open(StoreNewRollAverages, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            writeobject.writerow(HeaderList)
            for i in range(len(ReelAveragesDict[HeaderList[0]])):
                TempList = []
                for j in HeaderList:
                    TempList.append(ReelAveragesDict[j][i])
                writeobject.writerow(TempList)

                # for k, v in FinalReelDict.iteritems():
                #     ReelAveragesDict[k] = AAR.RollAverages(v, RollsPerReel)
                #     writeobject.writerow([k])
                #     for reel in ReelAveragesDict[k]:
                #         writeobject.writerow(reel)

        if OutputCSVs:
            CPAverages = {}
            SBAverages = {}

            print("Outputting New High-Res Profiles to %s..." % StoreAdjustedRawData)
            with open(StoreAdjustedRawData, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in FinalReelDict.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

            print("Outputting New CP Profiles to %s..." % StoreAdjustedCPAverages)
            with open(StoreAdjustedCPAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in FinalReelDict.iteritems():
                    CPAverages[k] = AAR.RollAverages(v, CPActNum)
                    writeobject.writerow([k])
                    for actuatorbin in CPAverages[k]:
                        writeobject.writerow(actuatorbin)

            print("Outputting New SB Profiles to %s..." % StoreAdjustedSBAverages)
            with open(StoreAdjustedSBAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in FinalReelDict.iteritems():
                    SBAverages[k] = AAR.RollAverages(v, SBActNum)
                    writeobject.writerow([k])
                    for actuatorbin in SBAverages[k]:
                        writeobject.writerow(actuatorbin)

    if OutputRandomReelComparisons:
        # Count total reels, choose some number of random ones to pull data from.
        TempList = []
        ComparisonDictionary = {}
        HeaderList = []
        HeaderIndexList = []

        print("Reading High Res Original Profiles %s..." % StoreScrubbedHighResOriginal)
        with open(StoreScrubbedHighResOriginal, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for reel_index in range(len(TempList)):
            if len(TempList[reel_index]) == 1:
                HeaderIndexList.append(reel_index)
        # print HeaderIndexList

        TotalNumReels = int((len(TempList) / len(HeaderIndexList)) - len(HeaderIndexList))
        RandReelArray = []
        for x in range(RandomReelNum):
            RandReelArray.append(randint(0, TotalNumReels))

        print("Selected random reels %s" % RandReelArray)
        print("Generating profiles for each reel...")

        print("Getting Original High Res Profiles")
        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index+1])
            DictName = "Scrubbed Original High Res " + TempList[line_index][0]  # + " " + str(rand_index +1)
            ComparisonDictionary[DictName] = TempArray #TempList[line_index + rand_index +1]

        ComparisonDictionary["Scrubbed Original High Res CTRL.STBX (??)"] = [[StartingSBPos] * SBActNum] * RandomReelNum

        # Clear Memory JIC
        TempList = []

        # Record CP-Normalization profiles

        print("Getting CWT-Normalized High Res...")
        with open(PostCPWeightDataFile, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index+1])
            DictName = "CWT-Normalized High Res " + TempList[line_index][0]# + " " + str(rand_index+1)
            ComparisonDictionary[DictName] = TempArray

        ComparisonDictionary["CWT-Normalized High Res CTRL.STMBX (??)"] = [[StartingSBPos] * SBActNum] * RandomReelNum

        HeaderIndexList.append(len(TempList))
        TempList = []
        HeaderList.append("CTRL.STMBX (??)")

        # Record SB-Affected Profiles (before CP readjustment)

        print("Getting Post-SB Adjustment High Res...")

        with open(PostSBAdjustmentDataFile, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)
                try:
                    line[1]
                except IndexError:
                    print(line[0])
                else:
                    pass
                    # print line[0]

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index+1])
            DictName = "SB-Effected High Res " + TempList[line_index][0] #+ " " + str(rand_index+1)
            ComparisonDictionary[DictName] = TempArray

        # Record SB-Affected Profiles (after CP readjustment)

        TempList = []

        print("Getting Final High Res Profiles...")
        with open(StoreAdjustedRawData, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)
            TempList = TempList + [["0"] * 10] * 5000
        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index+1])
            DictName = "Final High Res " + TempList[line_index][0] #+ " " + str(rand_index+1)
            ComparisonDictionary[DictName] = TempArray

        print("Writing high-res profiles to %s..." % ComparisonReels)

        with open(ComparisonReels, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in ComparisonDictionary.iteritems():
                for reel in range(len(RandReelArray)):
                    # temp = [k] + v[reel]
                    # temp1 = [k + " " + str(RandReelArray[reel])]
                    # temp2 = v[reel]
                    # print temp1
                    temp = [k + " " + str(RandReelArray[reel])] + v[reel]
                    writeobject.writerow(temp)
                # temp = [k] + v
                # writeobject.writerow([k] + v)


    print("Hello World")
