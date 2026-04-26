clear all; clc; format compact; 

%% look at features vs age
load age_features_mghsleep % Xtr Xte
Ytr = ytr'; 

%% put in order
[~,jj] = sort(ytr); 
ytr = ytr(jj); 
Xtr = Xtr(jj,:); 
Ytr = ytr'; 

%% add squares
xt = [];
for i = 1:size(Xtr,2); 
    xt(:,i) = Xtr(:,i).^2; 
end
Xtr = [Xtr xt]; 

%% normalize 
m = median(Xtr)
v = iqr(Xtr)
for i = 1:size(Xtr,2); 
    Xtr(:,i) = (Xtr(:,i)-m(i))/v(i); 
end

%% univariate correlations
for i = 1:size(Xtr,2); 
   [RHO,PVAL] = corr(Xtr(:,i),Ytr,'type','Spearman'); 
   p(i) = PVAL; 
   r(i) = RHO;
end

[ii,jj] = sort(p,'ascend'); 
Xtr = Xtr(:,jj(1:150)); 
% Ytr = Ytr(jj(1:100)); 

%% look at ones with p < 0.05
 for i = 1:size(Xtr,2);  
     
     figure(1); clf; 
     subplot(211); 
     scatter(Xtr(:,i),Ytr,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
     xlabel('Feature value'); ylabel('CA'); 
     drawnow; 
     
     % find transform to straighten trend
     [f, gof] = createFit1(Xtr(:,i), Ytr);
     xi = f(Xtr(:,i));
     subplot(212); 
     scatter(xi,Ytr,'MarkerFaceColor','k','MarkerEdgeColor','r','MarkerFaceAlpha',.05,'MarkerEdgeAlpha',.01); 
     xlabel('Transformed feature value'); ylabel('CA');
     xx = 20:80; 
     hold on; plot(xx,xx,'r--'); 
     drawnow
     
     XXtr(:,i) = xi; 
     
%      g = input('ok'); 
end

X = [XXtr Ytr];
%% try linear regression
b = glmfit(XXtr,Ytr,'normal','link','identity');
yhat = glmval(b,XXtr,'identity'); 
% 
figure(1); clf; 
scatter(Ytr,yhat-Ytr); 
corr(Ytr,yhat) % 0.4623 -- not very good; keep only those with low p-val: evern worse 0.1401

%% try GPR
tbl = array2table([Xtr Ytr]);

gprMdl = fitrgp(tbl,'NoShellRings','KernelFunction','ardsquaredexponential',...
       'FitMethod','sr','PredictMethod','fic','Standardize',1)

%%
% gprMdl = fitrgp(tbl,'Var41','KernelFunction','ardsquaredexponential',...
%         'FitMethod','sr','PredictMethod','fic','Standardize',1)
%gprMdl = fitrgp(Xtr,Ytr,'Basis','linear','FitMethod','exact','PredictMethod','exact');

%%
% ypred = resubPredict(gprMdl);
% scatter(Ytr,ypred-Ytr)
