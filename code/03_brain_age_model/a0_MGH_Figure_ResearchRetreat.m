clear all; clc; format compact; 

%% for research retreat -- plot de-biased brain age
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
%load MGHBACAte 

%%
da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; 
y = T.BA+randn(size(da))*.01;
[f, gof] = createFit2(x, y);
save MGH_Model f

%% ba vs ca -- before correction
c = f(T.CA); 
xx = 17:80; 
cm = f(xx); 

figure(1); clf; 
subplot(221); 
scatter(T.CA,T.BA,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 
plot(xx,cm,'b--','linewidth',2); 
axis([20 80 20 80]); 
axis square

%% show systematic error -- residuals
figure(1); ; 
subplot(222); 
scatter(T.CA,T.BA-T.CA,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx*0,'r--','linewidth',2); 
x = T.CA+randn(size(da))*.01; 
y = T.BA-T.CA+randn(size(da))*.01;
[f, gof] = createFit1(x, y);

plot(xx,f(xx),'b--','linewidth',2); 

axis([20 80 -20 20]); 
axis square

%% fit curve to error 
da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; 
y = T.BA-T.CA; 
[f, gof] = createFit1(x,y);

%% 
figure(2); clf; 
ba = T.BA-f(T.BA);
ca = T.CA; 
scatter(ca,ba,100,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.2,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 
axis([20 80 20 80]); 
axis square
set(gcf,'color','w'); 
xlabel('Chronological age'); 
ylabel('Brain age'); 
set(gca,'tickdir','out')
set(gca,'fontsize',20)
print -dpng -r300 fig_BrainAge

% x = ca+randn(size(da))*.01; 
% y = ba+randn(size(da))*.01;
% % [ft, gof] = createFit1(x,y);
% [ft, gof] = createFit1(x,y);

% plot(xx,ft(xx),'b--','linewidth',2); 

[RHO,PVAL] = corr(ca,ba,'type','Spearman')