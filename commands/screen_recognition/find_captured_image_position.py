import base64
import io

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand


ScreenRecognitionCategory = MacroCommandCategory(
    "screen_recognition",
    "Screen Recognition",
    "m:visibility",
)


def captured_image_to_image(value):
    if not isinstance(value, dict):
        return None

    image_base64 = str(
        value.get("image_base64", "") or ""
    ).strip()

    if not image_base64:
        return None

    try:
        from PIL import Image

        raw = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(raw))
        image.load()

        return image.convert("RGB").copy()
    except Exception:
        return None


def save_result_to_variable(
    runtime,
    variable_name,
    value,
):
    variable_name = str(
        variable_name or ""
    ).strip()

    if (
        not variable_name
        or runtime is None
        or not hasattr(runtime, "vars")
    ):
        return value

    runtime.vars.set(variable_name, value)

    return value


def normalize_screen_position(result):
    if result is None:
        return {
            "x": -1,
            "y": -1,
        }

    if isinstance(result, dict):
        x = result.get("x", -1)
        y = result.get("y", -1)

        try:
            x = int(x)
        except Exception:
            x = -1

        try:
            y = int(y)
        except Exception:
            y = -1

        return {
            "x": x,
            "y": y,
        }

    x = getattr(result, "x", None)
    y = getattr(result, "y", None)

    try:
        if x is not None and y is not None:
            return {
                "x": int(x),
                "y": int(y),
            }
    except Exception:
        pass

    try:
        if (
            isinstance(result, (list, tuple))
            and len(result) >= 2
        ):
            return {
                "x": int(result[0]),
                "y": int(result[1]),
            }
    except Exception:
        pass

    return {
        "x": -1,
        "y": -1,
    }


def normalize_match_score(value):
    try:
        value = float(value)
    except Exception:
        return 0.0

    if value != value:
        return 0.0

    return max(
        0.0,
        min(1.0, value),
    )


def get_result_match_confidence(result):
    if not isinstance(result, dict):
        return 0.0

    score = normalize_match_score(
        result.get("score", 0.0)
    )

    return round(score * 100.0, 2)


def failed_match_result(score=0.0):
    return {
        "x": -1,
        "y": -1,
        "score": normalize_match_score(score),
    }


def normalize_region(value):
    if not isinstance(value, dict):
        return None

    try:
        start_x = int(
            value.get("start_x", 0) or 0
        )
        start_y = int(
            value.get("start_y", 0) or 0
        )
        width = int(
            value.get("width", 0) or 0
        )
        height = int(
            value.get("height", 0) or 0
        )
    except Exception:
        return None

    if width <= 0 or height <= 0:
        return None

    return (
        start_x,
        start_y,
        width,
        height,
    )


def calculate_template_match_score(
    screenshot,
    target_image,
):
    try:
        import cv2
        import numpy

        screenshot_array = numpy.array(
            screenshot.convert("RGB")
        )
        target_array = numpy.array(
            target_image.convert("RGB")
        )

        screenshot_gray = cv2.cvtColor(
            screenshot_array,
            cv2.COLOR_RGB2GRAY,
        )
        target_gray = cv2.cvtColor(
            target_array,
            cv2.COLOR_RGB2GRAY,
        )

        target_height = target_gray.shape[0]
        target_width = target_gray.shape[1]
        screenshot_height = screenshot_gray.shape[0]
        screenshot_width = screenshot_gray.shape[1]

        if (
            target_width <= 0
            or target_height <= 0
            or target_width > screenshot_width
            or target_height > screenshot_height
        ):
            return 0.0

        result = cv2.matchTemplate(
            screenshot_gray,
            target_gray,
            cv2.TM_CCOEFF_NORMED,
        )

        _, maximum_value, _, _ = cv2.minMaxLoc(
            result
        )

        return normalize_match_score(
            maximum_value
        )
    except Exception:
        return 0.0


