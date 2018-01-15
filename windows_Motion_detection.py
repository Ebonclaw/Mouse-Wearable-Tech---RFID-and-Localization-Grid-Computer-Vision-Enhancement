# Author: Ziyue Hu
# This Code Runs with command $ python windows_Motion_detector.py --video example_01.h264 --micenumber 2
# blank --video argument calls pi camera
# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
import numpy as np
#from matplotlib import pyplot as plt

import os

from CoordTracker import *
from TagReader import *
# Watershed
# from skimage.feature import peak_local_max
# from skimage.morphology import watershed
# from scipy import ndimage

method1 = True; method2 = False; Dist = None; 
background_path = "MouseTrack_bg2.h264"
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-om", "--onemouse", type=int, default=4500, help="minimum area of one mouse")
ap.add_argument("-tm", "--twomice", type=int, default=13000, help="maximum area of two mouse") # default area is tested
ap.add_argument("-ttm","--threemice",type=int, default=20000, help="maximum area of three mouse")
ap.add_argument("-m", "--micenumber" ,type=int,default=3,help="number of mice in cage")
ap.add_argument("-id","--rfidfile", help="path to the video file")
ap.add_argument("-bg", "--background" ,default=None,help="path to background")
ap.add_argument("-rr","--refreshrate",type=int,default=1,help="how many data entries output per second")
ap.add_argument("-th","--threshold",type=int, default = 90, help="threshold for image threshing")
ap.add_argument("-of","--outfile",default = 'rfid_video_outfile.txt',help="name of output file")
# TODO: add mice number and path to tag id
args = vars(ap.parse_args())
 
# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
	camera = cv2.VideoCapture(0)
	time.sleep(0.25)
 
# otherwise, we are reading from a video file
else:
	camera = cv2.VideoCapture(args["video"])
	background = None
	if args["background"] == None:
		background = cv2.VideoCapture(background_path)
	else: 
		# add into main loop to deal with this
		background = cv2.imread(args["background"],1)

# ==================> [INITIALIZATIONS] <=================
 
# initialize the first frame in the video stream
firstFrame = None

# initialize mice tracker: 3 mice
total_mice = args["micenumber"]
if total_mice>3:
	total_mice = 3
miceList = list()
mouse1 = 0
mouse2 = 1
if total_mice == 3:
	mouse3 = 2 # Threemiceenable
miceList.append(CoordTracker((0,0),mouse1)) # randomnize
miceList.append(CoordTracker((499,499),mouse2))
if total_mice == 3:
	miceList.append(CoordTracker((250,250),mouse3))# Threemiceenable
# Mice Cage System Monitor:
miceCage = MouseCage(miceList)
#initialize RFID Map
rfidReaders = TagReader(args["rfidfile"]) # TODO: use argument

#initialize Sychronization Timer:
sync_timer_video = 0; # video timer start from zero, let tagreader do time correct
sync_timer_inc = 1/30 # increment per frame: our video is 30 hz
initTime = rfidReaders.getInitTime() # just for testing, initiate instance will auto init time
if(initTime != False):
	print("init Time: %d" % initTime)
# initialize
(tag,coord_tag,sync_timer_tag) = rfidReaders.getNextTagReading() # it needs to be here b/c we are letting rfid wait for video
# print(" tag reading parse: %s (%d,%d) %d" % (tag,coord,timest))
readerMap = None #initialize

# initialize file writer
fileWriter = FileWriter(str(args["outfile"]))


# TEST variables:
mouse_area_min = 5000
mouse_area_max = 5000

#TEST: first 10 frames:
test_frame_count = 0


