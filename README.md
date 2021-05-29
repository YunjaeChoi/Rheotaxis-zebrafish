# zebrafish  

Zebrafish detection and tracking from video for zebrafish rheotaxis.

Consists:
  1. library for zebrafish detection and tracking (`zebrafish`)
  2. interactive app (`zebrafish_on_jupyter`)

Interactive app runs on top of [nteract](https://github.com/nteract/nteract)

## Installation

Full installation (requires `pip`):

  1. Install `zebrafish` library:

  ```
  pip install -e .
  ```

  1. Install `zebrafish_on_jupyter` for interactive app:

  ```
  cd jupyter-extension-zebrafish/
  pip install -e .
  jupyter serverextension enable --py zebrafish_on_jupyter --sys-prefix
  ```

## Usage

- Run(in folder containing app_notebook.ipynb):

```
jupyter zebrafish.
```

User interface will pop up using a browser. (If not, copy and paste the notebook URL from the terminal.)

  ![Front](doc/image/front.png?raw=true)

- Before running `Detection` or `Postprocess` tab, Initialize by clicking `Initialize` button. INFO will be printed below if initialized without errors.

  ![Initialize](doc/image/initialize.png?raw=true)

- Put files to process at `data/` and click `Get Current Files` button to get file names.
 - Detection file paths: gets all files with mp4 extension.
 - Post processing excel file paths: gets all excel files with names that ends with `_detection`.
 - Post processing video file paths: gets all excel files with names that ends with `_detection_post` and gets videos(mp4) with same names except `_detection_post`.
 - Excluded file paths: any other files.
 - Detection preview file: first mp4 file from `Detection file paths`. Used for `Preview Detection`.

 ![GetFiles](doc/image/get_files.png?raw=true)


## 1. Notebook

Notebook(app_notebook.ipynb) consists python code for running user's frontend.

## 2. Detection

- Output Type:
  - excel: Outputs detection data in excel from videos in `Detection file paths`.
  - video: Outputs detection video from videos in `Detection file paths`.
  - excel+video: Both from above.

- Detection Method:
  - ThresholdDetector: Detector using binary thresholding.
    - Image Crop
      - Height bound: Overall crop height bound.
      - Width bound: Overall crop width bound.
    - Flow
      - Check if water flows left to right: Used for calculating relative angle of zebrafish to water flow.
    - Thresholds
      - Median Blur Size: Median blur kernel size. Median blur is applied on l_channel image. 
      - L Channel Threshold: Binary threshold.
      - Size bound: Size bound of zebrafish in pixels.
      - Closing iterations: Iterations for dilation and erosion (closing).

- Detection preview:
  If current settings are saved, you can see its results by clicking `Show Preview` button.

  ![Preview](doc/image/preview.png?raw=true)

- Run detection by clicking `Run` button or interrupt by `Interrupt` button.

  ![Run](doc/image/run.png?raw=true)

## 3. Postprocess

- Output Type:
  - excel: Outputs post processed data in excel from excel files in `Post processing excel file paths`.
  - video: Outputs post processed video from excel files and matching video files in `Post processing video file paths`.

- Tracker:
  - VicinityTracker: Tracking by searching vicinity.
    - Number of frames to find: max number of frames for searching.
    - Max distance to find: max distance for searching in pixels.
    - Max distance increment ratio per frame: max distance is incremented per frame.

- Methods:
  - DataConverter:
    - Frames per second: fps for calculating time related values(velocity ...).
    - Pixel to cm ratio: Used for converting pixel measurements to cm.
    - Converting methods: select converting methods.
  - Position bounder: add position bounds for checking if position is in the added bounds.(Bool)
    - Current Bounds: shows current added bounds.