def safe_locate_standard_center_on_screen(
    target_image,
    confidence,
    region=None,
):
    try:
        import pyautogui
    except Exception:
        raise RuntimeError(
            "pyautogui is required for screen "
            "recognition commands. Install it with: "
            "pip install pyautogui"
        )

    try:
        screenshot = pyautogui.screenshot(
            region=region
        )
        screenshot = screenshot.convert("RGB").copy()
        target_image = target_image.convert("RGB").copy()

        match = pyautogui.locate(
            target_image,
            screenshot,
            confidence=confidence,
        )

        if match is None:
            score = calculate_template_match_score(
                screenshot,
                target_image,
            )
            return failed_match_result(score)

        center = pyautogui.center(match)

        local_left = int(match.left)
        local_top = int(match.top)
        local_right = int(
            match.left + match.width
        )
        local_bottom = int(
            match.top + match.height
        )

        matched_image = screenshot.crop(
            (
                local_left,
                local_top,
                local_right,
                local_bottom,
            )
        )

        score = calculate_template_match_score(
            matched_image,
            target_image,
        )

        result_x = int(center.x)
        result_y = int(center.y)
        top_left_x = local_left
        top_left_y = local_top

        if region is not None:
            result_x += int(region[0])
            result_y += int(region[1])
            top_left_x += int(region[0])
            top_left_y += int(region[1])

        return {
            "x": result_x,
            "y": result_y,
            "top_left_x": top_left_x,
            "top_left_y": top_left_y,
            "score": score,
        }
    except Exception:
        return failed_match_result()


def safe_locate_template_center_on_screen(
    target_image,
    confidence,
    region=None,
):
    try:
        import cv2
        import numpy
        import pyautogui
    except Exception:
        raise RuntimeError(
            "opencv-python, numpy and pyautogui are "
            "required for template screen "
            "recognition. Install them with: "
            "pip install opencv-python numpy pyautogui"
        )

    try:
        screenshot = pyautogui.screenshot(
            region=region
        )
        screenshot = screenshot.convert("RGB").copy()
        target_image = target_image.convert("RGB").copy()

        screenshot_array = numpy.array(
            screenshot
        )
        target_array = numpy.array(
            target_image
        )

        screenshot_gray = cv2.cvtColor(
            screenshot_array,
            cv2.COLOR_RGB2GRAY,
        )
        target_gray = cv2.cvtColor(
            target_array,
            cv2.COLOR_RGB2GRAY,
        )

        target_height = target_gray.shape[0]
        target_width = target_gray.shape[1]

        if (
            target_width <= 0
            or target_height <= 0
            or target_width > screenshot_gray.shape[1]
            or target_height > screenshot_gray.shape[0]
        ):
            return failed_match_result()

        result = cv2.matchTemplate(
            screenshot_gray,
            target_gray,
            cv2.TM_CCOEFF_NORMED,
        )

        _, maximum_value, _, maximum_location = (
            cv2.minMaxLoc(result)
        )

        score = normalize_match_score(
            maximum_value
        )

        if float(maximum_value) < float(confidence):
            return failed_match_result(score)

        top_left_x = int(
            maximum_location[0]
        )
        top_left_y = int(
            maximum_location[1]
        )

        result_x = int(
            top_left_x + (target_width / 2)
        )
        result_y = int(
            top_left_y + (target_height / 2)
        )

        if region is not None:
            result_x += int(region[0])
            result_y += int(region[1])
            top_left_x += int(region[0])
            top_left_y += int(region[1])

        return {
            "x": result_x,
            "y": result_y,
            "top_left_x": top_left_x,
            "top_left_y": top_left_y,
            "score": score,
        }
    except Exception:
        return failed_match_result()


