clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
%load MGHBACAte 

%% balance the data 
x = 20:80; 
ca = T.CA;
ba = T.BA; 
histogram(ca,x); 

% % resample until each bin has 530 or more
% bins = 20:5:80; 
% for i = 2:length(bins)
%    ind = find(ca>bins(i-1) & ca<=bins(i)); 
%    n = length(ind); 
%    if n<530
%       temp1 = ca(ind); 
%       temp2 = ba(ind); 
%       temp3 = T(ind,:); 
%       k = 530 - n; 
%       [t1,idx] = datasample(temp1,k); 
%       ba = [ba; temp2(idx)]; 
%       ca = [ca; temp1(idx)]; 
%       T = [T; temp3]; 
%       figure(1); ; 
%       histogram(ca,x); 
%       drawnow; 
%      ind = find(ca>bins(i-1) & ca<=bins(i)); 
% 
%    end
% end

%%
da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; 
y = T.BA+randn(size(da))*.01;
% [f, gof] = createFit1(x,y);
[f, gof] = createFit2(x, y);
save MGH_Model f
close; 

%% ba vs ca -- before correction
c = f(T.BA); 
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
% [f, gof] = createFit1(x,y);
[f, gof] = createFit2(x, y);

plot(xx,f(xx),'b--','linewidth',2); 

axis([20 80 -20 20]); 
axis square

%% fit curve to error 
da = T.BA-T.CA; 
x = T.CA+randn(size(da))*.01; 
y = T.BA-T.CA; 
% [f, gof] = createFit1(x,y);
[f, gof] = createFit2(x,y);

subplot(223); 
ba = T.BA-f(T.BA);
ca = T.CA; 
scatter(ca,ba,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 
axis([20 80 20 80]); 
axis square

x = ca+randn(size(da))*.01; 
y = ba+randn(size(da))*.01;
% [ft, gof] = createFit1(x,y);
[ft, gof] = createFit2(x,y);

plot(xx,ft(xx),'b--','linewidth',2); 

%% residuals for corrected ba
subplot(224); 
scatter(ca,ba-ca,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx*0,'r--','linewidth',2); 

x = ca+randn(size(da))*.01; 
y = ba-ca+randn(size(da))*.01;
% [ft, gof] = createFit1(x,y);
[ft, gof] = createFit2(x,y);
plot(xx,ft(xx),'b--','linewidth',2); 
axis([20 80 -20 20]); 
axis square
set(gcf,'color','w'); 

[RHO,PVAL] = corr(ca,ba-ca,'type','Spearman')