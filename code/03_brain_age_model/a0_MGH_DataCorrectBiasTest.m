clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
load MGHBACAte 
%% 

da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; ; 
% [f, gof] = createFit1(x, da)
% save MGH_Model f
load MGH_Model
%%
c = f(T.CA); 
xx = 17:80; 
cm = f(xx); 

figure(1); clf; 
subplot(221); 
scatter(x,T.BA,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 
axis([15 85 15 85]); 
axis square
xlabel('CA'); ylabel('BA'); 

subplot(222); 
scatter(x,da,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,cm,'r--','linewidth',2); 
xlabel('CA'); 
ylabel('dA = BA - CA'); 
axis([15 85 -20 20]); 
axis square

subplot(223); 
scatter(x,T.BA-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx,'r--','linewidth',2)
axis([15 85 15 85]); 
axis square
xlabel('CA'); ylabel('BA'); 




subplot(224); 
scatter(x,da-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx*0,'r--','linewidth',2); 

xlabel('CA'); 
ylabel('dA = BA - CA'); 
axis([15 85 -20 20]); 
axis square

set(gcf,'color','w'); 


