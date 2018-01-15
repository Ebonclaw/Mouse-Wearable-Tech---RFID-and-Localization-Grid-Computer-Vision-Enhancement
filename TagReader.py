# This file is used to process read in information from tag readers

import os
import time
import numpy as np
import math


class TagReader:


	def __init__(self,file_name):
		self.file_name = file_name
		self.readerNum_X = 6
		self.readerNum_Y = 3
		self.readerMap = None
		self.readerLinePointer = None
		self.initTime = None # TagReader does the time correction
		self.getInitTime() # initialize time right after
		self.fps = 30 
		

	# Precondition: file composes of rows of mice information
	# Return formate: ( Tagnumber , coordinate , timestamp(with correction) )
	# Current format example: '[52, 52, 70, 66, 48] 2-3 1509659961.271041\n'
	def getNextTagReading(self):
		if (self.readerLinePointer == None): # meaning reader line pointer has not been initiated
			self.getInitTime()
		with open(self.file_name, "r") as tagFile:
			tagFile.seek(self.readerLinePointer)# continue from where we left off
			nextRecord = tagFile.readline()
			self.readerLinePointer = tagFile.tell()# record this position for next read
			nextRecord = nextRecord.split(']')
			# Tagnumber: we leave tagnumber as is for now TODO: convert tag number into number maybe
			nextRecord[0] = nextRecord[0][1:]
			tmp = nextRecord[1][1:].split(' ')
			# coordinate:
			nextRecord[1] = tmp[0]
			nextRecord[1] = nextRecord[1].split('-') 
			nextRecord[1][0] = int(nextRecord[1][0])-1
			nextRecord[1][1] = int(nextRecord[1][1])-1
			# # timestamp:
			nextRecord.append(float(tmp[1].strip())-self.initTime)

			#TODO: check end of file
			return nextRecord
			

	# Note: mapping of RFID is know and hardcoded
	# PostCondition: need to minus 1 when try to read coordinate
	def getReaderMap(self,frame,y_offset,x_offset):#, cage_length, cage_width, frame):
		frame_length = np.shape (frame)[0]
		frame_width = np.shape (frame)[1]
		readerInt_Y = frame_length/self.readerNum_Y
		readerInt_X = frame_width/self.readerNum_X

		self.readerMap = np.zeros(shape=(self.readerNum_Y,self.readerNum_X)) # np zeros read Y first
		# hard coded
		self.readerMap = [[(readerInt_X/2,readerInt_Y/2 + y_offset),(readerInt_X*1.5,readerInt_Y/2 + y_offset),(readerInt_X*2.5,readerInt_Y/2 + y_offset),(readerInt_X*3.5,readerInt_Y/2 + y_offset),(readerInt_X*4.5,readerInt_Y/2 + y_offset),(readerInt_X*5.5,readerInt_Y/2 + y_offset)],
					 [(readerInt_X/2,readerInt_Y*1.5 + y_offset),(readerInt_X*1.5,readerInt_Y*1.5 + y_offset),(readerInt_X*2.5,readerInt_Y*1.5 + y_offset),(readerInt_X*3.5,readerInt_Y*1.5 + y_offset),(readerInt_X*4.5,readerInt_Y*1.5 + y_offset),(readerInt_X*5.5,readerInt_Y*1.5 + y_offset)],
					 [(readerInt_X/2,readerInt_Y*2.5 + y_offset),(readerInt_X*1.5,readerInt_Y*2.5 + y_offset),(readerInt_X*2.5,readerInt_Y*2.5 + y_offset),(readerInt_X*3.5,readerInt_Y*2.5 + y_offset),(readerInt_X*4.5,readerInt_Y*2.5 + y_offset),(readerInt_X*5.5,readerInt_Y*2.5 + y_offset)]]
		return self.readerMap

	# Purpose: return Time written in the first lane (video start time)
	# 		   if no time is read, return false
	# TODO: what if function is called after getNextTagReading() --> make decision
	def getInitTime(self):
		if(self.initTime != None):
			return self.initTime
		else: # will be called once per file
			with open(self.file_name, "r") as tagFile:
				tagFile.seek(0) 
				self.initTime = tagFile.readline()
				try: 
					self.initTime = int(float(self.initTime.strip()))
					self.readerLinePointer = tagFile.tell()# update pointer
					tagFile.close()
					print(self.readerLinePointer)
					return self.initTime
				except Exception as e:
					tagFile.close()
					print("first line not a pure time stamp")
					return False # cast fail: not pure int string

			print("cannot open file")
			return False # open file fail