# ==================> [MAIN LOOP] <=================
# loop over the frames of the video
# Current loop time less than: 0.05 sec
while True: 



	# Flags:
	mouse_merge = False # if two mouse come too close
	two_merge 	= False
	if total_mice == 3:
		three_merge = False # Threemiceenable
	g_mouse_merge = False # global mouse merge: if there are merge at all

	# grab the current frame and initialize the occupied/unoccupied
	# text
	(grabbed, frame) = camera.read()
	text = "Unoccupied"
 
	# if the frame could not be grabbed, then we have reached the end
	# of the video
	if not grabbed:
		break
 
	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)
 
	# if the first frame is None, initialize it
	if firstFrame is None:
		# we are using different file for background
		(grabbg,backgroundFrame) = background.read()

		if not grabbed:
			break

		backgroundFrame = imutils.resize(backgroundFrame, width=500)
		backgroundFrame = cv2.cvtColor(backgroundFrame, cv2.COLOR_BGR2GRAY)
		backgroundFrame = cv2.GaussianBlur(backgroundFrame, (21, 21), 0) 
		firstFrame = backgroundFrame

		readerMap = rfidReaders.getReaderMap(backgroundFrame,-50,0) # initialize map, TODO: offsets will be in argument
		continue
	# TEST:
	# test_frame_count += 1
	# if test_frame_count < 8*30:
	# 	continue

	# compute the absolute difference between the current frame and
	# first frame
	frameDelta = cv2.absdiff(firstFrame, gray)
	thresh = cv2.threshold(frameDelta, args["threshold"], 255, cv2.THRESH_BINARY)[1]
 	
 	# edge detection (TODO: delete. not so useful):
	# frameEdge = cv2.Canny(frame,100,200)

	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)
	(_,cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

	# Loop over raw contours:
	# 	1. find analysable contours
	# 	2. update mouse flag
	# 	3. store to array
	contour_count = 0
	contour_list = list()
	mouse_merge_flag = list()
	

	# ============> First Contour Iteration <============
	for raw_contour in cnts:
		# if the contour is too small, ignore it 
		if cv2.contourArea(raw_contour) < args["onemouse"]:
			continue
 		
 		# trying to set an upper bound for windows to eliminate merging mice
 		# TODO: redesign mouse merge detect
		if (cv2.contourArea(raw_contour) > args["twomice"]) and (cv2.contourArea(raw_contour) < args["threemice"]):
			mouse_merge = True
			g_mouse_merge = True
			two_merge = True
		
		
		elif cv2.contourArea(raw_contour) > args["threemice"]:
			mouse_merge = True
			g_mouse_merge = True
			three_merge = True	

		contour_list.append(raw_contour)
		mouse_merge_flag.append(mouse_merge)
		contour_count += 1 
		mouse_merge = False # reset flag

	# decide merge cases # Threemiceenable	
	# if contour_count == 1 :
	# 	if(g_mouse_merge == True): # troublesome case: one out of bound and two merge: added three mice area
	# 		three_merge = True
	# 	# else there are two out of bound
	# elif contour_count == 2:
	# 	if g_mouse_merge == True:
	# 		two_merge = True
	# 	# else there are one out of bound
	# elif contour_count > 3:
	# 	#something wrong:
	# 	print("more than three contour detected")

	

	# ============> Second Contour Iteration <============ [for single]
	single_id = None
	contour_index = 0
	# loop over the contours
	identity_coordinate_single = list()
	for contour in contour_list:
		# unpack data
		mouse_merge = mouse_merge_flag[contour_index]
		contour_index += 1

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		
		angle = 0
		rotated_box = cv2.minAreaRect(contour) 
		if mouse_merge == False: #if they do not merge, print green box
			box = cv2.boxPoints(rotated_box)
			box = np.int0(box)
			cv2.drawContours(frame,[box],0,(0,255,0),2)
			angle = rotated_box[2]
			
		else: # if they merges, skip
			continue
			
			# mouse_merge = False

		# Find center of contour for single mouse
		
		M = cv2.moments(contour)
		center_X = int(M["m10"] / M["m00"])
		center_Y = int(M["m01"] / M["m00"])
		center_m = (center_X,center_Y)

		# store to tracker
		identity_coordinate_single.append(center_m)
		
		
	# Tracking:
	miceList[mouse1].updateCoordinate_single(identity_coordinate_single)
	miceList[mouse2].updateCoordinate_single(identity_coordinate_single)
	if total_mice == 3:
		miceList[mouse3].updateCoordinate_single(identity_coordinate_single) # Threemiceenable

	# Overlap prevent/ lost handle:
	# miceCage.sanitizeCageMemberIdentities(miceList,identity_coordinate_single)
	if total_mice == 3:
		if (two_merge == True): #Threemiceenable
			single_id = miceCage.sanitizeSingleMouse(miceList)
		# TODO: deal with extra contour
		# print("single is: mouse %d" % (single_id+1))

	# ============> Third Contour Iteration <============ [for merged]
	contour_index = 0
	identity_coordinate_merge = list()
	thresh_test = np.zeros(thresh.shape,np.uint8)#TEST
	
	# TODO: check 3 merge, here we mainly handles two merge
	for contour in contour_list:
		
		# unpack data
		mouse_merge = mouse_merge_flag[contour_index]
		contour_index += 1
		# print("mouse merge:" , mouse_merge)
		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		
		angle = 0
		rotated_box = cv2.minAreaRect(contour) 
		if mouse_merge == False: #if they do not merge, pass
			continue
			
		else: # if they merges, print red box
			box = cv2.boxPoints(rotated_box)
			box = np.int0(box)
			cv2.drawContours(frame,[box],0,(0,0,255),2)
			angle = rotated_box[2]
			
			# mouse_merge = False

		# Find center of contour for single mouse
		
		M = cv2.moments(contour)
		center_X = int(M["m10"] / M["m00"])
		center_Y = int(M["m01"] / M["m00"])
		center_m = (center_X,center_Y)
		# print("center",center_m)
		# handle two mice merge 
		# TODO: add flag for merge case

		# Two mouse merging relative position approximation & tracking
		# ***** METHOD 1 : Image moment ******
		
		if mouse_merge == True and method1 == True:

			# a small twist for drawContour method: it only takes list and draw its element
			contour_f = list()
			contour_f.append(contour) 

			# Two mice case:
			if (two_merge == True) or (total_mice < 3): # Threemiceenable
				# position recorder
				orientation1 = list()
				orientation2 = list()
				orientation3 = list()
				orientation4 = list()
				# ------------->> [First orientation] <<----------------

				# find mid-point of opposite side
				box_mid_1 = (box[0] + box[1])*0.5
				box_mid_3 = (box[2] + box[3])*0.5
				# orientation track
				orientation1.append(box_mid_1)
				orientation1.append(box_mid_3)
				thresh_1 = thresh.copy() # TODO: check and delete
				# thresh_1 = numpy.zeros()
				# print("image type: ",thresh_1.shape)
				thresh_1 = np.zeros(thresh.shape,np.uint8)# TEST
				cv2.drawContours(thresh_1,contour_f,-1,255,-1)# TEST
				# draw line on processed frame(thresh) copy
				cv2.line(thresh_1,(int(box_mid_1[0]),int(box_mid_1[1])),center_m,(0,0,0),5)
				cv2.line(thresh_1,(int(box_mid_3[0]),int(box_mid_3[1])),center_m,(0,0,0),5)
				
				# refind contour:
				(_,subcnts_1, _) = cv2.findContours(thresh_1.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
				for cnt in subcnts_1:
					# we only look at min area, giving it a bit more flexibility
					if cv2.contourArea(cnt) < (args["onemouse"]*(2/3)):
						continue
					M_1 = cv2.moments(cnt)
					center_X_1 = int(M_1["m10"] / M_1["m00"])
					center_Y_1 = int(M_1["m01"] / M_1["m00"])
					
					# store to tracker 
					orientation1.append((center_X_1, center_Y_1))
				# ------------->> [Second orientation] <<----------------
				# repeat first one
				box_mid_2 = (box[1] + box[2])*0.5
				box_mid_4 = (box[3] + box[0])*0.5
				# orientation track
				orientation2.append(box_mid_2)
				orientation2.append(box_mid_4)

				thresh_2 = thresh.copy()
				thresh_2 = np.zeros(thresh.shape,np.uint8)# TEST
				cv2.drawContours(thresh_2,contour_f,-1,255,-1)# TEST

				cv2.line(thresh_2,(int(box_mid_2[0]),int(box_mid_2[1])),center_m,(0,0,0),3)
				cv2.line(thresh_2,(int(box_mid_4[0]),int(box_mid_4[1])),center_m,(0,0,0),3)
				# refind contour:
				(_,subcnts_2, _) = cv2.findContours(thresh_2.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
				for cnt in subcnts_2:
					# we only look at min area, giving it a bit more flexibility
					if cv2.contourArea(cnt) < (args["onemouse"]*(2/3)):
						continue
					M_2 = cv2.moments(cnt)
					center_X_2 = int(M_2["m10"] / M_2["m00"])
					center_Y_2 = int(M_2["m01"] / M_2["m00"])
					
					# store to tracker 
					orientation2.append((center_X_2, center_Y_2))
				# ------------->> [Third orientation] <<---------------- diagonal
				# repeat first one
				box_1 = box[0]
				box_3 = box[2]
				# orientation track
				orientation3.append(box_1)
				orientation3.append(box_3)

				thresh_3 = thresh.copy()
				thresh_3 = np.zeros(thresh.shape,np.uint8)# TEST
				cv2.drawContours(thresh_3,contour_f,-1,255,-1)# TEST
				cv2.line(thresh_3,(int(box_1[0]),int(box_1[1])),center_m,(0,0,0),3)
				cv2.line(thresh_3,(int(box_3[0]),int(box_3[1])),center_m,(0,0,0),3)
				# refind contour:
				(_,subcnts_3, _) = cv2.findContours(thresh_3.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
				for cnt in subcnts_3:
					# we only look at min area, giving it a bit more flexibility
					if cv2.contourArea(cnt) < (args["onemouse"]*(2/3)):
						continue
					M_3 = cv2.moments(cnt)
					center_X_3 = int(M_3["m10"] / M_3["m00"])
					center_Y_3 = int(M_3["m01"] / M_3["m00"])
					
					# store to tracker 
					orientation3.append((center_X_3, center_Y_3))
					
				# ------------->> [Third orientation] <<---------------- diagonal
				# repeat first one
				box_2 = box[1]
				box_4 = box[3]
				# orientation track
				orientation4.append(box_2)
				orientation4.append(box_4)

				thresh_4 = thresh.copy()
				thresh_4 = np.zeros(thresh.shape,np.uint8)# TEST
				cv2.drawContours(thresh_4,contour_f,-1,255,-1)# TEST
				cv2.line(thresh_4,(int(box_2[0]),int(box_2[1])),center_m,(0,0,0),3)
				cv2.line(thresh_4,(int(box_4[0]),int(box_4[1])),center_m,(0,0,0),3)
				# refind contour:
				(_,subcnts_4, _) = cv2.findContours(thresh_4.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
				for cnt in subcnts_4:
					# we only look at min area, giving it a bit more flexibility
					if cv2.contourArea(cnt) < (args["onemouse"]*(2/3)):
						continue
					M_4 = cv2.moments(cnt)
					center_X_4 = int(M_4["m10"] / M_4["m00"])
					center_Y_4 = int(M_4["m01"] / M_4["m00"])
					
					# store to tracker 
					orientation4.append((center_X_4, center_Y_4))
					# print("center4: ",center_X_4, center_Y_4)# TODO: delete
					
				# Tracking
				# TODO: in 3 mice case need to identify which two are merged-> can see which two were closest
				identity_coordinate_merge = miceList[mouse1].updateCoordinate_double(miceList[mouse2],orientation1,orientation2,orientation3,orientation4)

				if total_mice == 3:# Threemiceenable
					if single_id == mouse1:
						identity_coordinate_merge = miceList[mouse2].updateCoordinate_double(miceList[mouse3],orientation1,orientation2,orientation3,orientation4)
					elif single_id == mouse2:
						identity_coordinate_merge = miceList[mouse3].updateCoordinate_double(miceList[mouse1],orientation1,orientation2,orientation3,orientation4)
					elif single_id == mouse3:
						identity_coordinate_merge = miceList[mouse1].updateCoordinate_double(miceList[mouse2],orientation1,orientation2,orientation3,orientation4)

				# print("updating two")
				# print(miceList[mouse1].getCurrentCoordinate())
				# print(miceList[mouse2].getCurrentCoordinate())

				# miceCage.sanitizeCageMemberIdentities(miceList,identity_coordinate_merge)


		# ****** Method 2 : Watershed Algo *****
		
		elif mouse_merge == True and method2 == True:

			placehold = 0
			# shifted = cv2.pyrMeanShiftFiltering(frame, 21, 51)
			# gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
			# # thresh = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
			# frameDelta = cv2.absdiff(firstFrame, gray)
			# thresh = cv2.threshold(frameDelta, 70, 255, cv2.THRESH_BINARY)[1]
			# D = ndimage.distance_transform_edt(thresh)
			# Dist = cv2.normalize(D, D, 0, 1., norm_type = cv2.NORM_MINMAX);
			# localMax = peak_local_max(D, indices=False, min_distance=40,labels=thresh)
			# markers = ndimage.label(localMax, structure=np.ones((3, 3)))[0]
			# labels = watershed(-D, markers, mask=thresh)
			# lable_num =0
			# for label in np.unique(labels):
			# 	# if the label is zero, we are examining the 'background'
			# 	# so simply ignore it
			# 	if label == 0:
			# 		continue

			# 	lable_num +=1
			# 	print(lable_num)
			# 	# otherwise, allocate memory for the label region and draw
			# 	# it on the mask
			# 	mask = np.zeros(gray.shape, dtype="uint8")
			# 	mask[labels == label] = 255
			  
			# 	# detect contours in the mask and grab the largest one
			# 	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
			# 		cv2.CHAIN_APPROX_SIMPLE)[-2]
			# 	c = max(cnts, key=cv2.contourArea)
			 
			# 	# draw a circle enclosing the object
			# 	((x, y), r) = cv2.minEnclosingCircle(c)
			# 	cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
	# Debug: Coordinates
	# print(identity_coordinate_merge)
	# print(identity_coordinate_single)
	# print(identity_coordinate_single+identity_coordinate_merge)	

	# Overlap prevent/ lost handling:
	miceCage.sanitizeCageMemberIdentities(miceList,identity_coordinate_single+identity_coordinate_merge)
	
	# update synchronize timer:
	sync_timer_video += sync_timer_inc
	if (sync_timer_video >= sync_timer_tag):
		if mouse_merge :
			print("mice merged")
		print("time: %f "% (sync_timer_video),"tracker 1 ", miceList[mouse1].tag_ID, "tracker 2 ",miceList[mouse2].tag_ID)
		print("update rfid: ",tag)
		if coord_tag != None:
			miceCage.synchronizeWithRFID(readerMap[coord_tag[0]][coord_tag[1]],tag,miceList)

		(tag,coord_tag,sync_timer_tag) = rfidReaders.getNextTagReading()

	

	(lost,coord) = miceList[mouse1].getCurrentCoordinate()
	if (lost == False):
		cv2.circle(frame, coord, 7, (255, 255, 255), -1)
		cv2.putText(frame,"m1",coord, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
	else: 
		cv2.circle(frame, coord, 7, (0, 0, 255), -1)
		cv2.putText(frame,"m1", coord, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
	(lost2,coord2) = miceList[mouse2].getCurrentCoordinate()
	if (lost2 == False):
		cv2.circle(frame, coord2, 7, (255, 255, 255), -1)
		cv2.putText(frame,"m2", coord2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
	else: 
		cv2.circle(frame, coord2, 7, (0, 0, 225), -1)
		cv2.putText(frame,"m2", coord2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
	if total_mice == 3: # Threemiceenable 
		(lost3,coord3) = miceList[mouse3].getCurrentCoordinate()
		if (lost3 == False):
			cv2.circle(frame, coord3, 7, (255, 255, 255), -1)
			cv2.putText(frame,"m3", coord3, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
		else: 
			cv2.circle(frame, coord3, 7, (0, 0, 225), -1)
			cv2.putText(frame,"m3", coord3, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)	
	# Write to output file:
	for tracker in miceList:
		(lost,coord) = tracker.getCurrentCoordinate()
		fileWriter.writeToFile(sync_timer_video,tracker.tag_ID,coord)


	# Draw RFID reader map: # TODO: enable
	for rows in readerMap:
		for readerPosition in rows:
			cv2.circle(frame, (int(readerPosition[0]),int(readerPosition[1])), 7, (255, 255, 255), -1)
	cv2.circle(frame,(int(readerMap[coord_tag[0]][coord_tag[1]][0]),int(readerMap[coord_tag[0]][coord_tag[1]][1])), 7, (0, 255, 0), -1)

	# draw the text and timestamp on the frame
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
 	
	# show the frame 
	cv2.imshow("Mouse Tracking", frame)
	
	cv2.imshow("Thresh", thresh)
	if (method2 ==True):
		try:
			cv2.imshow("Thresh",Dist)
		except Exception as e:
			pass
	# cv2.imshow("",frameEdge)
	# TEST:
	# if mouse_merge : # for observation
	time.sleep(0.1)
	# Merge Flag reset:
	mouse_merge = False



	# End loop
	key = cv2.waitKey(1) & 0xFF
 
	# if the `q` key is pressed, break from the lop
	if key == ord("q"):
		break


 
# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
print("[INFO] Done")