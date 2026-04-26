clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load SHHSBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2

%% 
boxplot([T.BA1 T.BA2]); 

d1 = T.BA1; 
d2 = T.BA2; 

% systematic error? medians are very close... 
median(d1)
median(d2)

%% estimate systmatic age-dependent bias, then remove it
% assume: BA1 = BA0 + B(CA) = CA + dA, where BA0 = initial estimate, B(CA) = bias

x = [T.CA1; T.CA2]; y = [T.BA1; T.BA2];

figure(2); clf; 

subplot(121); 
plot(x,y,'.');
xx = 39:90; hold on; plot(xx,xx,'r--'); 
axis([39 90 39 90]); 
axis square; 
title('biased prediction') 
xlabel('CA'); 
ylabel('predicted CA'); 

subplot(122); 
plot(x,y-x,'.');
xx = 39:90; hold on; plot(xx,xx*0,'r--'); 
xlim([39 90])
ylim([-50 20])
axis square; 
title('error') 
xlabel('CA'); 
ylabel('predicted CA'); 

%% fit polynomial to data --to remove bias
[fitresult, gof] = createFit(x,y);

figure(2); hold on
h = plot( fitresult, x, y);
p1 = -0.0002742; 
p2 =      0.0491; 
p3 =      -2.238; 
p4 =       72.58; 

c = p1*x.^3 + p2*x.^2 + p3*x + p4;
clf; 
h = plot( fitresult, x, y);


%% check that this removes the bias
figure(3); clf; 
% yc = (y-c) + x; 
% plot(x,yc,'k.',xx,xx,'r--'); 

T2 = T; 
x = T2.CA1; c1 = p1*x.^3 + p2*x.^2 + p3*x + p4;
x = T2.CA2; c2 = p1*x.^3 + p2*x.^2 + p3*x + p4;

T2.BA1 = T2.BA1-c1+T2.CA1;  
T2.BA2 = T2.BA2-c2+T2.CA2; 

y1 = T2.BA1; 
y2 = T2.BA2; 
x1 = T2.CA1; 
x2 = T2.CA2; 

figure(3); 
plot(x1,y1,'.',x2,y2,'.'); 

% systematic error now? largely removed! 
d1 = T2.BA1; 
d2 = T2.BA2; 

median(d1)
median(d2)

figure(4); 
boxplot([T2.BA1 T2.BA2]); 


