import tkinter as tk
from tkinter import filedialog
from tkinter import ttk, Frame
import json
from datetime import datetime
from threading import Thread
import traceback
import os
import re
import scorer
import datahandler

def load_config_file(fname):
    f = open(fname, 'r')
    config = json.load(f)
    f.close()
    return config

def check_output_dir():
    exists = os.path.exists(OUTPUT_DIR)
    if not exists:
        os.makedirs(OUTPUT_DIR)
        print('Output directory created: %s' % OUTPUT_DIR)

def try_get_gls_code():
    # Try to find GLS, Phase, Night
    # if format not found, use filename from path
    path = infile_var.get()
    try:
        gls_span = re.search('GLS_\d+/', path)
        gls = int(path[gls_span.start()+4:gls_span.end()-1])

        phase_span = re.search('Phase\d/', path)
        phase = int(path[phase_span.start()+5:phase_span.end()-1])

        night_span = re.search('Night_\d+/', path)
        night = int(path[night_span.start()+6:night_span.end()-1])

        ret = 'GLS%02d-p%d-n%02d' % (gls, phase, night)

        type_span = re.search('Zmax|Mentalab', path)
        if type_span:
            ret += '-' + path[type_span.start():type_span.end()].lower()

        print('GLS code found: ', ret)
        return ret

    except:
        ret = '.'.join(path.split('/')[-1].split('.')[:-1])
        print('No GLS code found using: ')
        return ret


def save_history(fname, config):
    f = open(HISTORY_FILE, 'a')
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = "%s, %s, %s\n" % (t, fname, str(config))
    f.write(msg)
    f.close()

def save_error_log(error):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = "%s | %s |\n %s\n\n" % (t, error, traceback.format_exc())
    print(msg)

    f = open(ERROR_LOG_FILE, 'a')
    f.write(msg)
    f.close()

def set_vars_to_config(vars, config):
    vars['ch'].set(config.get('ch', ""))
    vars['ref'].set(config.get('ref', ""))
    vars['flo'].set(config.get('filt', ["",""])[0])
    vars['fhi'].set(config.get('filt', ["",""])[1])

def set_all_vars(config):
    vars = [eeg_vars, emg_vars, eog_vars]
    config_names = ['EEG', 'EMG', 'EOG']
    for var, name in zip(vars, config_names):
        if name in config.keys():
            set_vars_to_config(var, config[name])
        else:
            set_vars_to_config(var, {})

def get_values(vars):
    vals = {}
    vals['ch'] = vars['ch'].get()
    vals['ref'] = vars['ref'].get()
    vals['filt'] = (vars['flo'].get(), vars['fhi'].get())
    return vals

def get_current_config():
    eeg_vals = get_values(eeg_vars)
    eeg = create_channel_config(**eeg_vals)
    eog_vals = get_values(eog_vars)
    eog = create_channel_config(**eog_vals)
    emg_vals = get_values(emg_vars)
    emg = create_channel_config(**emg_vals)
    return create_config('current', eeg, emg, eog)

def create_config(name, eeg, emg, eog):
    return {
        name: {
            'EEG': eeg,
            'EMG': emg,
            'EOG': eog
            }
        }

def create_channel_config(ch, ref, filt):
    return {
        'ch': ch,
        'ref': ref,
        'filt': filt
    }

def preset_selected(event):
    config_name = preset_dropdown.get()
    print('Preset selected:', config_name)
    set_all_vars(configs[config_name])

