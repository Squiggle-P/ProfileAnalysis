""" Boilerplate Info
ProfileSimulator.PY - Using existing profile data (CSV) and existing MD/CD configuration data (config.txt), simulate
changes through the profile. This won't be perfect, but it should estimate large-scale changes (like addition of a
steambox) for rough estimates.

Created 09/01/17/PP - [R0]:


Edited  MM/DD/YY/NN - [R1]:

"""

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
            print "Output scrubbed high-res data to %s." % StoreScrubbedHighResOriginal
            with open(StoreScrubbedHighResOriginal, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

        # Write Some Data
        if OutputCSVs:
            print "Outputting CSVs %s %s and %s." % (StoreRealRollAverages, StoreRealCPAverages, StoreRealSBAverages)

            ReelAveragesDict = {}
            CPAverages = {}
            SBAverages = {}

            with open(StoreRealRollAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    ReelAveragesDict[k] = AAR.RollAverages(v, RollsPerReel)
                    writeobject.writerow([k])
                    for reel in ReelAveragesDict[k]:
                        writeobject.writerow(reel)

            with open(StoreRealCPAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in DatasetDictionary.iteritems():
                    CPAverages[k] = AAR.RollAverages(v, CPActNum)
                    writeobject.writerow([k])
                    for actuatorbin in CPAverages[k]:
                        writeobject.writerow(actuatorbin)

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
        print "Adjusting Actuators for true moisture profile."
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
        print "Applying adjustments across all relevant profiles."
        for k, v in DatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in xrange(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], CPGainDict[k]))
            TemporaryDatasetDictionary[k] = AdjustedReels

        if OutputCSVs:
            print "Outputting results to new csv file: %s" % PostCPWeightDataFile
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
        print "Adjusting SB to correct moisture profile."
        for reel in TemporaryDatasetDictionary["RL.MST (10)"]:
            ReelAvg = numpy.mean(reel)
            ChunkAverageReel = AAR.AverageReel(reel, SBActNum)
            ActChange = []
            for chunk in ChunkAverageReel:
                ActChange.append((ReelAvg - chunk) * (1 / SBMoiGain))

            # Make sure nothing is outside of physical limits
            for i in xrange(len(ActChange)):
                if ActChange[i] > 100 - StartingSBPos:
                    ActChange[i] = 100 - StartingSBPos
                elif ActChange[i] < 0 - StartingSBPos:
                    ActChange[i] = 0 - StartingSBPos

            SteamboxDataset.append([x + 50 for x in ActChange])
            All_Act_Changes.append(ActChange)

        # Apply adjustments to everything
        PostSBDict = {}
        print "Applying changes to moisture profiles."
        for k, v in TemporaryDatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in xrange(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], SBGainDict[k]))
            PostSBDict[k] = AdjustedReels
        PostSBDict["CTRL.STMBX (??)"] = SteamboxDataset
        CPGainDict["CTRL.STMBX (??)"] = 0
        SBGainDict["CTRL.STMBX (??)"] = 1

        if OutputCSVs:
            print "Outputting to CSV: %s" % PostSBAdjustmentDataFile
            with open(PostSBAdjustmentDataFile, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in PostSBDict.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

        # Return profile to CP-Moisture Controlled

        All_Act_Changes = []

        print "Adjusting CP actuators to account for new profiles"
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
        print "Applying CP changes to all profiles."
        for k, v in TemporaryDatasetDictionary.iteritems():
            AdjustedReels = []
            for reel_i in xrange(len(v)):
                AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], CPGainDict[k]))
            FinalReelDict[k] = AdjustedReels

        if LowerMemoryUsage:
            TemporaryDatasetDictionary.clear()

        print "Calculating Final Roll Averages..."
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

        print "Outputting final CSV of Roll Averages to %s." % StoreNewRollAverages
        TempList = []
        with open(StoreNewRollAverages, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            writeobject.writerow(HeaderList)
            for i in xrange(len(ReelAveragesDict[HeaderList[0]])):
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
            print "Outputting CSVs: %s, %s, & %s" % (
            StoreAdjustedRawData, StoreAdjustedCPAverages, StoreAdjustedSBAverages)
            CPAverages = {}
            SBAverages = {}

            with open(StoreAdjustedRawData, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in FinalReelDict.iteritems():
                    writeobject.writerow([k])
                    for reel in v:
                        writeobject.writerow(reel)

            with open(StoreAdjustedCPAverages, 'wb') as csvfile:
                writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
                for k, v in FinalReelDict.iteritems():
                    CPAverages[k] = AAR.RollAverages(v, CPActNum)
                    writeobject.writerow([k])
                    for actuatorbin in CPAverages[k]:
                        writeobject.writerow(actuatorbin)

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

        with open(StoreScrubbedHighResOriginal, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for reel_index in xrange(len(TempList)):
            if len(TempList[reel_index]) == 1:
                HeaderIndexList.append(reel_index)
        print HeaderIndexList

        TotalNumReels = int((len(TempList) - 1) / len(HeaderIndexList))
        RandReelArray = []
        for x in range(RandomReelNum):
            RandReelArray.append(randint(0, TotalNumReels))

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index])
            DictName = "Scrubbed Original High Res " + TempList[line_index][0] + " " + str(rand_index)
            ComparisonDictionary[DictName] = TempArray

        ComparisonDictionary["Scrubbed Original High Res CTRL.STBX (??)"] = [[StartingSBPos] * SBActNum] * RandomReelNum

        # Clear Memory JIC
        TempList = []

        # Record CP-Normalization profiles

        with open(PostCPWeightDataFile, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index])
            DictName = "CWT-Normalized High Res " + TempList[line_index][0] + " " + str(rand_index)
            ComparisonDictionary[DictName] = TempArray

        ComparisonDictionary["CWT-Normalized High Res CTRL.STMBX (??)"] = [[StartingSBPos] * SBActNum] * RandomReelNum

        TempList = []
        HeaderList.append("CTRL.STMBX (??)")
        # Record SB-Affected Profiles (before CP readjustment)

        with open(PostSBAdjustmentDataFile, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index])
            DictName = "SB-Effected High Res " + TempList[line_index][0] + " " + str(rand_index)
            ComparisonDictionary[DictName] = TempArray

        # Record SB-Affected Profiles (after CP readjustment)

        TempList = []

        with open(StoreAdjustedRawData, 'rb') as csvfile:
            readobject = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
            # Record every high-res profile to a list line - this is one reel per line.
            for line in readobject:
                TempList.append(line)

        for line_index in HeaderIndexList:
            TempArray = []
            for rand_index in RandReelArray:
                TempArray.append(TempList[line_index + rand_index])
            DictName = "Final High Res " + TempList[line_index][0] + " " + str(rand_index)
            ComparisonDictionary[DictName] = TempArray

        with open(ComparisonReels, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in ComparisonDictionary.iteritems():
                writeobject.writerow([k] + v)


    print "Hello World"