def safe_locate_feature_center_on_screen(
    target_image,
    confidence,
    region=None,
    feature_type="sift",
):
    try:
        import cv2
        import numpy
        import pyautogui
    except Exception:
        raise RuntimeError(
            "opencv-python, numpy and pyautogui are "
            "required for scale and rotation screen "
            "recognition. Install them with: "
            "pip install opencv-python numpy pyautogui"
        )

    try:
        screenshot = pyautogui.screenshot(
            region=region
        )
        screenshot = screenshot.convert("RGB").copy()
        target_image = target_image.convert("RGB").copy()

        screenshot_array = numpy.array(
            screenshot
        )
        target_array = numpy.array(
            target_image
        )

        screenshot_gray = cv2.cvtColor(
            screenshot_array,
            cv2.COLOR_RGB2GRAY,
        )
        target_gray = cv2.cvtColor(
            target_array,
            cv2.COLOR_RGB2GRAY,
        )

        target_height = target_gray.shape[0]
        target_width = target_gray.shape[1]

        if (
            target_width <= 0
            or target_height <= 0
            or screenshot_gray.shape[0] <= 0
            or screenshot_gray.shape[1] <= 0
        ):
            return failed_match_result()

        feature_type = str(
            feature_type or "sift"
        ).strip().lower()

        if feature_type == "orb":
            detector = cv2.ORB_create(
                nfeatures=3000
            )
            norm_type = cv2.NORM_HAMMING
            ratio_threshold = 0.75
        else:
            if not hasattr(cv2, "SIFT_create"):
                raise RuntimeError(
                    "SIFT is not available in this "
                    "OpenCV build. Install a recent "
                    "opencv-python package or use ORB."
                )

            detector = cv2.SIFT_create(
                nfeatures=3000
            )
            norm_type = cv2.NORM_L2
            ratio_threshold = 0.75

        target_keypoints, target_descriptors = (
            detector.detectAndCompute(
                target_gray,
                None,
            )
        )
        screen_keypoints, screen_descriptors = (
            detector.detectAndCompute(
                screenshot_gray,
                None,
            )
        )

        if (
            target_descriptors is None
            or screen_descriptors is None
            or len(target_keypoints) < 4
            or len(screen_keypoints) < 4
        ):
            return failed_match_result()

        matcher = cv2.BFMatcher(
            norm_type,
            crossCheck=False,
        )

        raw_matches = matcher.knnMatch(
            target_descriptors,
            screen_descriptors,
            k=2,
        )

        good_matches = []

        for match_pair in raw_matches:
            if len(match_pair) < 2:
                continue

            first_match, second_match = match_pair

            if (
                first_match.distance
                < ratio_threshold
                * second_match.distance
            ):
                good_matches.append(first_match)

        min_good_matches = max(
            8,
            int(8 + (float(confidence) * 16)),
        )

        if len(good_matches) < min_good_matches:
            return failed_match_result()

        source_points = numpy.float32(
            [
                target_keypoints[match.queryIdx].pt
                for match in good_matches
            ]
        ).reshape(-1, 1, 2)

        destination_points = numpy.float32(
            [
                screen_keypoints[match.trainIdx].pt
                for match in good_matches
            ]
        ).reshape(-1, 1, 2)

        homography, mask = cv2.findHomography(
            source_points,
            destination_points,
            cv2.RANSAC,
            5.0,
        )

        if homography is None or mask is None:
            return failed_match_result()

        inlier_count = int(
            mask.ravel().sum()
        )
        inlier_ratio = float(
            inlier_count
        ) / float(
            max(1, len(good_matches))
        )
        score = normalize_match_score(
            inlier_ratio
        )

        min_inliers = max(
            6,
            int(min_good_matches * 0.6),
        )

        if (
            inlier_count < min_inliers
            or inlier_ratio
            < max(
                0.15,
                float(confidence) * 0.35,
            )
        ):
            return failed_match_result(score)

        target_corners = numpy.float32(
            [
                [0, 0],
                [target_width, 0],
                [target_width, target_height],
                [0, target_height],
            ]
        ).reshape(-1, 1, 2)

        transformed_corners = cv2.perspectiveTransform(
            target_corners,
            homography,
        )

        corner_points = transformed_corners.reshape(
            4,
            2,
        )

        min_x = float(
            numpy.min(corner_points[:, 0])
        )
        min_y = float(
            numpy.min(corner_points[:, 1])
        )
        max_x = float(
            numpy.max(corner_points[:, 0])
        )
        max_y = float(
            numpy.max(corner_points[:, 1])
        )

        if (
            max_x < 0
            or max_y < 0
            or min_x > screenshot_gray.shape[1]
            or min_y > screenshot_gray.shape[0]
        ):
            return failed_match_result(score)

        result_x = int(
            (min_x + max_x) / 2
        )
        result_y = int(
            (min_y + max_y) / 2
        )
        top_left_x = int(min_x)
        top_left_y = int(min_y)

        if region is not None:
            result_x += int(region[0])
            result_y += int(region[1])
            top_left_x += int(region[0])
            top_left_y += int(region[1])

        return {
            "x": result_x,
            "y": result_y,
            "top_left_x": top_left_x,
            "top_left_y": top_left_y,
            "score": score,
            "matches": len(good_matches),
            "inliers": inlier_count,
        }
    except Exception:
        return failed_match_result()


