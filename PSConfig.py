# Settings imported into ProfileSimulator.py
#
# Define good data - any reels with averages / counts outside of the below ranges will be considered bad and eliminated
CWBinLimits = [15, 30]
BWBinLimits = [15, 30]
MoiBinLimits = [3, 17]
ScanCountLimits = [70, 200]
GoodGradeList = ["3587802300NAT DF"]
#
# CD Sizing Data
CPActNum = 122
SBActNum = 88
RollsPerReel = 3
StartingSBPos = 40
#
# Actuator gains - taken from MX controller
CPBWGain = -0.1328
CPCWGain = -0.0783
CPMoiGain = -0.1866
#SBMoiGain = -0.0105 # This produced a negligible impact on moisture profiles.
SBMoiGain = -.02
#
# If OutputCSVs == True, major profile datasets will be stored as CSVs. Recommend doing this for further analysis in
# Minitab or elsewhere.
OutputCSVs = True
RebuildTables = False
OutputRandomReelComparisons = True
RandomReelNum = 5
LowerMemoryUsage = True  # This won't help much - enable to clear dictonaries after they're last used.
#
# File names specified: These will be read/written regardless of OutputCSVs
RawDataFile = "PM2_Data_Set_All.csv"
# RawDataFile = "TestData.csv"
#
# File names specified: These will be written if Output CSVs is true.
StoreScrubbedHighResOriginal = "RealScrubbedHighRes.csv"
StoreRealCPAverages = "RealCPAverages.csv"
StoreRealRollAverages = "RealRollAverages.csv"
StoreRealSBAverages = "RealSBAverages.csv"
PostCPWeightDataFile = "NormalizedWeight.csv"
PostSBAdjustmentDataFile = "SteamboxEffect.csv"
PostCPMoistureNormalizationDataFile = "FinalRawData.csv"
StoreTemporaryCPAverages = "WeightWeightedCPAverages.csv"
StoreAdjustedCPAverages = "NewCPAverages.csv"
StoreAdjustedSBAverages = "NewSBAverages.csv"
StoreNewRollAverages = "NewRollAverages.csv"
StoreAdjustedRawData = "NewHighResProfiles.csv"
ComparisonReels = "ComparisonReels.csv"
