#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from collections import Counter
import datetime
from dateutil.parser import parse
import os
import os.path
import shutil
import sys
import pickle
from tqdm import tqdm
import numpy as np
import pandas as pd
from scipy import io as sio
from sklearn.preprocessing import StandardScaler
from keras.models import load_model
from load_mgh_sleep_dataset import *
from segment_EEG import *
from extract_features_parallel import *
sys.path.insert(0, '/data/brain_age/mycode')
from dnn_regressor import my_nobias_loss
from step3_train_age import impute_missing_stage

import matplotlib
matplotlib.rc('pdf', fonttype=42)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn
seaborn.set_style('ticks')

epoch_length = 30 # [s]
start_end_remove_epoch_num = 1
amplitude_thres = 500 # [uV]
changepoint_epoch_num = 1
EEG_channels = ['F3M2','F4M1','C3M2','C4M1','O1M2','O2M1']
combined_EEG_channels =  ['F', 'C', 'O']
line_freq = 60.  # [Hz]
bandpass_freq = [0.5, 20.]  # [Hz]
tostudy_freq = [0.5, 20.]  # [Hz]
random_state = 2


seg_mask_explanation = [
    'normal',
    'around sleep stage change point',
    'NaN in sleep stage',
    'NaN in EEG',
    'overly high/low amplitude',
    'flat signal',
    'NaN in feature',
    'NaN in spectrum',
    'muscle artifact',
    'spurious spectrum']


def softplus(x):
    return np.log(1+np.exp(-np.abs(x))) + np.maximum(x,0)
    
    
def myprint(seg_mask):
    sm = Counter(seg_mask)
    for ex in seg_mask_explanation:
        if ex in sm:
            print('%s: %d/%d, %g%%'%(ex,sm[ex],len(seg_mask),sm[ex]*100./len(seg_mask)))
    
    