def get_last_input_dir():
    try:
        with open(HISTORY_FILE,'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            lastfile = lines[-1].split(',')[1]
            lastdir = '/'.join(lastfile.split('/')[:-1])
            print('Last dir found:', lastdir)
            return lastdir.strip()
    except:
        print('No last input found')
        return None

def select_infile():
    last_dir = get_last_input_dir()
    fname = filedialog.askopenfilename(initialdir=last_dir)
    infile_var.set(fname)

def replace_extension(fname, ext):
    return '.'.join(fname.split('.')[:-1] + [ext])

def channel_input_row(parent, name, row, vars):
    settings_label = tk.Label(parent, text=name)
    settings_label.grid(row=row, column=0, padx=5, pady=5)

    ch = tk.Entry(parent, width=3, textvariable=vars['ch'])
    ch.grid(row=row, column=1, padx=5, pady=5)

    ref = tk.Entry(parent, width=3, textvariable=vars['ref'])
    ref.grid(row=row, column=2, padx=5, pady=5)

    flo = tk.Entry(parent, width=4, textvariable=vars['flo'])
    flo.grid(row=row, column=3, padx=5, pady=5)

    dash_label = tk.Label(settings_frame, text="-")
    dash_label.grid(row=0, column=4, padx=5, pady=5)

    fhi = tk.Entry(parent, width=4, textvariable=vars['fhi'])
    fhi.grid(row=row, column=5, padx=5, pady=5)

def init_header(frame):
    channel_label = tk.Label(frame, text="Channel")
    channel_label.grid(row=0, column=1, padx=5, pady=5)

    reference_label = tk.Label(settings_frame, text="Reference")
    reference_label.grid(row=0, column=2, padx=5, pady=5)

    filt_low_label = tk.Label(settings_frame, text="Filt.\nlow")
    filt_low_label.grid(row=0, column=3, padx=5, pady=5)

    dash_label = tk.Label(settings_frame, text="-")
    dash_label.grid(row=0, column=4, padx=5, pady=5)

    filt_high_label = tk.Label(settings_frame, text="Filt.\nhigh")
    filt_high_label.grid(row=0, column=5, padx=5, pady=5)


def init_vars():
    return {name:tk.StringVar() for name in ['ch','ref','flo','fhi']}




def start_scoring():
    config = get_current_config()
    print(config)
    fname = infile_var.get()
    save_history(fname, config['current'])

    def worker():
        try:
            score_button.config(state=tk.DISABLED)

            # Data loading & preprocessing
            status_var.set('Loading data...')
            data = datahandler.load_preproc_data(fname, config['current'])
            print(data.info)

            # Scoring
            status_var.set('Scoring...')
            if 'EOG' in data.info['ch_names'] and 'EMG' in data.info['ch_names']:
                hyp = scorer.score_psg(data, 'EEG', 'EOG', 'EMG')
            else:
                hyp = scorer.score_eeg(data, 'EEG')

            check_output_dir()
            gls_out = '/'.join([OUTPUT_DIR, try_get_gls_code()])

            json_outfile = replace_extension(infile_var.get(), 'json')
            scorer.hyp_to_json(json_outfile, hyp)
            scorer.hyp_to_json(gls_out + '.json', hyp)

            png_outfiles = [replace_extension(infile_var.get(), 'png'),
                gls_out + '.png']

            scorer.plot_hyp_timefreq(data.get_data('EEG')[0],
                data.info['sfreq'], 30, hyp, png_outfiles)
            print('Timfreq + hypno plot saved to: ', png_outfiles)

            status_var.set('Done!')
        except Exception as error:
            status_var.set('An error occured, check errors.log')
            save_error_log(error)
            print(error)
        finally:
            score_button.config(state=tk.NORMAL)

    thread = Thread(target=worker)
    thread.start()



all_configs = load_config_file('config.json')
configs = all_configs['channel_configs']
file_configs = all_configs['file_configs']

HISTORY_FILE = file_configs['history_file']
ERROR_LOG_FILE = file_configs['error_file']
OUTPUT_DIR = file_configs['output_dir']

root = tk.Tk()
root.title("YASA - scorer GUI")

# Variables
eeg_vars = init_vars()
emg_vars = init_vars()
eog_vars = init_vars()

preset_var = tk.StringVar()
preset_var.set(list(configs.keys())[0])

infile_var = tk.StringVar()
infile_var.set('...')

status_var = tk.StringVar()
status_var.set('Idle')

# File select frame
file_select_frame = Frame(root)
file_select_frame.pack(anchor='w', padx=10, pady=10)

file_select_button = tk.Button(file_select_frame, text="Select file", command=select_infile)
file_select_button.grid(row=0, column=0, padx=5, pady=5)

file_select_label = ttk.Label(file_select_frame, textvariable=infile_var, wraplength=500)
file_select_label.grid(row=0, column=1, padx=5, pady=5)

# Preset frame
preset_frame = Frame(root)
preset_frame.pack(anchor='w', padx=10, pady=10)

preset_label = tk.Label(preset_frame, text="Presets:")
preset_label.grid(row=0, column=0, padx=5, pady=5)

preset_dropdown = ttk.Combobox(preset_frame, values=list(configs.keys()), textvariable=preset_var)
preset_dropdown.bind('<<ComboboxSelected>>', preset_selected)
preset_dropdown.grid(row=0, column=1, padx=5, pady=5)

# Settings frame
settings_frame = Frame(root)
settings_frame.pack(padx=10, pady=10)

#   Header
init_header(settings_frame)

# Settings
eeg_row = channel_input_row(settings_frame, 'EEG', 1, eeg_vars)
eog_row = channel_input_row(settings_frame, 'ECG', 2, eog_vars)
emg_row = channel_input_row(settings_frame, 'EMG', 3, emg_vars)

# Start score frame
start_frame = Frame(root)
start_frame.pack(padx=10, pady=10)

score_button = tk.Button(start_frame, text="Score!", command=start_scoring)
score_button.grid(row=0, column=0, padx=5, pady=5)

progress_label = ttk.Label(start_frame, textvar=status_var)
progress_label.grid(row=1, column=0, padx=5, pady=5)



# Start
set_all_vars(configs['zmax'])
root.mainloop()
