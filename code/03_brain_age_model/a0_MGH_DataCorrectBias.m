clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
%load MGHBACAte 
%% 

da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; ; 
[f, gof] = createFit1(x, da)
save MGH_Model f
%%
c = f(T.CA); 
xx = 17:80; 
cm = f(xx); 

figure(1); clf; 
subplot(321); 
scatter(x,T.BA,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 

subplot(322); 
scatter(x,da,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,cm,'r--','linewidth',2); 

subplot(324); 
scatter(x,da-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx*0,'r--','linewidth',2); 


subplot(323); 
scatter(x,T.CA+da-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx,'r--','linewidth',2)