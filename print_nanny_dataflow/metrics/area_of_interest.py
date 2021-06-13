from typing import Iterable, Tuple, Optional
import numpy as np

from print_nanny_client.protobuf.monitoring_pb2 import DeviceCalibration, BoxAnnotations
from print_nanny_dataflow.coders.types import CATEGORY_INDEX


def calc_percent_intersection(
    detection_boxes: Iterable[BoxAnnotations],
    aoi_coords: Tuple[float, float, float, float],
) -> Iterable:
    """
    Returns intersection-over-union area, normalized between 0 and 1
    """
    # initialize array of zeroes
    aou = np.zeros(len(detection_boxes))

    # for each bounding box, calculate the intersection-over-area
    for i, box in enumerate(detection_boxes):
        # determine the coordinates of the intersection rectangle
        x_left = max(aoi_coords[0], box[0])
        y_top = max(aoi_coords[1], box[1])
        x_right = min(aoi_coords[2], box[2])
        y_bottom = min(aoi_coords[3], box[3])

        # boxes do not intersect, area is 0
        if x_right < x_left or y_bottom < y_top:
            aou[i] = 0.0
            continue

        # calculate
        # The intersection of two axis-aligned bounding boxes is always an
        # axis-aligned bounding box
        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # compute the area of detection box
        box_area = (box[2] - box[0]) * (box[3] - box[1])

        if (intersection_area / box_area) == 1.0:
            aou[i] = 1.0
            continue

        aou[i] = intersection_area / box_area

    return aou


def filter_box_annotations(
    element: BoxAnnotations,
    calibration: Optional[DeviceCalibration] = None,
    min_calibration_area_overlap=0.75,
    min_score_threshold=0.66,
) -> BoxAnnotations:

    detection_scores = np.array(element.detection_scores)

    if calibration:
        percent_intersection = calc_percent_intersection(
            element.detection_boxes, calibration.coordinates
        )
        ignored_mask = (
            percent_intersection
            < min_calibration_area_overlap & detection_scores
            > min_score_threshold
        )
    else:
        ignored_mask = detection_scores > min_score_threshold

    detection_boxes = np.array(element.detection_boxes)
    detection_classes = np.array(element.detection_classes)
    filtered_detection_boxes = detection_boxes[ignored_mask]

    filtered_detection_scores = detection_scores[ignored_mask]
    filtered_detection_classes = detection_classes[ignored_mask]

    num_detections = int(np.count_nonzero(ignored_mask))

    annotations = BoxAnnotations(
        num_detections=num_detections,
        detection_scores=filtered_detection_scores,
        detection_boxes=filtered_detection_boxes,
        detection_classes=filtered_detection_classes,
        health_weights=[
            CATEGORY_INDEX[i]["health_weight"] for i in filtered_detection_classes
        ],
    )
    return annotations
