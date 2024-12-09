from mne.io import read_raw_edf, read_raw_bdf, RawArray
from mne import create_info
from mne.filter import design_mne_c_filter
import traceback
from numpy import convolve

def bandpass(signal, lowcut, highcut, fs):
    kernel = design_mne_c_filter(fs, l_freq=lowcut, h_freq=highcut)
    return convolve(kernel, signal, mode='vaild')

def load_preproc_data(fname, config):
    data = read_raw_bdf(fname) if fname.endswith('.bdf') else read_raw_edf(fname)
    data_preproc = None
    for key in ['EEG', 'EMG', 'EOG']:
        channel_data = preprocess_channel(data, key, config[key])
        if channel_data:
            if data_preproc is None:
                data_preproc = channel_data
            else:
                data_preproc.add_channels([channel_data])
    return data_preproc

def preprocess_channel(data, name, ch_config):
    print(ch_config)
    sfreq  = data.info['sfreq']
    try:
        signal = data.get_data(int(ch_config['ch']))
        print('Channel ok: ', name)
    except:
        print('No channel id found for: ', name)
        return None

    try:
        print('Reference ok')
        ref  = data.get_data(int(ch_config['ref']))
        signal = signal - ref
    except:
        pass

    try:
        freq_low, freq_high = float(ch_config['filt'][0]), float(ch_config['filt'][1])
        print('Filter ok')
        print(freq_low, freq_high)
        print('Fl %.2f, Fh %2.f' % (freq_low, freq_high))
        signal = [bandpass(signal[0], freq_low, freq_high, sfreq)]
    except Exception as e:
        print(e)
        print('No filter, exception:')
        print(traceback.format_exc())

    new_info = create_info([name], ch_types=['eeg'], sfreq=sfreq)
    return RawArray(signal, new_info)