def safe_locate_center_on_screen(
    target_image,
    confidence,
    region=None,
    detection_method="standard",
):
    detection_method = str(
        detection_method or "standard"
    ).strip().lower()

    if detection_method == "template":
        return safe_locate_template_center_on_screen(
            target_image,
            confidence,
            region=region,
        )

    if detection_method == "orb":
        return safe_locate_feature_center_on_screen(
            target_image,
            confidence,
            region=region,
            feature_type="orb",
        )

    if detection_method == "sift":
        return safe_locate_feature_center_on_screen(
            target_image,
            confidence,
            region=region,
            feature_type="sift",
        )

    return safe_locate_standard_center_on_screen(
        target_image,
        confidence,
        region=region,
    )


def convert_result_position(
    result,
    image_value,
    position_type,
):
    normalized = normalize_screen_position(result)
    match_confidence = get_result_match_confidence(
        result
    )

    if (
        normalized["x"] < 0
        or normalized["y"] < 0
    ):
        return {
            "x": -1,
            "y": -1,
            "confidence": match_confidence,
        }

    if (
        str(
            position_type or "center"
        ).strip().lower()
        != "top_left"
    ):
        return {
            "x": normalized["x"],
            "y": normalized["y"],
            "confidence": match_confidence,
        }

    if isinstance(result, dict):
        try:
            top_left_x = result.get(
                "top_left_x"
            )
            top_left_y = result.get(
                "top_left_y"
            )

            if (
                top_left_x is not None
                and top_left_y is not None
            ):
                return {
                    "x": int(top_left_x),
                    "y": int(top_left_y),
                    "confidence": match_confidence,
                }
        except Exception:
            pass

    width = 0
    height = 0

    if isinstance(image_value, dict):
        try:
            width = int(
                image_value.get("width", 0) or 0
            )
            height = int(
                image_value.get("height", 0) or 0
            )
        except Exception:
            width = 0
            height = 0

    return {
        "x": int(
            normalized["x"] - (width / 2)
        ),
        "y": int(
            normalized["y"] - (height / 2)
        ),
        "confidence": match_confidence,
    }


def normalize_float(
    value,
    default_value,
    minimum,
    maximum,
):
    try:
        value = float(value)
    except Exception:
        value = float(default_value)

    return max(
        float(minimum),
        min(float(maximum), value),
    )


