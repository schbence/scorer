### Basic GUI for EEG/PSD scoring with YASA algorithm

#### Setup
Requirements: **python3**, **pip3**, **venv**
1. Create a new virtual environment: `python3 -m venv scorer`
2. Activate env: `source scorer/bin.activate`
3. Install required python packages: `pip3 install -r requirements.txt`
4. Run: `python3 main-gui.py`

#### Configuration
All configurations are located in `config.json`.

Structure of the file:
- Channel configs
  - Montage name
    - Channel name (EEG/EMG/EOG)
      - `ch` : channel number from .edf/.bdf file
      - `ref` : reference channel (optional)
      - `filt` : bandpass filter settings in the format `[highpass freq., lowpass freq]`
- File configs:
  - `output_dir` : path of directory where to save the hypnograms and plots (will be created if not present)
  - `history_file` : log file containing info of previous scorings
  - `error_file` : error log file, helpful for debugging

