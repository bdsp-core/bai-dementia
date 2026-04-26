clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load MGHBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2
load MGHBACAte 
load SHHSBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2

%% 
ba = [T.BA1; T.BA2]; 
ca = [T.CA1; T.CA2]; 
da = [ba-ca]; 

x = ca+randn(size(da))*.01;  
% [f, gof] = createFit1(x, da)
% save MGH_Model f
load MGH_Model
%%
c = f(ca); 
xx = 35:90; 
cm = f(xx); 

figure(1); clf; 
subplot(221); 
scatter(x,ba,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,xx,'r--','linewidth',2); 
axis([35 90 35 90]); 
axis square
xlabel('CA'); ylabel('BA'); 

subplot(222); 
scatter(x,da,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on; 
plot(xx,cm,'r--','linewidth',2); 
xlabel('CA'); 
ylabel('dA = BA - CA'); 
axis([35 90 -20 20]); 
axis square

subplot(223); 
scatter(x,ba-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx,'r--','linewidth',2)
axis([35 90 35 90]); 
axis square
xlabel('CA'); ylabel('BA'); 
set(gcf,'color','w'); 




subplot(224); 
scatter(x,da-c,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
hold on
plot(xx,xx*0,'r--','linewidth',2); 

xlabel('CA'); 
ylabel('dA = BA - CA'); 
axis([35 90 -20 20]); 
axis square


%% compare first vs second recordings
ca1 = T.CA1; ca2 = T.CA2; 
ba1 = T.BA1; 
ba2 = T.BA2; 
ba1c = ba1-f(ca1); 
ba2c = ba2-f(ca2); 

figure(2); clf; 
subplot(121); boxplot([ba1 ba2]); 
title('Without correction'); 
ylim([20 105]); 

color = ['b', 'r'];
h = findobj(gca,'Tag','Box');
for j=1:length(h)
   patch(get(h(j),'XData'),get(h(j),'YData'),color(j),'FaceAlpha',.2);
end

subplot(122); boxplot([ba1c ba2c]); 
title('With correction'); 
ylim([20 105]); 
grid on

color = ['b', 'r'];
h = findobj(gca,'Tag','Box');
for j=1:length(h)
   patch(get(h(j),'XData'),get(h(j),'YData'),color(j),'FaceAlpha',.2);
end

grid on

set(gcf,'color','w'); 

%% 
[median(ba1) median(ba2)]
[median(ba1c) median(ba2c)]
