# Computes the score for the test directory

import sys
import os

caffe_root = os.environ['CAFFE_ROOT']
sys.path.insert(0, caffe_root + 'python')

import caffe
import numpy as np
from collections import Counter

# feed chunks of this size into the cnn at a time to compute scores for all of them
CHUNK_SIZE = 200

# are we testing on the out-of-the-box AlexNet that outputs a 1000-d vector?
# (if we are, then the label indices will be messed up so need to account for that)
ALEXNET_1000 = False

PRETRAINED = "/root/cs231n-project/cnns/alexnet-11/snapshots/alexnet11_iter_4000.caffemodel"
MODEL_FILE = "/root/cs231n-project/cnns/alexnet-11/deploy.prototxt"
MEAN_FILE = "/root/cs231n-project/data/image_means/ilsvrc12/imagenet_mean.npy"
GROUND_TRUTH_DIR = "/root/cs231n-project/data/images/val/instagram/227"

GROUND_TRUTH_LABEL_FILE = os.path.join(GROUND_TRUTH_DIR, "caffe.txt")

# alexnet predicted index -> our label index
alexnet_labels = {
	444 : 0, # bicycle
	406 : 2, # christmasstocking
	594 : 3, # harp
	283 : 5, # persiancat
	806 : 8  # soccerball
}

K = 1 # take the top k when computing score

if ALEXNET_1000:
	K = 20
	PRETRAINED = "/root/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel"
	MODEL_FILE = "/root/caffe/models/bvlc_reference_caffenet/deploy.prototxt"
	MEAN_FILE = "/root/caffe/data/ilsvrc12/imagenet_mean.npy"


TRASH = 10 # label for trash class


label_key = {
	"bicycle" : 0,
	"broccoli" : 1,
	"christmasstocking" : 2,
	"harp" : 3,
	"paintballmarker" : 4,
	"persiancat" : 5,
	"sewingmachine" : 6,
	"skateboard" : 7,
	"soccerball" : 8,
	"tennisball" : 9
}

key_label = {}
for key in label_key:
	key_label[label_key[key]] = key

label_indices_set = set(key_label.keys())

# Returns a list of chunks of size n, made from l.
def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


caffe.set_mode_gpu()
net = caffe.Classifier(MODEL_FILE, PRETRAINED, mean=np.load(MEAN_FILE).mean(1).mean(1), channel_swap=(2, 1, 0), raw_scale=255)

# Load into memory the filename -> label mapping
def load_label_file():
	f = open(GROUND_TRUTH_LABEL_FILE, 'r')
	image_labels = {}
	for line in f:
		vals = line.strip().split()
		image_filename = vals[0]
		int_label = vals[1]
		image_labels[image_filename] = int(int_label)
	f.close()
	return image_labels

# Get the class label from the filename (e.g. bike_001.jpg --> bike)
def get_class_label(filename):
	class_name = filename.split('/')[-2]
	return label_key[class_name]

# mapping of filename -> ground truth label
image_labels = load_label_file()

# a set of all possible correct labels
gold_labels = set(image_labels.values())
gold_labels.remove(TRASH)

# chunk the filenames of all the images we want to test
image_filenames = image_labels.keys()
filename_chunks = chunks(image_filenames, CHUNK_SIZE)

# record errors by class label
# assume working with an image whose class label number is x (trash is 10)
# fp: if prediction on image is x and fiverr label is 10
# tp: if prediction on image is x and fiverr label is x
# fn: if prediction on image is 10 and fiverr label is x
# tn: if prediction on image is 10 and fiverr label is 10

fp = Counter()
fn = Counter()
tp = Counter()
tn = Counter()

c = 0
n = len(filename_chunks)

# Get the predictions for each chunk
for curr_filenames in filename_chunks[:1]:
	print "Chunk %d out of %d" % (c, n)
	c += 1

	images = [caffe.io.load_image(os.path.join(GROUND_TRUTH_DIR, name)) for name in curr_filenames]
	predictions = net.predict(images)

	for i, filename in enumerate(curr_filenames):
		curr_predictions = predictions[i]

		if ALEXNET_1000:
			assert len(curr_predictions) == 1000
		else:
			assert len(curr_predictions) == 11

		idx = [i for i in xrange(len(curr_predictions))]
		preds = zip(curr_predictions, idx) # gives list of tuples (pred, index)

		sorted_predictions = sorted(preds, reverse=True)
		top_k = sorted_predictions[:K]

		top_k_labels = set([index for (pred, index) in top_k])

		# as far as we are concerned, AlexNet will predict one of our 5 classes, or trash
		if ALEXNET_1000:
			new_labels = set()
			for label in top_k_labels:
				if label in alexnet_labels:
					new_labels.add(alexnet_labels[label])
				else:
					new_labels.add(TRASH)
			top_k_labels = new_labels

		fiverr_label = image_labels[filename]
		class_label = get_class_label(filename)

		# assume working with an image whose class label number is x (trash is 10)
		# fp: if prediction on image is x and fiverr label is 10
		# tp: if prediction on image is x and fiverr label is x
		# fn: if prediction on image is 10 or y != x and fiverr label is x
		# tn: if prediction on image is 10 and fiverr label is 10

		if class_label in top_k_labels:
			if fiverr_label == TRASH:
				fp[class_label] += 1
			else:
				# fiverr guy correctly labeled it as the class that it is
				assert fiverr_label == class_label
				tp[class_label] += 1
		elif TRASH in top_k_labels:
			if fiverr_label == class_label:
				fn[class_label] += 1
			else:
				# fiverr guy correctly labeled it as trash
				assert fiverr_label == TRASH
				tn[class_label] += 1
		else:
			fn[class_label] += 1


print "Scores: "
total_num = 0
for true_class in gold_labels:
	tp_val = tp[true_class]
	fp_val = fp[true_class]
	tn_val = tn[true_class]
	fn_val = fn[true_class]

	total = tp_val + fp_val + tn_val + fn_val
	total_num += total

	if total == 0:
		print "  True label %s -> # test points = %d" (key_label[true_class], total)
	else:
		accuracy = float(tp_val + tn_val) / (tp_val + fp_val + tn_val + fn_val)
		
		precision = -1.0
		if tp_val + fp_val > 0:
			precision = float(tp_val) / (tp_val + fp_val)
		
		recall = -1.0
		if tp_val + fn_val > 0:
			recall = float(tp_val) / (tp_val + fn_val)

		print "  True label %s -> # test points = %d, acc = %f; prec = %f; recall = %f" % \
			(key_label[true_class], total, accuracy, precision, recall)

print "Total # of test points = %d" % total_num

