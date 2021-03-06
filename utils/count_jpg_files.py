import os

# Counts the number of jpg image files in a given train or val directory

# paths relative to the directory where this script lives
DIRS = [
	"../data/images/train/no_augmentations/imagenet/256",
	"../data/images/val/instagram/227",
	"../data/images/train/no_augmentations/instagram_imagenet",
	"../data/images/train/all_augmentations/instagram_imagenet",
	"../data/images/train/all_augmentations/imagenet/256",
	"../data/images/train/tint_contrast_only/instagram_imagenet",
	"../data/images/train/tint_contrast_only/imagenet/256"
]

# Returns a list of full directory paths in current directory.
def get_dirs_in_curr(curr_dir):
	return [os.path.join(curr_dir, name) for name in os.listdir(curr_dir) if os.path.isdir(os.path.join(curr_dir, name))]

# Returns a list of image filenames (with full path) in the directory dir_path.
def get_image_filenames(dir_path):
	return [os.path.join(dir_path, o) for o in os.listdir(dir_path) if o.lower().endswith(".jpeg") or o.lower().endswith(".jpg")]

for DIR in DIRS:
	directory = os.path.join(os.getcwd(), DIR)
	count = 0
	dirs = get_dirs_in_curr(directory)
	for directory in dirs:
		image_filenames = get_image_filenames(directory)
		count += len(image_filenames)
	print "%s: number of JPG files = %d" % (DIR, count)
		