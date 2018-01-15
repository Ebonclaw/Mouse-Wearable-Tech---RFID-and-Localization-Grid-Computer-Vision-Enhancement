# Author: Ziyue Hu
# Project ENPH 479
# Description: this is a class that helps easy tracking of coordinate 
# 			   of specific object given possibly good coordinates
import os
import time
import numpy as np
import math

class CoordTracker: 

	# C'tor
	def __init__(self,init_coordinate,tracker_id):
		self.previous_coordinate = init_coordinate;
		self.current_coordinate = self.previous_coordinate;
		self.tracker_ID = tracker_id;# starts from 0
		self.tag_ID = tracker_id # will be changed later this is just for record
		self.velocity = [0,0]; # [orientation, speed]
		self.mergeOrientation = None #should be kept same for doubly merging mice
		self.tracker_lost = False
		self.rfid_correction_timer = time.time() # for duplication prevention, update when tag_ID is corrected. randomnize in beginning 

	# Description: this method will choose the distance thats the shortest
	#			   from previous coordinate for identity tracking.
	#			   Here we assume that the camera rate is much faster than mice moving
	# Note new_coordinate 
	# input: list of (x,y)
	def updateCoordinate_single(self, new_coordinate):
		if(len(new_coordinate) == 0):
			return False
		dist_diff = np.zeros(len(new_coordinate))# list of distance

		for index in range(0,len(new_coordinate)):
			x1 = self.previous_coordinate[0]
			y1 = self.previous_coordinate[1]
			x2 = new_coordinate[index][0]
			y2 = new_coordinate[index][1]
			abs_distance = np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
			dist_diff[index] = abs_distance
		self.previous_coordinate  = self.current_coordinate;
		index_min = np.argmin(dist_diff)
		self.current_coordinate = new_coordinate[index_min]
		self.mergeOrientation = None # reset since we no longer merged


	
	# Description: this method will track seperation orientation and determine set of 
	#			   coordinate for use.
	# Purpose: if we just use single mouse update in merge case there is a chance that tracked points
	#		   will end up in different orientation sets which has 2 affects: 
	#			1. if they pass by each other straight they will have an identity swap
	#			2. it does not make sense that two mice are on different orientation set
	# Note: This method updates both mice's positions
	# Input: new_orient1 & new_orient2: element 0,1: set of opposing box midpoint and two identity coordinates
	#							element 2,3: identity(moments of seperated graphs) points
	#		 neighbour: second mouse
	def updateCoordinate_double(self, neighbour, new_orient1, new_orient2, new_orient3, new_orient4):
		# incase we do not have initialize instances
		try:
			orientations = list()
			orientations.append(new_orient1)
			orientations.append(new_orient2)
			orientations.append(new_orient3)
			orientations.append(new_orient4)
			# if merging just begun
			if ((self.mergeOrientation != neighbour.mergeOrientation) \
				or (self.mergeOrientation == None)\
				or (neighbour.mergeOrientation == None)): 
				# pick one most likely orientation to start with
				m1_x = self.previous_coordinate[0]
				m1_y = self.previous_coordinate[1]
				m2_x = neighbour.previous_coordinate[0]
				m2_y = neighbour.previous_coordinate[1]
				# identity points
				o1_x1 = new_orient1[2][0]; 	o3_x1 = new_orient3[2][0];
				o1_y1 = new_orient1[2][1]; 	o3_y1 = new_orient3[2][1];
				o1_x2 = new_orient1[3][0]; 	o3_x2 = new_orient3[3][0];
				o1_y2 = new_orient1[3][1]; 	o3_y2 = new_orient3[3][1];
				o2_x1 = new_orient2[2][0]; 	o4_x1 = new_orient4[2][0];
				o2_y1 = new_orient2[2][1]; 	o4_y1 = new_orient4[2][1];
				o2_x2 = new_orient2[3][0]; 	o4_x2 = new_orient4[3][0];
				o2_y2 = new_orient2[3][1]; 	o4_y2 = new_orient4[3][1];

			
				# the following code calculates closest distance
				# 1st orientation: First mouse
				m1_o1_1 = np.sqrt((m1_x-o1_x1)*(m1_x-o1_x1) + (m1_y-o1_y1)*(m1_y-o1_y1))
				m1_o1_2 = np.sqrt((m1_x-o1_x2)*(m1_x-o1_x2) + (m1_y-o1_y2)*(m1_y-o1_y2))
				# 1st orientation: Second mouse
				m2_o1_1 = np.sqrt((m2_x-o1_x1)*(m2_x-o1_x1) + (m2_y-o1_y1)*(m2_y-o1_y1))
				m2_o1_2 = np.sqrt((m2_x-o1_x2)*(m2_x-o1_x2) + (m2_y-o1_y2)*(m2_y-o1_y2))
				# 1st orientation assessment: sum
				o1_sum  = min([m1_o1_1,m1_o1_2]) + min([m2_o1_1,m2_o1_2])
				# 2st orientation: First mouse
				m1_o2_1 = np.sqrt((m1_x-o2_x1)*(m1_x-o2_x1) + (m1_y-o2_y1)*(m1_y-o2_y1))
				m1_o2_2 = np.sqrt((m1_x-o2_x2)*(m1_x-o2_x2) + (m1_y-o2_y2)*(m1_y-o2_y2))
				# 2st orientation: Second mouse
				m2_o2_1 = np.sqrt((m2_x-o2_x1)*(m2_x-o2_x1) + (m2_y-o2_y1)*(m2_y-o2_y1))
				m2_o2_2 = np.sqrt((m2_x-o2_x2)*(m2_x-o2_x2) + (m2_y-o2_y2)*(m2_y-o2_y2))
				# 2st orientation assessment: sum
				o2_sum  = min([m1_o2_1,m1_o2_2]) + min([m2_o2_1,m2_o2_2])
				# 3rd orientation: First mouse
				m1_o3_1 = np.sqrt((m1_x-o3_x1)*(m1_x-o3_x1) + (m1_y-o3_y1)*(m1_y-o3_y1))
				m1_o3_2 = np.sqrt((m1_x-o3_x2)*(m1_x-o3_x2) + (m1_y-o3_y2)*(m1_y-o3_y2))
				# 3rd orientation: Second mouse
				m2_o3_1 = np.sqrt((m2_x-o3_x1)*(m2_x-o3_x1) + (m2_y-o3_y1)*(m2_y-o3_y1))
				m2_o3_2 = np.sqrt((m2_x-o3_x2)*(m2_x-o3_x2) + (m2_y-o3_y2)*(m2_y-o3_y2))
				# 3rd orientation assessment: sum
				o3_sum  = min([m1_o3_1,m1_o3_2]) + min([m2_o3_1,m2_o3_2])
				# 4th orientation: First mouse
				m1_o4_1 = np.sqrt((m1_x-o4_x1)*(m1_x-o4_x1) + (m1_y-o4_y1)*(m1_y-o4_y1))
				m1_o4_2 = np.sqrt((m1_x-o4_x2)*(m1_x-o4_x2) + (m1_y-o4_y2)*(m1_y-o4_y2))
				# 4th orientation: Second mouse
				m2_o4_1 = np.sqrt((m2_x-o4_x1)*(m2_x-o4_x1) + (m2_y-o4_y1)*(m2_y-o4_y1))
				m2_o4_2 = np.sqrt((m2_x-o4_x2)*(m2_x-o4_x2) + (m2_y-o4_y2)*(m2_y-o4_y2))
				# 4th orientation assessment: sum
				o4_sum  = min([m1_o4_1,m1_o4_2]) + min([m2_o4_1,m2_o4_2])

				min_distance = np.zeros(4)
				min_distance[0] = o1_sum
				min_distance[1] = o2_sum
				min_distance[2] = o3_sum
				min_distance[3] = o4_sum
				
				min_ori =  np.argmin(min_distance)

				# update coordinate for each mouse Note : no overlap prevention
				self.updateCoordinate_mergeSingle([orientations[min_ori][2],orientations[min_ori][3]])
				neighbour.updateCoordinate_mergeSingle([orientations[min_ori][2],orientations[min_ori][3]])
				# initialize orientation
				o_angleX = orientations[min_ori][0][0] - orientations[min_ori][1][0]
				o_angleY = orientations[min_ori][0][1] - orientations[min_ori][1][1] 
				self.mergeOrientation      = normalizeAngle(math.atan2(o_angleY,o_angleX))
				neighbour.mergeOrientation = normalizeAngle(math.atan2(o_angleY,o_angleX))

				return [orientations[min_ori][2],orientations[min_ori][3]]

			# if orientation has been recorded 
			else: 
				o1_angleX = new_orient1[0][0] - new_orient1[1][0]
				o1_angleY = new_orient1[0][1] - new_orient1[1][1]
				o2_angleX = new_orient2[0][0] - new_orient2[1][0]
				o2_angleY = new_orient2[0][1] - new_orient2[1][1]
				o3_angleX = new_orient3[0][0] - new_orient3[1][0]
				o3_angleY = new_orient3[0][1] - new_orient3[1][1]
				o4_angleX = new_orient4[0][0] - new_orient4[1][0]
				o4_angleY = new_orient4[0][1] - new_orient4[1][1]

				first_orient  = normalizeAngle(math.atan2(o1_angleY,o1_angleX))
				second_orient = normalizeAngle(math.atan2(o2_angleY,o2_angleX))
				third_orient  = normalizeAngle(math.atan2(o3_angleY,o3_angleX))
				fourth_orient = normalizeAngle(math.atan2(o4_angleY,o4_angleX))
				first_orient_diff  = self.mergeOrientation-first_orient
				second_orient_diff = self.mergeOrientation-second_orient
				third_orient_diff  = self.mergeOrientation-third_orient
				fourth_orient_diff = self.mergeOrientation-fourth_orient

				orientation_angles = list()
				orientation_angles.append(first_orient )
				orientation_angles.append(second_orient)
				orientation_angles.append(third_orient )
				orientation_angles.append(fourth_orient)

				min_angle = np.zeros(4)
				min_angle[0] = first_orient_diff 
				min_angle[1] = second_orient_diff 
				min_angle[2] = third_orient_diff 
				min_angle[3] = fourth_orient_diff 

				min_ang =  np.argmin(min_angle)

				 
				self.updateCoordinate_mergeSingle([orientations[min_ang][2],orientations[min_ang][3]])
				neighbour.updateCoordinate_mergeSingle([orientations[min_ang][2],orientations[min_ang][3]])
				self.mergeOrientation 	   = orientation_angles[min_ang]
				neighbour.mergeOrientation = orientation_angles[min_ang]


				return [orientations[min_ang][2],orientations[min_ang][3]]
		except Exception as e:
			pass
		return list()

	# Purpose: for merge cast update
	# Description: this method will choose the distance thats the shortest
	#			   from previous coordinate for identity tracking.
	#			   Here we assume that the camera rate is much faster than mice moving
	# Note: private method, will only be used by above method 
	# input: list of (x,y)
	def updateCoordinate_mergeSingle(self, new_coordinate):
		if(len(new_coordinate) == 0):
			return False
		dist_diff = np.zeros(len(new_coordinate))# list of distance
		for index in range(0,len(new_coordinate)):
			x1 = self.previous_coordinate[0]
			y1 = self.previous_coordinate[1]
			x2 = new_coordinate[index][0]
			y2 = new_coordinate[index][1]
			abs_distance = np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
			dist_diff[index] = abs_distance
		self.previous_coordinate  = self.current_coordinate;
		index_min = np.argmin(dist_diff)
		self.current_coordinate = new_coordinate[index_min]

	def getCurrentCoordinate(self):
		# if (self.tracker_lost == True):
		# 	print(self.current_coordinate)
		return (self.tracker_lost,self.current_coordinate)