if __name__=='__main__':
    normal_only = True
    np.random.seed(random_state)
    
    feature_dir = '/media/mad3/Projects/SLEEP/SLEEP_STAGING/all_brain_age_features'
    signal_dir = '/media/mad3/Datasets_ConvertedData/sleeplab/grass_data'
        
    subject_files_path = 'subject_files.npy'
    if os.path.exists(subject_files_path):
        print('Reading from %s'%subject_files_path)
        subject_files = np.load(subject_files_path)
    else:
    
        ## generate subject_files: signal_path    sleep_stage_paths   feature_path
        signal_paths = []
        label_paths = []
        feature_paths = []
        #cc = 0
        sds = sorted(os.listdir(signal_dir))
        for sd in tqdm(sds):
            signal_path = []
            label_path = []
            sfs = os.listdir(os.path.join(signal_dir, sd))
            for sf in sfs:
                if sf.startswith('Signal_') and sf.endswith('.mat'):
                    signal_path.append(sf)
                if sf.startswith('Labels_') and sf.endswith('.mat'):
                    label_path.append(sf)
            if len(signal_path)==len(label_path)==1:
                signal_paths.append(os.path.join(signal_dir, sd, signal_path[0]))
                label_paths.append(os.path.join(signal_dir, sd, label_path[0]))
                x = signal_path[0].replace('Signal_', 'Feature_')
                x = re.sub('_1[,.]([0-9])', r'_1\1', x)
                feature_paths.append(os.path.join(feature_dir, x))
            #else:
            #    cc += 1
            #    print('[%d] %s'%(cc, sd))
        subject_files = np.c_[signal_paths, label_paths, feature_paths]
        np.save(subject_files_path, subject_files)
    subject_num = len(subject_files)
    
    subject_err_path = 'err_subject_reason.txt'
    if os.path.isfile(subject_err_path):
        err_subject_reasons = []
        err_subjects = []
        with open(subject_err_path,'r') as f:
            for row in f:
                if row.strip()=='':
                    continue
                i = row.split(':::')
                err_subjects.append(i[0].strip())
                err_subject_reasons.append(i[1].strip())
    else:
        err_subject_reasons = []
        err_subjects = []
        
    feature_dir_old1 = '/data/brain_age/brain_age_Elissa_AllMGH/features'
    feature_dir_old2 = '/data/brain_age/eeg_features'
    feature_paths_old1 = os.listdir(feature_dir_old1)
    feature_paths_old2 = os.listdir(feature_dir_old2)
    feature_paths_old1_ = list(map(lambda x:x.replace(',',''), os.listdir(feature_dir_old1)))
    feature_paths_old2_ = list(map(lambda x:x.replace(',',''), os.listdir(feature_dir_old2)))
    
    features = []
    #subject_ages = []
    for si in range(0):#subject_num
        data_path = subject_files[si,0]
        label_path = subject_files[si,1]
        feature_path = subject_files[si,2]
        subject_file_name = os.path.basename(feature_path)
        if subject_file_name in err_subjects:
            continue
        if os.path.isfile(feature_path):
            print('====== [(%d)/%d] %s %s ======'%(si+1,subject_num,subject_file_name.replace('.mat',''),datetime.datetime.now()))
            
        else:
            print('\n====== [%d/%d] %s %s ======'%(si+1,subject_num,subject_file_name.replace('.mat',''),datetime.datetime.now()))
            
            if subject_file_name in feature_paths_old1_:
                print('Copying from old set 1...')
                shutil.copyfile(os.path.join(feature_dir_old1, feature_paths_old1[feature_paths_old1_.index(subject_file_name)]), feature_path)
                continue
            if subject_file_name in feature_paths_old2_:
                print('Copying from old set 2...')
                shutil.copyfile(os.path.join(feature_dir_old2, feature_paths_old2[feature_paths_old2_.index(subject_file_name)]), feature_path)
                continue
                
            try:
                # check and load dataset
                EEG, sleep_stages_, params = check_load_Twin_dataset(data_path, label_path, channels=EEG_channels)
                Fs = params.get('Fs')
                if Fs!=200:
                    raise ValueError('Spurious Fs at %gHz'%Fs)
                
                # segment EEG
                segs_, sleep_stages_, seg_times_, seg_mask, specs_, freq = segment_EEG(EEG, sleep_stages_, epoch_length, epoch_length, Fs, EEG_channels, notch_freq=line_freq, bandpass_freq=bandpass_freq, start_end_remove_window_num=start_end_remove_epoch_num, amplitude_thres=amplitude_thres, to_remove_mean=False, n_jobs=-1)
                if segs_.shape[0] <= 0:
                    raise ValueError('Empty EEG segments')
                
                """    
                # muscle artifact removal
                specs_matlab = 10*np.log(specs_.T)
                specs_matlab[np.isinf(specs_matlab)] = np.nan
                specs_matlab = specs_matlab - np.nanmean(specs_matlab, axis=2, keepdims=True)
                sio.savemat('segs.mat', {'segs':segs_.transpose(1,2,0), 'Fs':Fs, 'specs':specs_matlab})#, 'specs_orig':specs_.T
                with open('matlab_output.txt','w') as ff:
                    subprocess.check_call([MATLAB_BIN_PATH, '<', MATLAB_CODE_PATH], stdout=ff)
                muscle_rej_ch = sio.loadmat('rej.mat')['rejE'].T==1  # (#sample, #channel)
                muscle_rej_ch1d = np.where(np.any(muscle_rej_ch,axis=1))[0]
                for i in muscle_rej_ch1d:
                    seg_mask[i] = seg_mask_explanation[8]
                """
                if normal_only:
                    good_ids = np.where(np.in1d(seg_mask,seg_mask_explanation[:2]))[0]
                    if len(good_ids)<=300:
                        myprint(seg_mask)
                        raise ValueError('<=300 normal segments')
                    segs_ = segs_[good_ids]
                    specs_ = specs_[good_ids]
                    sleep_stages_ = sleep_stages_[good_ids]
                    seg_times_ = seg_times_[good_ids]
                else:
                    good_ids = np.arange(len(seg_mask))

                # extract features

                features_, feature_names = extract_features(segs_, EEG_channels, combined_EEG_channels, Fs, 2, tostudy_freq, 2, 1, seg_times_, return_feature_names=True, n_jobs=-1, verbose=True)
                features_[np.isinf(features_)] = np.nan
                nan_ids = np.where(np.any(np.isnan(features_),axis=1))[0]
                for ii in nan_ids:
                    seg_mask[ii] = seg_mask_explanation[6]
                if normal_only:
                    good_ids2 = np.where(np.in1d(np.array(seg_mask)[good_ids],seg_mask_explanation[:2]))[0]
                    segs_ = segs_[good_ids2]
                    specs_ = specs_[good_ids2]
                    sleep_stages_ = sleep_stages_[good_ids2]
                    seg_times_ = seg_times_[good_ids2]
                
                myprint(seg_mask)
                
            except Exception as e:
                err_info = str(e.message).split('\n')[0].strip()
                print('\n%s.\nSubject %s is IGNORED.\n'%(err_info,subject_file_name))
                err_subject_reasons.append(err_info)
                err_subjects.append(subject_file_name)

                with open(subject_err_path,'a') as f:
                    msg_ = '%s::: %s\n'%(subject_file_name,err_info)
                    f.write(msg_)
                continue
            
            sio.savemat(feature_path, {
                'EEG_feature_names':feature_names,
                'EEG_features':features_,
                'EEG_specs':specs_,
                'EEG_frequency':freq,
                'sleep_stages':sleep_stages_,
                'seg_times':seg_times_,
                #'age':age,
                'seg_mask':seg_mask,
                'Fs':Fs})
                #'subject':subject
                #'gender':gender,
        #subject_ages.append(age)
    
    ## build input matrix X for testing

    stages = ['W','N1','N2','N3','R']
    stage2num = {'W':5,'R':4,'N1':3,'N2':2,'N3':1}
    num2stage = {stage2num[x]:x for x in stage2num}

    # load EEG features
    feature_files = sorted([os.path.join(feature_dir, x) for x in os.listdir(feature_dir)])
    
    # build features and ages
    # mean_features_s = {'W': array(#patient,#feature),
    #             'N1': array(#patient,#feature), ...}
    mean_features_s = {stage:[] for stage in stages}
    subjects_s = {stage:[] for stage in stages}
    sleep_stages = []
    minimum_epochs_per_stage = 5
    #minimum_epochs = 300
    for pid in tqdm(range(len(feature_files))):
        fn = feature_files[pid]
        eeg_patient = sio.loadmat(fn, variable_names=['EEG_feature_names','EEG_features','sleep_stages'])
        if 'sleep_stages' not in eeg_patient:
            continue
        if pid==0:
            feature_names = np.array(map(lambda x:x.strip(), eeg_patient['EEG_feature_names']))#[range(12)+range(18,102)]
        
        """
        specs_db = 10*np.log10(eeg_patient['EEG_specs'])
        # criterion 1: slope of spectrum < 0
        criteria1 = np.all([np.polyfit(np.arange(specs_db.shape[1]), specs_db[ii], 1)[0]<0 for ii in range(len(specs_db))], axis=1)
        
        totalpower = specs_db.mean(axis=1)
        #all_total_power_db.extends(totalpower)
        # criterion 2: total power not too big, not too small
        criteria2 = np.all(totalpower<=15, axis=1)&np.all(totalpower>=-4, axis=1)
        
        good_id = np.where(criteria1&criteria2)[0]
        """
        
        features_ = eeg_patient['EEG_features']#[good_id]
        features_ = np.sign(features_)*np.log1p(np.abs(features_))
        sleep_stages.append(eeg_patient['sleep_stages'].flatten())
        sleep_stages_ = sleep_stages[-1]#[good_id]
        
        #if len(np.unique(sleep_stages_))!=5:  # if subject has less than 5 stages, skip
        #    continue
        for stage in stages:
            eid = np.where(sleep_stages_==stage2num[stage])[0]
            if len(eid)<minimum_epochs_per_stage:
                continue
            mean_features_s[stage].append(features_[eid].mean(axis=0))
            subjects_s[stage].append(feature_files[pid])
            
    for stage in stages:
        #assert np.any(np.isnan(mean_features_s[stage]))==False
        print('%s: %d'%(stage,len(mean_features_s[stage])))

    feature_num_each_stage = len(feature_names)
    feature_num = feature_num_each_stage*len(stages)
    N = len(feature_files)
    X = np.zeros((N, feature_num),dtype=float)+np.nan
    for ni in tqdm(range(N)):
        for si in range(len(stages)):
            stage = stages[si]
            if feature_files[ni] in subjects_s[stage]:
                pid = subjects_s[stage].index(feature_files[ni])
                X[ni, si*feature_num_each_stage:(si+1)*feature_num_each_stage] = mean_features_s[stage][pid]#*np.sum(sleep_stages[ni]==stagesint[si])*1./sleep_stages[ni].sum()

    training_info_folder = '/data/brain_age/mycode'
    Xnonan = sio.loadmat(os.path.join(training_info_folder, 'mgh_eeg_data.mat'))['Xtr']
    missing_stage = list(np.sum(np.isnan(X), axis=1)//feature_num_each_stage)
    K = 10  # number of patients without any missing stage to average
    X = impute_missing_stage(X, K, Xnonan=Xnonan)

    with open(os.path.join(training_info_folder, 'feature_normalizer_eeg.pickle'), 'rb') as f:
        standardizer = pickle.load(f)
    X = (X-standardizer.mean_)/standardizer.scale_
    
    ## testing (applying the trained model)
    
    model = load_model(os.path.join(training_info_folder, 'dnn_eeg_nomissingstage.pickle'), custom_objects={'loss':my_nobias_loss(1.)})
    BA = model.predict({'X':X, 'sample_weight':np.ones((len(X),1))})[:,0].flatten()
    
    ## generate output
    
    # add subjects with error
    notes = []
    for i, ba in enumerate(BA):
        if ba<1 or ba>120:
            notes.append('Possible EEG artifact')
        elif missing_stage[i]>=3:
            notes.append('Too many missing stages')
        else:
            notes.append('')
    feature_files.extend(err_subjects)
    BA = np.r_[BA, [np.nan]*len(err_subjects)]
    missing_stage.extend([np.nan]*len(err_subjects))
    notes.extend(err_subject_reasons)
    df = pd.DataFrame(data={'SubjectID':[os.path.basename(x)[len('Feature_'):-len('.mat')] for x in feature_files], 'BA (yr)':BA, 'NumMissingStage':missing_stage, 'Note':notes})
    
    # add CA
    CA = []
    for ff in tqdm(feature_files):
        if not ff.startswith('/me'):#### ff not in subject_files[:,2]:
            CA.append(np.nan)
            continue
        id_path = os.path.join(os.path.dirname(subject_files[subject_files[:,2]==ff,0][0]), 'ID.csv')
        id_data = pd.read_csv(id_path, sep=',')
        dov = id_data.DateOfVisit[0]
        dob = id_data.DateOfBirth[0]
        if pd.isna(dov) or pd.isna(dob):
            CA.append(np.nan)
        else:
            CA.append((parse(dov)-parse(dob)).total_seconds()/86400./365.)
    df['CA (yr)'] = CA
        
    df = df[['SubjectID', 'CA (yr)', 'BA (yr)', 'NumMissingStage', 'Note']]
    df = df.sort_values('SubjectID')
    import pdb;pdb.set_trace()
    df.to_csv('output_BA.csv', sep='\t', index=False)
    
    """
    for si, subject in enumerate(tqdm(feature_files, leave=False)):
        fp = os.path.join(feature_dir, subject)
        if not os.path.exists(fp):
            continue
        res = sio.loadmat(fp, variable_names=['EEG_specs', 'EEG_frequency', 'sleep_stages'])
        specs = res['EEG_specs']
        freqs = res['EEG_frequency'].flatten()
        sleep_stages = res['sleep_stages'].flatten()
        
        specs=10*np.log10(specs)
        specs = specs.mean(axis=1)
        
        plt.close()
        fig = plt.figure(figsize=(10,6))
        gs = gridspec.GridSpec(2, 1, height_ratios=[1,2])
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.step(np.arange(len(specs))*30./3600., sleep_stages, color='k')
        ax1.set_ylim([0.5,5.5])
        ax1.set_yticks([1,2,3,4,5])
        ax1.set_yticklabels([num2stage[x] for x in ax1.get_yticks()])
        ax1.set_ylabel('Sleep Stage')
        ax1.yaxis.grid(True)
        plt.setp(ax1.get_xticklabels(), visible=False)
        seaborn.despine(ax=ax1)
        
        ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
        ax2.imshow(specs.T, cmap='jet', aspect='auto', extent=(0,len(specs)*30./3600,freqs.min(),freqs.max()), origin='lower', vmin=-30, vmax=10)
        ax2.set_ylabel('Frequency (Hz)')
        ax2.set_xlabel('Time (hour)')
        
        plt.tight_layout()
        plt.savefig('output_figures/%s_BA_%.2f.png'%(subject, BA[si]), bbox_inches='tight', pad_inches=0.01)
    """
