import unittest
from codeForTesting import *

class SimpleTest(unittest.TestCase):
	# the setup for all the test cases
	os.chdir("../../datasets/LibEST_semeru_format")
	sourcePath=os.getcwd()+"/requirements"
	targetPath=os.getcwd()+"/source_code"
	targetFile = "est_client.c"
	feedbackSourceList = "est_ossl_util.c,est_client.c".split(",")
	feedbackTargetList = "targetString=RQ4.txt,RQ8.txt".split(",")
	feedbackNumList = "21.0,24.0".split(",")
	input={} # dictionary to be filled
	for i in range (len(feedbackSourceList)):
		input[feedbackSourceList[i]+" "+feedbackTargetList[i]]=float(feedbackNumList[i])

	# tests the developer feedback function, which right now is just the average of two values
	def testFeedbackFunction(self):
		ans = new_probability(1, 3)
		self.assertEqual(ans, 2.0)

	# tests that there are traceability values produced for the word2vec model and WMD metric for one target file
	def testTraceabilityResultWMDwithOneTarget(self):
		param1 = "word2vec"
		param2 = "WMD"
		singleFile = True
		targetList = []
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)

		self.assertIsNotNone(values)

	# tests that there are traceability values produced for the word2vec model and WMD metric for all target files
	def testTraceabilityResultWMDwithAllTargets(self):
		param1 = "word2vec"
		param2 = "WMD"
		singleFile = False
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)
			self.assertIsNotNone(values)
	
	# tests that there are traceability values produced for the word2vec model and SCM metric for one target file
	def testTraceabilityResultSCMWithOneTarget(self):
		param1 = "word2vec"
		param2 = "SCM"
		singleFile = True
		targetList = []
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)

		self.assertIsNotNone(values)

	# tests that there are traceability values produced for the word2vec model and SC< metric for all target files
	def testTraceabilityResultSCMWithAllTargets(self):
		param1 = "word2vec"
		param2 = "SCM"
		singleFile = False
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)
			self.assertIsNotNone(values)
	
	# tests that there are traceability values produced for the doc2vec model for one target file
	def testTraceabilityResultDoc2VecWithOneTarget(self):
		param1 = "doc2vec"
		singleFile = True
		targetList = []
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1)

		self.assertIsNotNone(values)

	# tests that there are traceability values produced for the doc2vec model for all target files	
	def testTraceabilityResultDoc2VecWithAllTargets(self):
		param1 = "doc2vec"
		singleFile = False
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1)

			self.assertIsNotNone(values)

	# generates values with and without developer feedback for a certain file to make sure the feedback is taken into account
	def testFeedbackTakenIntoAccount(self):
		param1 = "word2vec"
		param2 = "WMD"
		singleFile = True
		targetList = []
		if singleFile:
			targetList.append(targetFile)
		else:
			targetList = os.listdir(targetPath)

		feedbackSourceList = ""
		feedbackTargetList = ""
		feedbackNumList = ""
		input={} # dictionary to be filled
		for i in range (len(feedbackSourceList)):
			input[feedbackSourceList[i]+" "+feedbackTargetList[i]]=float(feedbackNumList[i])	

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)

		feedbackSourceList = "est_ossl_util.c,est_client.c".split(",")
		feedbackTargetList = "targetString=RQ4.txt,RQ8.txt".split(",")
		feedbackNumList = "21.0,24.0".split(",")
		input={} # dictionary to be filled
		for i in range (len(feedbackSourceList)):
			input[feedbackSourceList[i]+" "+feedbackTargetList[i]]=float(feedbackNumList[i])

		for targetFilename in targetList: # calculate the traceability values for each target and source file pair
			new_values = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2)
		
		avg = (new_values["RQ8.txt"]+values["RQ8.txt"])/2
		self.assertEquals(new_values["RQ8.txt"], avg)

if __name__ == '__main__':
	unittest.main()