# normalize to 0 - 180
def normalizeAngle(angle):
	if angle<0 :
		return (angle + math.pi)
	else:
		return angle


# mainly used to prevent coordinate overlap
class MouseCage: 

	def __init__(self,member_list):
		self.member_list = member_list # list of mice. Note: does not auto-update, this is not reference
		self.total_member = len(member_list)
		self.num_lost_tracker = 0
		self.rfid_exist_list = list() # keep track of all rfids we have

		
	# Purpose: Sometimes mice go out of camera scope or simply lost. 
	#		   Loss of track will cause identity stack -- 2 or more identity on 
	#		   a single mouse. This method is to prevent the situation from happening
	# Precondition: member_list should be updated by new_coordinate already
	# Note: be careful to determine frequency of this method in main loop(not really we have only 3 mice = 9 iter)
	# @Parameter: member_list --> newest member list
	#			  new_coordinate --> list of newest coordinate
	# @Return:
	def sanitizeCageMemberIdentities(self,member_list,new_coordinate):
		if(new_coordinate is None):
			for tracker in member_list:
				tracker.tracker_lost = True
				self.num_lost_tracker += 1
		elif ( len(new_coordinate) == 0  ): # None of mice are in scope lel
			for tracker in member_list:
				tracker.tracker_lost = True
				self.num_lost_tracker += 1
		else: # regular check
			# we track mice using the old way: closer coordinate wins
			for tracker in member_list:
				for other_tracker in member_list:
					# pass on self
					if(tracker.tracker_ID == other_tracker.tracker_ID):
						continue
					# we have overlap
					elif(tracker.current_coordinate == other_tracker.current_coordinate):
						# print("tracker %d to other %d" % (tracker.tracker_ID,other_tracker.tracker_ID))
						# print(tracker.current_coordinate,other_tracker.current_coordinate)
						xc = tracker.current_coordinate[0]
						yc = tracker.current_coordinate[1]
						x1 = tracker.previous_coordinate[0]
						y1 = tracker.previous_coordinate[1]
						x2 = other_tracker.previous_coordinate[0]
						y2 = other_tracker.previous_coordinate[1]
						abs_distance_1 = np.sqrt((x1-xc)*(x1-xc) + (y1-yc)*(y1-yc))
						abs_distance_2 = np.sqrt((x2-xc)*(x2-xc) + (y2-yc)*(y2-yc))
						if abs_distance_1 < abs_distance_2: # tracker is closer than other_tracker
							other_tracker.tracker_lost = True
							self.num_lost_tracker += 1
						else:
							tracker.tracker_lost = True
							self.num_lost_tracker += 1


		if(new_coordinate is None):	
			for tracker in member_list:
				if (tracker.tracker_lost == True):
					tracker.current_coordinate = tracker.previous_coordinate				
		# this case we have out of scope loss: (this part is not vigorous hope wierd case does not happen often)
		# wierd case: one mouse lost and two others overlapped 
		elif(len(new_coordinate)<len(member_list)):
			# their coord will stay where they are lost. 
			# Observation tells when mice are out of scope they dont move far(usually), 
			# from where they are lost
			# print("out of scope!") # three merge will also arrive here
			for tracker in member_list:
				if (tracker.tracker_lost == True):
					
					tracker.current_coordinate = tracker.previous_coordinate
		# this is identity overlap without out of scope loss (also for random restoration):
		else:
			# print("check overlap!")
			# randomly assign if more than 2 are lost
			# reassigned tracking: tracker lost flag down
			for tracker in member_list:
				if(tracker.tracker_lost == False):
					try:# TODO: need to handle for three mice
						new_coordinate.remove(tracker.current_coordinate)
					except Exception as e:
						print("Cannot remove: ",tracker.current_coordinate, "From: ", new_coordinate)
						pass
			for tracker in member_list:
				if(tracker.tracker_lost == True):
					tracker.updateCoordinate_single(new_coordinate)
					new_coordinate.remove(tracker.getCurrentCoordinate()[1])# randomnize restart
					tracker.tracker_lost= False
		self.num_lost_tracker = 0

	
	# Purpose: To deal with situation where seperation between single case and merge(two) case 
	#		   is needed. This method returns the ONE tracker number of the tracker that holds
	#		   a single mouse in current contour(ie which tracker does this contour belong to)
	# Precondition: 1. This method should only be called with in single mouse contour loop. 
	#				   ie. it only looks at one contour. 
	#				2. This method should be called after coordinates are updated(even they might be wrong)
	# Postcondition: 1. all other single tracker which are not correct will be reverted to previous coord
	#				*2. there will be a black box drawn on tracker's area(to be done outside method)
	def sanitizeSingleMouse(self,member_list):
		# print("in sanitize single!")
		dist_diff = np.zeros(len(member_list)) # list to store distances difference between current and prev
		for index in range(0,len(member_list)):
			tracker = member_list[index]
			x_curr = tracker.current_coordinate[0]
			y_curr = tracker.current_coordinate[1]
			x_prev = tracker.previous_coordinate[0]
			y_prev = tracker.previous_coordinate[1]
			distance = np.sqrt((x_curr-x_prev)*(x_curr-x_prev) + (y_curr-y_prev)*(y_curr-y_prev))
			dist_diff[index] = distance
		tracker_id =  np.argmin(dist_diff)
		# unreal track should not be recorded:(case where someone is lost we need correct prev coord)
		for index in range(0,len(member_list)):
			if index != tracker_id:
				member_list[index].current_coordinate = member_list[index].previous_coordinate
		return tracker_id

	# Purpose: Synchronize rfid reading with computer vision tracking
	# Note: here we assume that rfid is always right so that we will take the closer 
	#		mouse to be the one that is corresponded to rfid
	# Precondition: need to make sure tag read and camera are in good sync
	# input: rfid_coord  -> rfid coordinate in camera coordinate system: (x,y)
	#		 member_list -> list of the mice in cage
	def synchronizeWithRFID(self,rfid_coord,rfid,member_list):

		# check if rfid is in list, if not add to it
		if rfid not in self.rfid_exist_list:
			self.rfid_exist_list.append(rfid)
		# also check if rfid is more than number of mice: its a problem if less it is not 
		if len(self.rfid_exist_list) > len(member_list):
			print("[ERROR] more rfid are detected than number of mice, please check mice number or rfid file")
		if rfid == None or rfid_coord == None:
			return False
		dist_diff = np.zeros(len(member_list)) # list to store distances difference between current and prev
		for index in range(0,len(member_list)):
			tracker = member_list[index]
			x_curr = tracker.current_coordinate[0]
			y_curr = tracker.current_coordinate[1]
			x_rfid = rfid_coord[0]
			y_rfid = rfid_coord[1]
			distance = np.sqrt((x_curr-x_rfid)*(x_curr-x_rfid) + (y_curr-y_rfid)*(y_curr-y_rfid))
			dist_diff[index] = distance
		tracker_id =  np.argmin(dist_diff)
		#print("tracker: ", tracker_id)
		temp_dup_bk_id = member_list[tracker_id].tag_ID # temporary duplication prevention backup for rfid
		member_list[tracker_id].tag_ID = rfid
		# update timer
		member_list[tracker_id].rfid_correction_timer = time.time()

		# now we need to check if our tracker has duplicate id
		# Note: Since we assume rfid and closer time is always more correct, when duplication happens, 
		#       we will swap id with the tracker that has not been updated for the longest time
		#		
		# Jan 10

		# duplicate check
		dup_check = list()
		temp_rfid_exist_list = list(self.rfid_exist_list)
		dup_index = None # check first dup for now: this needs refinement when more mice present
		for index in range(0,len(member_list)):
			# collect all ids
			dup_check.append(member_list[index].tag_ID)
			# skip self
			if index == tracker_id:
				continue 
			# if we have duplicate redistribute rfid according to new reading
			if member_list[index].tag_ID == rfid:
				# re-distribute:
				dup_index = index
				continue
		# if we have duplicate tag_ID in members and if our rfid list is equal to memberlist in size,
		# we must have excessive rfids
		if dup_index != None:
			print("duplicate found at tracker " ,dup_index+1) 
			for index in range(0,len(dup_check)):
				if dup_check[index] in temp_rfid_exist_list:
					temp_rfid_exist_list.remove(dup_check[index])
			print("exist list is left with ",temp_rfid_exist_list)
			print("duplicate check list is ", dup_check)
			if len(temp_rfid_exist_list) > 0 :
				# we just take the first one
				member_list[dup_index].tag_ID = temp_rfid_exist_list[0]
			else:
				print("not enough rfid for distribute")
				member_list[dup_index].tag_ID = "no_id" 
			
		# if our rfid list is shorter than memberlist: two possibilities: 1. not reached yet. 2. some mice have "no tag"

		

	#TODO: sanitize RFID

# writer to output file
class FileWriter:

		def __init__(self,outFileName):
			self.outFileName = outFileName
			open(outFileName,'w+').close()

		def writeToFile(self,time,rfid,location):
			file = open(self.outFileName,'a')
			stringBuild = ''
			stringBuild += str('%.4f' % time) + ';' + '[' +str(rfid) + ']' + ';' + str(location) + '\n'
			file.write(stringBuild)
			file.close()

