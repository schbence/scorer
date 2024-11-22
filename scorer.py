import numpy as np
from matplotlib.pyplot import subplots, tight_layout, savefig
from mne.io import read_raw_edf
import yasa
import json
from scipy.signal import *
from scipy.signal.windows import gaussian

# Constants
STAGES = ['N3', 'N2', 'N1' ,'R', 'W']
STAGES_JSON = ['N3', 'N2', 'N1', 'REM', 'Wake']
EPOCH_LEN = 30

def hyp_from_json(jname):
    f = open(jname, 'r')
    d = json.load(f)[0]
    f.close()
    return [e['stage'] if e['stage'] else 'none' for e in d]

def score_eeg(data, eeg):
    global STAGES
    print('Scoring EEG...')
    sls = yasa.SleepStaging(data, eeg_name=eeg)
    hyp = sls.predict()
    print('Done.')
    return np.array([STAGES.index(h) for h in hyp])

def score_psg(data, eeg, eog, emg):
    global STAGES
    print('Scoring PSG...')
    sls = yasa.SleepStaging(data, eeg_name=eeg, eog_name=eog, emg_name=emg)
    hyp = sls.predict()
    print('Done.')
    return np.array([STAGES.index(h) for h in hyp])

def timefreq_plot(ax, sig, Fs, fmax_show):
    win = 1024
    Ts = 1. / Fs
    hop = 128

    delta_t = hop * Ts
    delta_f = 1 / (win * Ts)

    STF = ShortTimeFFT(gaussian(win, win / 8, sym=True), hop=hop, fs=Fs)
    Sxx = STF.stft(sig)
    Pxx = np.log(abs(Sxx)**2)

    fmax = Sxx.shape[0] * delta_f
    tmax = Sxx.shape[1] * delta_t

    #ax.imshow(Pxx, aspect='auto', cmap='inferno', origin='lower', vmin=-22, vmax=-15, extent=[0, tmax, 0, fmax])
    vmin, vmax = np.quantile(Pxx[:int(len(Pxx)* fmax_show / fmax)], [0.1, 0.9])
    ax.imshow(Pxx, aspect='auto', cmap='inferno', origin='lower',
        vmin=vmin, vmax=vmax, extent=[0, tmax, 0, fmax])

    ax.set_ylim(0, fmax_show)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Freq. [Hz]')
    return delta_f, delta_t, Sxx

def hypno_plot(ax, hyp):
    global STAGES
    t = np.arange(len(hyp)) * 30
    ax.plot(t, hyp)
    ax.set_yticks(np.arange(5), STAGES)
    ax.set_xlim(0, t[-1])
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('STAGE')
    ax.grid()

def row_template(epoch, stage):
    global STAGES_JSON, EPOCH_LEN
    stg_to_digit = {'N1':-1, 'N2':-2, 'N3':-3, 'Wake':1, 'REM':0}
    d = {}
    d['epoch'] = int(epoch + 1)
    d['start'] = int(epoch * EPOCH_LEN)
    d['end']   = int((epoch + 1) * EPOCH_LEN)
    d['stage'] = STAGES_JSON[stage]
    d['digit'] = stg_to_digit[STAGES_JSON[stage]]
    d['confidence'] = None
    d['channels'] = ['FC1','FC2']
    d['clean'] = 1
    d['source'] = 'human'
    return d

def hyp_to_json(jfile, hyp):
    print('Saving json to: %s' % jfile)
    epochs = np.arange(len(hyp))
    rows = [row_template(e, s) for e, s in zip(epochs, hyp)]
    f = open(jfile, 'w')
    json.dump([rows, []], f, indent=2)
    f.close()
    print('Done.')

def plot_hyp_timefreq(signal, sfreq, fmax_show, hyp, fname):
    print('Saving time-frequency plot to: %s' % fname)
    f, (ax0, ax1) = subplots(2, 1,
        gridspec_kw={'height_ratios': [1,3]}, **{'figsize':[12,6]})
    hypno_plot(ax0, hyp)

    df, dt, Sxx = timefreq_plot(ax1, signal, sfreq, fmax_show)

    tight_layout()
    if type(fname) is list:
        [savefig(f) for f in fname]
    else:
        savefig(fname)
    print('Done.')
