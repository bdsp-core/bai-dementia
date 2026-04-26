clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
load MGHBACAte 
%% 
i1 = find(T.CA>=30&T.CA<=35); 
i2 = find(T.CA>=35&T.CA<=40); 
m1 = mean(T.CA(i1))
m2 = mean(T.BA(i2))