class FindCapturedImagePositionCommand(
    MacroCommand
):
    id = (
        "screen_recognition."
        "find_captured_image_position"
    )
    title = "Find Captured Image Position"
    category = ScreenRecognitionCategory
    icon = "mc:e43f"
    description = (
        "Find a captured image on screen and "
        "return its position and match confidence."
    )
    fields = [
        {
            "name": "image",
            "title": "Captured Image",
            "value_type": "captured_image",
            "default_value": {
                "image_base64": "",
                "width": 0,
                "height": 0,
            },
        },
        {
            "name": "position_type",
            "title": "Return Position",
            "value_type": "choice",
            "default_value": "center",
            "options": [
                {
                    "value": "center",
                    "title": "Center",
                },
                {
                    "value": "top_left",
                    "title": "Top Left",
                },
            ],
        },
        {
            "name": "detection_method",
            "title": "Detection Method",
            "value_type": "choice",
            "default_value": "standard",
            "options": [
                {
                    "value": "standard",
                    "title": "Standard Match",
                },
                {
                    "value": "template",
                    "title": "Template Match",
                },
                {
                    "value": "orb",
                    "title": "Fast Scale & Rotation Match (Advanced/Experimental)",
                },
                {
                    "value": "sift",
                    "title": "Accurate Scale & Rotation Match (Advanced/Experimental)",
                },
            ],
        },
        {
            "name": "search_area_type",
            "title": "Search Area",
            "value_type": "choice",
            "default_value": "full_screen",
            "options": [
                {
                    "value": "full_screen",
                    "title": "Full Screen",
                },
                {
                    "value": "region",
                    "title": "Region",
                },
            ],
        },
        {
            "name": "search_region",
            "title": "Search Region",
            "value_type": "region",
            "default_value": {
                "image_base64": "",
                "start_x": 0,
                "start_y": 0,
                "end_x": 0,
                "end_y": 0,
                "width": 0,
                "height": 0,
            },
            "visible_if": {
                "field": "search_area_type",
                "operator": "==",
                "equals": "region",
            },
        },
        {
            "name": "confidence",
            "title": "Minimum Confidence",
            "place_holder": "80%",
            "value_type": "float",
            "default_value": 80,
            "min_value": 0,
            "max_value": 100,
            "decimals": 2,
        },
        {
            "name": "save_to_variable",
            "title": "Save To Variable",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        image = values.get("image") or {}

        if isinstance(image, dict):
            width = int(
                image.get("width", 0) or 0
            )
            height = int(
                image.get("height", 0) or 0
            )
        else:
            width = 0
            height = 0

        detection_method = str(
            values.get(
                "detection_method",
                "standard",
            )
            or "standard"
        ).strip().lower()

        detection_titles = {
            "standard": "standard",
            "template": "template",
            "orb": "fast scale/rotation",
            "sift": "accurate scale/rotation",
        }

        detection_title = detection_titles.get(
            detection_method,
            "standard",
        )

        return (
            "find captured image: "
            f"{width}x{height}, {detection_title}"
        )

    def execute(
        self,
        values=None,
        runtime=None,
    ):
        values = self.normalize_values(values)

        image_value = values.get("image") or {}

        position_type = str(
            values.get(
                "position_type",
                "center",
            )
            or "center"
        ).strip().lower()

        detection_method = str(
            values.get(
                "detection_method",
                "standard",
            )
            or "standard"
        ).strip().lower()

        search_area_type = str(
            values.get(
                "search_area_type",
                "full_screen",
            )
            or "full_screen"
        ).strip().lower()

        confidence = normalize_float(
            values.get("confidence", 80),
            80,
            0,
            100,
        ) / 100.0

        if detection_method not in {
            "standard",
            "template",
            "orb",
            "sift",
        }:
            detection_method = "standard"

        target_image = captured_image_to_image(
            image_value
        )

        if target_image is None:
            result = {
                "x": -1,
                "y": -1,
                "confidence": 0.0,
            }

            return save_result_to_variable(
                runtime,
                values.get("save_to_variable"),
                result,
            )

        search_region = None

        if search_area_type == "region":
            search_region = normalize_region(
                values.get("search_region") or {}
            )

        result = safe_locate_center_on_screen(
            target_image,
            confidence,
            region=search_region,
            detection_method=detection_method,
        )

        result = convert_result_position(
            result,
            image_value,
            position_type,
        )

        return save_result_to_variable(
            runtime,
            values.get("save_to_variable"),
            result,
        )


def register_macro(registry):
    registry.register(
        FindCapturedImagePositionCommand
    )
