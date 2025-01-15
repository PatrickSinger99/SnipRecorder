import cv2


def resize_image(img_array, max_width, max_height):
    """
    Resizes an image to fit within the maximum width and height while preserving its aspect ratio.

    :param img_array: The input image as a NumPy array.
    :param max_width: The maximum allowed width for the resized image.
    :param max_height: The maximum allowed height for the resized image.
    :return: The resized image as a NumPy array.
    """
    # Get the original dimensions of the image
    original_height, original_width = img_array.shape[:2]

    # Calculate the scaling factors for width and height
    width_scale = max_width / original_width
    height_scale = max_height / original_height

    # Use the smaller scale to maintain aspect ratio
    scale = min(width_scale, height_scale)

    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # Resize the image using OpenCV
    resized_image = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return resized_image
