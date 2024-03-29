import cv2
import numpy as np
import collections

def region_of_interest(img, vertices):
    """
    Applies an image mask.

    Only keeps the region of the image defined by the polygon
    formed from `vertices`. The rest of the image is set to black.
    """
    #defining a blank mask to start with
    mask = np.zeros_like(img)

    #defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255

    #filling pixels inside the polygon defined by "vertices" with the fill color    
    cv2.fillPoly(mask, vertices, ignore_mask_color)

    #returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

l_slope_history = collections.deque(maxlen=5)
r_slope_history = collections.deque(maxlen=5)
slope_history = collections.deque(maxlen=5)

def low_pass_filter(measurement):
    d.append(measurement)
    return d.median()

def draw_lines(img, lines): #, color=[255, 0, 0], thickness=6):
    """workflow:
    1) examine each individual line returned by hough & determine if it's in left or right lane by its slope
    because we are working "upside down" with the array, the left lane will have a negative slope and right positive
    2) track extrema
    3) compute averages
    4) solve for b intercept
    5) use extrema to solve for points
    6) smooth frames and cache
    """
    global cache
    global first_frame
    y_global_min = img.shape[0] #min will be the "highest" y value, or point down the road away from car
    y_max = img.shape[0]
    l_slope, r_slope = [],[]
    l_lane,r_lane = [],[]
    det_slope = 0.4
    alpha = 0.9

    if lines is None:
        return 1

    for line in lines:
        #1
        for x1,y1,x2,y2 in line:
            if x2-x1 != 0:
                slope = (y2-y1)/(x2-x1)
            else:
                slope = (y2-y1)
            if slope > det_slope:
                r_slope.append(slope)
                r_lane.append(line)
            elif slope < -det_slope:
                l_slope.append(slope)
                l_lane.append(line)
        #2
        y_global_min = min(y1,y2,y_global_min)

    # to prevent errors in challenge video from dividing by zero
    if((len(l_lane) == 0) or (len(r_lane) == 0)):
        print ('no lane detected')
        return 1

    #3
    l_slope_mean = np.median(l_slope,axis =0)
    r_slope_mean = np.median(r_slope,axis =0)
    slope_mean = (l_slope_mean + r_slope_mean) / 2
    l_slope_history.append(l_slope_mean)
    r_slope_history.append(r_slope_mean)
    slope_history.append(slope_mean)
    l_slope_mean = np.median(l_slope_history)
    r_slope_mean = np.median(r_slope_history)
    slope_mean = np.median(slope_history)
    slope_angle = np.arctan(slope_mean) * 180 / np.pi
    print(slope_angle)
    l_mean = np.median(np.array(l_lane),axis=0)
    r_mean = np.median(np.array(r_lane),axis=0)

    if ((r_slope_mean == 0) or (l_slope_mean == 0 )):
        print('dividing by zero')
        return 1



    #4, y=mx+b -> b = y -mx
    l_b = l_mean[0][1] - (l_slope_mean * l_mean[0][0])
    r_b = r_mean[0][1] - (r_slope_mean * r_mean[0][0])

    #5, using y-extrema (#2), b intercept (#4), and slope (#3) solve for x using y=mx+b
    # x = (y-b)/m
    # these 4 points are our two lines that we will pass to the draw function
    l_x1 = int((y_global_min - l_b)/l_slope_mean)
    l_x2 = int((y_max - l_b)/l_slope_mean)
    r_x1 = int((y_global_min - r_b)/r_slope_mean)
    r_x2 = int((y_max - r_b)/r_slope_mean)

    #6
    if l_x1 > r_x1:
        l_x1 = int((l_x1+r_x1)/2)
        r_x1 = l_x1
        l_y1 = int((l_slope_mean * l_x1 ) + l_b)
        r_y1 = int((r_slope_mean * r_x1 ) + r_b)
        l_y2 = int((l_slope_mean * l_x2 ) + l_b)
        r_y2 = int((r_slope_mean * r_x2 ) + r_b)
    else:
        l_y1 = y_global_min
        l_y2 = y_max
        r_y1 = y_global_min
        r_y2 = y_max

    current_frame = np.array([l_x1,l_y1,l_x2,l_y2,r_x1,r_y1,r_x2,r_y2],dtype ="float32")

    if first_frame == 1:
        next_frame = current_frame
        first_frame = 0
    else:
        prev_frame = cache
        next_frame = (1-alpha)*prev_frame+alpha*current_frame

    cv2.line(img, (int(next_frame[0]), int(next_frame[1])), (int(next_frame[2]),int(next_frame[3])), [0,0,255], 5)
    cv2.line(img, (int(next_frame[4]), int(next_frame[5])), (int(next_frame[6]),int(next_frame[7])), [0,0,255], 5)
    cv2.line(img, (int((next_frame[0]+next_frame[4])/2), int((next_frame[1]+next_frame[5])/2)), (int((next_frame[2]+next_frame[6])/2), int((next_frame[0]+next_frame[4])/2)), [0,255,0], 3) # Create a line down the middle of the lane.

    cache = next_frame

def nothing(x):
	pass

#cv2.namedWindow('Lanes', cv2.WINDOW_NORMAL)

def detectLanes(augmented):
	global first_frame
	first_frame = 1

	gray = cv2.cvtColor(augmented, cv2.COLOR_BGR2GRAY)
	img_hsv = cv2.cvtColor(augmented, cv2.COLOR_RGB2HSV)

	lower_yellow = np.array([30, 0, 140], dtype = "uint8")
	upper_yellow = np.array([255, 255, 255], dtype = "uint8")

	mask_yellow = cv2.inRange(img_hsv, lower_yellow, upper_yellow)
	mask_white = cv2.inRange(gray, 200, 255)
	mask_yw = cv2.bitwise_or(mask_white, mask_yellow)
	mask_yw_image = cv2.bitwise_and(gray, mask_yw)

	kernel_size = 5
	gauss_gray = cv2.GaussianBlur(mask_yw_image, (kernel_size, kernel_size), 0)

	low_threshold = 50
	high_threshold = 150
	canny_edges = cv2.Canny(gauss_gray, low_threshold, high_threshold)

	imshape = augmented.shape
	lower_left = [imshape[1]/9,imshape[0]]
	lower_right = [imshape[1]-imshape[1]/9,imshape[0]]
	top_left = [imshape[1]/2-imshape[1]/8,imshape[0]/2+imshape[0]/10]
	top_right = [imshape[1]/2+imshape[1]/8,imshape[0]/2+imshape[0]/10]
	vertices = [np.array([lower_left,top_left,top_right,lower_right],dtype=np.int32)]
	roi_image = region_of_interest(canny_edges, vertices)

	rho = 4
	theta = np.pi/180
	threshold = 30
	min_line_len = 100
	max_line_gap = 180

	lines = cv2.HoughLinesP(roi_image, rho, theta, threshold, np.array([]), min_line_len, max_line_gap)
	line_img = np.zeros((roi_image.shape[0], roi_image.shape[1], 3), dtype=np.uint8)
	draw_lines(line_img, lines)

	augmented = cv2.addWeighted(line_img, 0.8, augmented, 1., 0.)
	#cv2.imshow("Lanes", augmented)
	
	return augmented
