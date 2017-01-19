#!/usr/bin/env python

import time, threading
from os.path import expanduser
# Import the RAPP Robot API
from rapp_robot_api import RappRobot

# Import the QR detection module
from RappCloud.CloudMsgs import HumanDetection
from RappCloud import RappPlatformService

# Create an object in order to call the desired functions
rh = RappRobot()
# Instantiate a new HumanDetection service.
msg = HumanDetection()

svc = RappPlatformService()

# Enable the NAO motors for the head to move
rh.motion.enableMotors()

def callback():
    print "Callback called!"
    # Capture an image from the NAO cameras
    rh.vision.capturePhoto("/home/nao/human.jpg", "front", "640x480")
    # Get the photo to the PC
    rh.utilities.moveFileToPC("/home/nao/human.jpg", expanduser("~") + "/Pictures/human.jpg")
    # Check if a human exists
    msg.req.imageFilepath = expanduser("~") + "/Pictures/human.jpg"
    res = svc.call(msg)
    print "Call to platform finished"

    if len(res.humans) == 0: # No humans were detected
        print "No humans codes were detected"
    elif len(res.humans) == 1: # One human detected
        print "One human detected"
        up_left_point = res.humans[0]['up_left_point']
        down_right_point = res.humans[0]['down_right_point']

        # compute the center of the human
        human_center_x = (up_left_point['x'] + (down_right_point['x']-up_left_point['x'])/2)
        human_center_y = (up_left_point['y'] + (down_right_point['y']-up_left_point['y'])/2)
        
        # Directions are computed bounded in [-1,1]
        dir_x = (human_center_x - (640.0/2.0)) / (640.0 / 2.0)
        dir_y = (human_center_y - (480.0/2.0)) / (480.0 / 2.0)
        angle_x = -dir_x * 30.0 / 180.0 * 3.1415
        angle_y = dir_y * 23.7 / 180.0 * 3.1415

        # Get NAO head angles
        [ans, err] = rh.humanoid_motion.getJointAngles(["HeadYaw", "HeadPitch"]) 

        # Set NAO angles according to the human center
        rh.humanoid_motion.setJointAngles(["HeadYaw", "HeadPitch"], \
                [angle_x + ans[0], angle_y + ans[1]], 0.1)

        if callback.human_found == False:
            rh.audio.speak("Hello human")
            if rh.humanoid_motion.getPosture() != "Stand":
                rh.audio.speak("Wait for me to stand up first.")
                rh.humanoid_motion.goToPosture("Stand", 0.75)
            rh.audio.speak("Lead the way and I will follow you")
            callback.human_found = True

        rh.motion.moveTo(0.4, 0, angle_x + ans[0])
        # Capture an image from the NAO cameras
        rh.vision.capturePhoto("/home/nao/human.jpg", "front", "640x480")
        # Get the photo to the PC
        rh.utilities.moveFileToPC("/home/nao/human.jpg", expanduser("~") + "/Pictures/human.jpg")
    
    elif len(res.humans) > 1: # More than one humans detected
        print "More than one humans were detected."
        rh.audio.speak("I see more than one humans I cannot follow you all.")
    threading.Timer(0, callback).start()


callback.human_found = False
callback()
