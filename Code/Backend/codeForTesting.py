#this is a modified version of our backend script -- refactored for easier testing of specficially these methods


import configparser
import importlib
import os
import sys

import ds4se.facade as facade

# inputs from the user for the traceability library to use to calculate the links
# config = configparser.ConfigParser()
# config.read('../../pyConfig.ini')
# facade = importlib.import_module(config["Imports"]["Import1"])
# traceLink = getattr(facade,config["FunctionName"]["Function"])
# param1 = config["FunctionParams"]["Param1"]
# param2 = config["FunctionParams"]["Param2"]

traceLink = facade.TraceLinkValue
# param1 = "word2vec"
# param2 = "WMD"

# function to calculate a new probability based on the feedback from the user
def new_probability(num1, num2):   #written as a function to be more easily updated to a different algorithm later
    return (num1+num2)/2
    
# calculates the traceabilty value for the given source and target with the given model(from a traceability library) and metric if needed
def traceabilityResult(source, target, targetFile, feedback, model, metric = None):
    with open(os.path.join(target, targetFile), 'r', encoding='latin1') as f: # open in readonly mode
        targetData = f.read()
        f.close()
    values = {}
    for sourceFilename in os.listdir(source):  # goes to each source file and compares the current target file
        with open(os.path.join(source,sourceFilename), 'r', encoding='latin1') as f:
            sourceData = f.read()
            f.close()
        if metric is None:
            result = traceLink(sourceData,targetData, model)
        else:
            result = traceLink(sourceData,targetData, model, metric)

        traceResult = result[1]
        tmpStr = targetFile+" "+sourceFilename
        if tmpStr in input:  # check if the user input their own traceability value for this file pair
            traceResult = new_probability(traceResult, float(feedback[tmpStr]))  # recalculating the probability

        values[sourceFilename] = traceResult  # stores the values with the source filename as the key of a dictionary
    return values

# outputs the traceability value for the given model to a file, organizes/labels the output
def outputValues(model, valuesDict, outputThreshold, curFile, output):   
    
        for key in valuesDict:
            if (float(valuesDict[key]) >= outputThreshold):
                print("Source File: ",key, "Target File: ", curFile, "Traceability: ",valuesDict[key])
                output.write("Model:"+ model + "\nSource File: " + key + ", Target File: " + curFile + ", Traceability: " + str(valuesDict[key]) + '\n')
        

# os.chdir('../../')
# sourcePath = os.getcwd() + sys.argv[1]
# targetPath = os.getcwd()
# targetList = open(os.getcwd() + sys.argv[2], 'r', encoding='latin1').read().splitlines()

os.chdir("../../datasets/LibEST_semeru_format")
sourcePath=os.getcwd()+"/requirements"
targetPath=os.getcwd()+"/source_code"
targetFile = "est_client.c"
targetList = []
singleFile = True
if singleFile:
    targetList.append(targetFile)
else:
    targetList = os.listdir(targetPath)

# threshold = float(sys.argv[4]) # the threshold for what traceability values to return
# feedbackSourceList = sys.argv[5].split(",")  # user feedback on the traceability value
# feedbackTargetList = sys.argv[6].split(",")
# feedbackNumList = sys.argv[7].split(",")

threshold = 0
feedbackSourceList = "est_ossl_util.c,est.c".split(",")
feedbackTargetList = "targetString=RQ4.txt,RQ8.txt".split(",")
feedbackNumList = "21.0,24.0".split(",")
# print(feedbackSourceList, feedbackTargetList, feedbackNumList)

input={} # dictionary to be filled
for i in range (len(feedbackSourceList)):
    input[feedbackSourceList[i]+" "+feedbackTargetList[i]]=float(feedbackNumList[i]) # the dictionary with (targetFile, sourceFile) -- a tuple -- as the key and the probability as the value


# for targetFilename in targetList: # calculate the traceability values for each target and source file pair

#     valuesWMD = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)
#     valuesSCM = traceabilityResult(sourcePath, targetPath, targetFilename, input, "word2vec", "SCM")
#     valuesDoc = traceabilityResult(sourcePath, targetPath, targetFilename, input, "doc2vec")



#     with open(os.getcwd() + sys.argv[3], 'w', encoding='latin1') as writeFile:  # ouputting each of the values for the different models from DS4SE traceability library

#         outputValues("word2vec, metric = WMD", valuesWMD, threshold, targetFilename, writeFile)
#         outputValues("word2vec, metric = SCM", valuesSCM, threshold, targetFilename, writeFile)
#         outputValues("doc2vec", valuesDoc, threshold, targetFilename, writeFile)
#         writeFile.close()
