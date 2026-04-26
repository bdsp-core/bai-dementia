clear all; clc; format compact; 

%% look at difference in BA for SHHS subjects
load SHHSBACA % gets T: %subject_id, CA1, CA2, BA1, BA2, BA_std1, BA_std2

%% 
boxplot([(T.BA1-mean(T.BA1)) (T.BA2-mean(T.BA1))]); 
boxplot([(T.BA1-mean(T.CA1)) (T.BA2-mean(T.CA1))]); 

d1 = T.BA1-T.CA1; 
d2 = T.BA2-T.CA1; 

% systematic error

%% 
median(d1)
median(d2)

%  -5.0893, -4.2252

%% try correcting systmatic bias
x = [T.CA1; T.CA2];
y = [T.BA1; T.BA2];
figure(2); clf; 
plot(x,y,'.');
xx = 30:90; hold on; plot(xx,xx,'r'); 
axis([30 90 30 90]); 
axis square; 

%% fit polynomial to data -- to remove bias
[fitresult, gof] = createFit(x,y-x);

figure(2); hold on
h = plot( fitresult, x, y);
p1 = -0.0002742; 
p2 =      0.0491; 
p3 =      -2.238; 
p4 =       72.58; 

c = p1*x.^3 + p2*x.^2 + p3*x + p4;

%% 
figure(3); clf; 
yc = y-c+x;
plot(x,yc,'k.',xx,xx,'r--'); 

d1 = T.BA1-T.CA1; 
d2 = T.BA2-T.CA1; 



